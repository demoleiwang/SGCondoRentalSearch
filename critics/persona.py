"""Persona schema, loader, and saver."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

REQUIRED_FRONTMATTER = [
    "id",
    "name",
    "status",
    "created",
    "last_run",
    "runs",
    "archetype_axes",
]

REQUIRED_SECTIONS = ["Context", "Search Style", "Success Criteria", "Quit Triggers"]
ALLOWED_STATUS = {"draft", "active", "refined", "retired"}


@dataclass
class Persona:
    id: str
    name: str
    status: str
    created: date
    last_run: Optional[date]
    runs: int
    archetype_axes: dict
    context: str
    search_style: str
    success_criteria: str
    quit_triggers: str
    lessons: list[str] = field(default_factory=list)
    source_path: Optional[Path] = None


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("persona file must start with YAML frontmatter (---)")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("unterminated frontmatter")
    fm_text = text[4:end]
    body = text[end + 5:]
    data = yaml.safe_load(fm_text) or {}
    return data, body


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: Optional[str] = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _parse_lessons(text: str) -> list[str]:
    lessons: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not stripped.startswith("- _"):
            lessons.append(stripped[2:].strip())
    return lessons


def load_persona(path: Path) -> Persona:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)

    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            raise ValueError(f"{path.name}: missing required frontmatter: {key}")

    if fm["status"] not in ALLOWED_STATUS:
        raise ValueError(f"{path.name}: invalid status: {fm['status']}")

    sections = _parse_sections(body)
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            raise ValueError(f"{path.name}: missing required section: ## {section}")

    created = fm["created"]
    if isinstance(created, str):
        created = date.fromisoformat(created)
    last_run = fm["last_run"]
    if isinstance(last_run, str):
        last_run = date.fromisoformat(last_run)

    return Persona(
        id=fm["id"],
        name=fm["name"],
        status=fm["status"],
        created=created,
        last_run=last_run,
        runs=int(fm["runs"]),
        archetype_axes=dict(fm["archetype_axes"]),
        context=sections["Context"],
        search_style=sections["Search Style"],
        success_criteria=sections["Success Criteria"],
        quit_triggers=sections["Quit Triggers"],
        lessons=_parse_lessons(sections.get("Lessons", "")),
        source_path=path,
    )


def list_active_personas(personas_dir: Path) -> list[Persona]:
    personas_dir = Path(personas_dir)
    results: list[Persona] = []
    for path in sorted(personas_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        p = load_persona(path)
        if p.status == "active":
            results.append(p)
    return results


def save_persona(p: Persona, path: Path) -> None:
    path = Path(path)
    fm = {
        "id": p.id,
        "name": p.name,
        "status": p.status,
        "created": p.created.isoformat(),
        "last_run": p.last_run.isoformat() if p.last_run else None,
        "runs": p.runs,
        "archetype_axes": p.archetype_axes,
    }
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()

    lessons_block = "\n".join(f"- {l}" for l in p.lessons) if p.lessons else "_(none yet)_"

    body = (
        f"## Context\n\n{p.context}\n\n"
        f"## Search Style\n\n{p.search_style}\n\n"
        f"## Success Criteria\n\n{p.success_criteria}\n\n"
        f"## Quit Triggers\n\n{p.quit_triggers}\n\n"
        f"## Lessons\n\n{lessons_block}\n"
    )

    path.write_text(f"---\n{fm_text}\n---\n\n{body}", encoding="utf-8")
