# Critic-Driven Evolution Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-evolving synthetic-user critique loop to SGCondoRentalSearch so a daily Claude Code session can simulate an "ordinary user", produce actionable findings, and drive product improvements.

**Architecture:** Fully additive top-level `critics/` module (persona markdown library, session runner in Python, findings/meta markdown files) + three slash commands (`/critic-run`, `/critic-act`, `/critic-evolve`) that orchestrate persona → queries → pipeline → critique → findings → persona-update using the existing `engine`, `smart_search`, `scraper.data_gov` APIs. LLM reasoning lives in slash-command prompts; Python code is deterministic and testable.

**Tech Stack:** Python 3.10+, pandas (existing), PyYAML (new dep for frontmatter), pytest (existing), no new runtime deps for the main path. Optional `take_screenshots.py` path uses existing Playwright dep.

**Spec:** `docs/superpowers/specs/2026-04-22-critic-evolution-loop-design.md`

---

## File Structure

**New files:**

```
critics/
├── __init__.py                      # Package marker + version
├── README.md                        # System docs (for humans and Claude)
├── personas/
│   ├── _template.md                 # Canonical persona schema
│   └── P001-marcus-downtown.md      # First persona
├── sessions/                        # (starts empty)
├── findings/
│   ├── backlog.md                   # (starts with just headers)
│   └── done.md                      # (starts with just headers)
├── meta.md                          # Coverage matrix + evolution log
├── persona.py                       # Persona schema, loader, validator
├── session.py                       # SessionBundle dataclasses + log writer
├── findings.py                      # Backlog append/move utilities
├── run_session.py                   # Orchestrator: persona → queries → pipeline → SessionBundle
├── __main__.py                      # CLI: `python -m critics <subcommand>`
└── prompts/
    ├── generate-queries.md          # Prompt: given persona → queries
    ├── critique.md                  # Prompt: given results → critique + findings
    └── evolve.md                    # Prompt: given sessions → persona actions

.claude/commands/
├── critic-run.md                    # Daily run slash command
├── critic-act.md                    # Implement findings slash command
└── critic-evolve.md                 # Weekly maintenance slash command

tests/critics/
├── __init__.py
├── conftest.py                      # Skip unless CRITICS=1
├── fixtures/
│   └── P999-fixture.md              # Fixture persona for tests
├── test_persona.py                  # Persona schema & loader tests
├── test_session.py                  # Session log schema tests
├── test_findings.py                 # Backlog/done utilities tests
└── test_run_session.py              # End-to-end run_session test
```

**Modified files:**

- `requirements.txt` — add `PyYAML>=6.0` for frontmatter parsing.
- `.gitignore` — no changes expected (sessions go into git as the evolution log).

**Responsibilities:**

- `critics/persona.py` — one responsibility: parse a persona markdown file into a `Persona` dataclass, validate schema, save back with updates.
- `critics/session.py` — one responsibility: `SessionBundle` dataclass + markdown serialization (read + write the session log format).
- `critics/findings.py` — one responsibility: append to `backlog.md`, move items to `done.md`, parse the backlog for listing.
- `critics/run_session.py` — orchestrator: takes `(persona_id, queries)` → returns `SessionBundle`. Calls `engine`, `smart_search`. No LLM calls. No file I/O except what `session.py` handles.
- `critics/__main__.py` — CLI-only wrapper: parses args, calls library functions, writes output. Never imports app/Streamlit code.
- Slash command markdown files — Claude-executed orchestration glue. They call `python -m critics ...` and read/write the markdown files directly via CC tools.

---

## Task 1: Bootstrap directory skeleton and test gating

**Files:**
- Create: `critics/__init__.py`
- Create: `critics/README.md`
- Create: `critics/personas/_template.md`
- Create: `critics/sessions/.gitkeep`
- Create: `critics/findings/backlog.md`
- Create: `critics/findings/done.md`
- Create: `critics/meta.md`
- Create: `tests/critics/__init__.py`
- Create: `tests/critics/conftest.py`
- Modify: `requirements.txt` (add PyYAML)

- [ ] **Step 1: Create package init**

Create `critics/__init__.py`:

```python
"""Critic-driven evolution loop for SGCondoRentalSearch.

See critics/README.md for usage.
"""

__version__ = "0.1.0"
```

- [ ] **Step 2: Create tests package with skip gate**

Create `tests/critics/__init__.py`:

```python
```

Create `tests/critics/conftest.py`:

```python
import os
import pytest

if os.environ.get("CRITICS") != "1":
    pytest.skip(
        "critics tests require CRITICS=1 env var",
        allow_module_level=True,
    )
```

- [ ] **Step 3: Verify the skip gate works**

Run (without CRITICS=1):

```bash
python -m pytest tests/critics/ -q
```

Expected: `no tests ran` (conftest triggers module-level skip before collection picks anything up). If you see a collection error instead, it means an empty test file exists — fine, just proceed.

Run with CRITICS=1:

```bash
CRITICS=1 python -m pytest tests/critics/ -q
```

Expected: `no tests ran` (no test files yet).

- [ ] **Step 4: Add empty placeholders for markdown artifacts**

Create `critics/sessions/.gitkeep` (empty file).

Create `critics/findings/backlog.md`:

```markdown
# Findings Backlog

Open findings from critic sessions. Sorted by priority then FIFO.
New findings are appended below. Resolved findings move to `done.md`.

## P0 — Blocks core user goal

## P1 — Friction, workaround exists

## P2 — Nice-to-have
```

Create `critics/findings/done.md`:

```markdown
# Resolved Findings

Completed findings with their resolving commit sha.

## Completed
```

Create `critics/meta.md`:

```markdown
# Critics Meta — Coverage and Evolution

## Coverage Matrix

Axes: language × budget × household × work_zone × data_literacy × mobility.
Updated by `/critic-evolve`.

_Empty. First update after P001 runs._

## Evolution Log

Append-only record of persona actions (add / refine / retire / rename).

- 2026-04-22: System bootstrapped. P001 (Marcus — Downtown Banker) added as first active persona.
```

- [ ] **Step 5: Write persona template**

Create `critics/personas/_template.md`:

```markdown
---
id: Pxxx
name: Placeholder Name — One-line archetype
status: draft
created: YYYY-MM-DD
last_run: null
runs: 0
archetype_axes:
  language: en-only
  budget: mid
  household: single
  work_zone: central
  data_literacy: casual
  mobility: mrt-primary
---

## Context

- Job / role:
- Salary (SGD):
- Years in SG:
- Target unit:
- Commute tolerance:
- Lifestyle priorities:

## Search Style

- Language mix:
- Specificity progression:
- Verification habits:

## Success Criteria

1.
2.
3.

## Quit Triggers

-

## Lessons

_(Appended per run. Format: `- YYYY-MM-DD: one-sentence takeaway`.)_
```

- [ ] **Step 6: Write critics README**

Create `critics/README.md`:

```markdown
# Critics — Self-Evolving Synthetic-User Critique Loop

An in-repo system where Claude Code simulates "ordinary users" trying this
app, produces a critique from their perspective, and feeds findings back
into product improvements. Runs once per day.

## Daily usage

```bash
# In Claude Code:
/critic-run            # simulate next persona, log critique, add findings
/critic-act 3          # implement top 3 findings from backlog
/critic-evolve         # weekly: review coverage, propose persona changes
```

## Layout

- `personas/` — one markdown file per persona, `Pxxx-slug.md`. Files starting
  with `_` (e.g. `_template.md`) are ignored. `_archive/` holds retired ones.
- `sessions/` — one log per run, `YYYY-MM-DD-Pxxx.md`.
- `findings/backlog.md` — open items, P0/P1/P2.
- `findings/done.md` — resolved items with commit sha.
- `meta.md` — coverage matrix + evolution log.

## Design

See `docs/superpowers/specs/2026-04-22-critic-evolution-loop-design.md`.
```

- [ ] **Step 7: Add PyYAML dep and commit**

Modify `requirements.txt`, appending:

```
PyYAML>=6.0
```

Install:

```bash
pip install PyYAML>=6.0
```

Commit:

```bash
git add critics/ tests/critics/ requirements.txt
git commit -m "feat(critics): bootstrap directory skeleton and test gate"
```

---

## Task 2: Persona loader and validator

**Files:**
- Create: `critics/persona.py`
- Create: `tests/critics/fixtures/P999-fixture.md`
- Create: `tests/critics/test_persona.py`

- [ ] **Step 1: Write the fixture persona**

Create `tests/critics/fixtures/P999-fixture.md`:

```markdown
---
id: P999
name: Test Fixture Persona
status: active
created: 2026-01-01
last_run: 2026-01-10
runs: 2
archetype_axes:
  language: en-only
  budget: mid
  household: single
  work_zone: central
  data_literacy: casual
  mobility: mrt-primary
---

## Context

- Fixture persona for tests.

## Search Style

- Plain English queries.

## Success Criteria

1. Loader returns a Persona with all fields populated.

## Quit Triggers

- Missing required fields.

## Lessons

- 2026-01-05: First lesson.
- 2026-01-10: Second lesson.
```

- [ ] **Step 2: Write the failing tests**

Create `tests/critics/test_persona.py`:

```python
from datetime import date
from pathlib import Path

import pytest

from critics.persona import Persona, load_persona, list_active_personas, save_persona

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_persona_parses_frontmatter_and_body():
    p = load_persona(FIXTURE_DIR / "P999-fixture.md")
    assert p.id == "P999"
    assert p.name == "Test Fixture Persona"
    assert p.status == "active"
    assert p.created == date(2026, 1, 1)
    assert p.last_run == date(2026, 1, 10)
    assert p.runs == 2
    assert p.archetype_axes["language"] == "en-only"
    assert "Fixture persona for tests." in p.context
    assert "Plain English queries." in p.search_style
    assert p.lessons == [
        "2026-01-05: First lesson.",
        "2026-01-10: Second lesson.",
    ]


def test_load_persona_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_persona(tmp_path / "missing.md")


def test_load_persona_missing_required_field(tmp_path):
    p = tmp_path / "P800-broken.md"
    p.write_text(
        "---\nid: P800\nstatus: active\n---\n\n## Context\n- foo\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required frontmatter: name"):
        load_persona(p)


def test_list_active_personas_skips_underscore_and_archive(tmp_path):
    (tmp_path / "_template.md").write_text("ignored", encoding="utf-8")
    (tmp_path / "_archive").mkdir()
    (tmp_path / "_archive" / "P000-old.md").write_text("ignored", encoding="utf-8")

    import shutil
    shutil.copy(FIXTURE_DIR / "P999-fixture.md", tmp_path / "P999-fixture.md")

    result = list_active_personas(tmp_path)
    assert [p.id for p in result] == ["P999"]


def test_save_persona_roundtrip(tmp_path):
    src = FIXTURE_DIR / "P999-fixture.md"
    dst = tmp_path / "P999-fixture.md"
    dst.write_bytes(src.read_bytes())
    p = load_persona(dst)
    p.runs += 1
    p.last_run = date(2026, 2, 1)
    p.lessons.append("2026-02-01: Third lesson.")
    save_persona(p, dst)

    reloaded = load_persona(dst)
    assert reloaded.runs == 3
    assert reloaded.last_run == date(2026, 2, 1)
    assert reloaded.lessons[-1] == "2026-02-01: Third lesson."
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run:

```bash
CRITICS=1 python -m pytest tests/critics/test_persona.py -v
```

Expected: collection error (`ModuleNotFoundError: critics.persona`).

- [ ] **Step 4: Implement persona.py**

Create `critics/persona.py`:

```python
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
    body = text[end + 5 :]
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
```

- [ ] **Step 5: Run tests, confirm pass**

```bash
CRITICS=1 python -m pytest tests/critics/test_persona.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add critics/persona.py tests/critics/test_persona.py tests/critics/fixtures/
git commit -m "feat(critics): persona schema, loader, saver"
```

---

## Task 3: SessionBundle dataclasses and markdown writer

**Files:**
- Create: `critics/session.py`
- Create: `tests/critics/test_session.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/critics/test_session.py`:

```python
from datetime import datetime
from pathlib import Path

import pytest

from critics.session import (
    QueryResult,
    SessionBundle,
    load_session_log,
    write_session_log,
)


def _sample_bundle(persona_id="P999") -> SessionBundle:
    return SessionBundle(
        persona_id=persona_id,
        timestamp="2026-04-22T10:30:00",
        data_cache_mtime=1713783600.0,
        query_results=[
            QueryResult(
                query_text="2b2b near OUE Downtown 4500",
                parsed_criteria={"bedrooms": 2, "bathrooms": 2, "price_max": 4500},
                smart_search_output={
                    "landmark_name": "oue downtown",
                    "strategies_count": 8,
                    "results_count": 23,
                },
                raw_results=[
                    {"project_name": "Icon", "est_rent": 4300, "district": 2},
                ],
                ranking_notes={"count": 23, "median": 4200},
            ),
        ],
        screenshots=[],
    )


def test_write_and_load_session_log_roundtrip(tmp_path):
    bundle = _sample_bundle()
    path = tmp_path / "2026-04-22-P999.md"
    write_session_log(bundle, path)
    assert path.exists()

    loaded = load_session_log(path)
    assert loaded.persona_id == "P999"
    assert loaded.timestamp == "2026-04-22T10:30:00"
    assert len(loaded.query_results) == 1
    assert loaded.query_results[0].query_text == "2b2b near OUE Downtown 4500"
    assert loaded.query_results[0].parsed_criteria["bedrooms"] == 2
    assert loaded.query_results[0].smart_search_output["strategies_count"] == 8
    assert loaded.query_results[0].raw_results[0]["project_name"] == "Icon"


def test_write_session_log_contains_required_sections(tmp_path):
    path = tmp_path / "2026-04-22-P999.md"
    write_session_log(_sample_bundle(), path)
    text = path.read_text(encoding="utf-8")
    assert "# Session 2026-04-22 — P999" in text
    assert "## Queries" in text
    assert "## Results" in text
    assert "## Critique" in text  # placeholder section, filled by slash command
    assert "## Findings" in text


def test_load_session_log_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_session_log(tmp_path / "missing.md")
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
CRITICS=1 python -m pytest tests/critics/test_session.py -v
```

Expected: collection error (`ModuleNotFoundError: critics.session`).

- [ ] **Step 3: Implement session.py**

Create `critics/session.py`:

```python
"""Session bundle dataclasses and markdown log writer/reader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class QueryResult:
    query_text: str
    parsed_criteria: dict
    smart_search_output: Optional[dict]
    raw_results: list[dict]
    ranking_notes: dict


@dataclass
class SessionBundle:
    persona_id: str
    timestamp: str
    data_cache_mtime: float
    query_results: list[QueryResult]
    screenshots: list[Path] = field(default_factory=list)


_JSON_FENCE = "```json"
_FENCE_END = "```"


def _fmt_json_block(obj: Any) -> str:
    return f"{_JSON_FENCE}\n{json.dumps(obj, indent=2, ensure_ascii=False, default=str)}\n{_FENCE_END}"


def write_session_log(bundle: SessionBundle, path: Path) -> None:
    path = Path(path)
    date_part = bundle.timestamp.split("T", 1)[0]

    lines: list[str] = []
    lines.append(f"# Session {date_part} — {bundle.persona_id}\n")
    lines.append(f"- Timestamp: `{bundle.timestamp}`")
    lines.append(f"- Persona: `{bundle.persona_id}`")
    lines.append(f"- Data cache mtime: `{bundle.data_cache_mtime}`")
    lines.append(f"- Screenshots: {len(bundle.screenshots)}")
    lines.append("")
    lines.append("## Queries\n")
    for i, qr in enumerate(bundle.query_results, 1):
        lines.append(f"{i}. `{qr.query_text}`")
    lines.append("")
    lines.append("## Results\n")
    for i, qr in enumerate(bundle.query_results, 1):
        lines.append(f"### Query {i}: `{qr.query_text}`\n")
        lines.append("**Parsed criteria:**")
        lines.append(_fmt_json_block(qr.parsed_criteria))
        lines.append("")
        lines.append("**Smart search summary:**")
        lines.append(_fmt_json_block(qr.smart_search_output))
        lines.append("")
        lines.append("**Ranking notes:**")
        lines.append(_fmt_json_block(qr.ranking_notes))
        lines.append("")
        lines.append("**Top raw results:**")
        lines.append(_fmt_json_block(qr.raw_results))
        lines.append("")
    lines.append("## Critique\n")
    lines.append("_(Filled by `/critic-run` after the Python bundle is produced.)_\n")
    lines.append("## Findings\n")
    lines.append("_(Filled by `/critic-run`. Each finding ID mirrors `findings/backlog.md`.)_\n")

    path.write_text("\n".join(lines), encoding="utf-8")


def _extract_json_blocks(text: str) -> list[Any]:
    blocks: list[Any] = []
    i = 0
    while True:
        start = text.find(_JSON_FENCE, i)
        if start == -1:
            break
        content_start = start + len(_JSON_FENCE)
        if text[content_start] == "\n":
            content_start += 1
        end = text.find(_FENCE_END, content_start)
        if end == -1:
            break
        body = text[content_start:end].strip()
        blocks.append(json.loads(body) if body else None)
        i = end + len(_FENCE_END)
    return blocks


def load_session_log(path: Path) -> SessionBundle:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")

    persona_id = ""
    timestamp = ""
    data_cache_mtime = 0.0
    for line in text.splitlines():
        if line.startswith("- Persona: "):
            persona_id = line.split("`")[1]
        elif line.startswith("- Timestamp: "):
            timestamp = line.split("`")[1]
        elif line.startswith("- Data cache mtime: "):
            data_cache_mtime = float(line.split("`")[1])

    results_section = text.split("## Results", 1)[1].split("## Critique", 1)[0]
    per_query_chunks = [
        chunk for chunk in results_section.split("### Query ")[1:]
    ]
    query_results: list[QueryResult] = []
    for chunk in per_query_chunks:
        header_line = chunk.splitlines()[0]
        query_text = header_line.split("`", 2)[1]
        blocks = _extract_json_blocks(chunk)
        parsed_criteria = blocks[0] if len(blocks) > 0 else {}
        smart_output = blocks[1] if len(blocks) > 1 else None
        ranking_notes = blocks[2] if len(blocks) > 2 else {}
        raw_results = blocks[3] if len(blocks) > 3 else []
        query_results.append(
            QueryResult(
                query_text=query_text,
                parsed_criteria=parsed_criteria or {},
                smart_search_output=smart_output,
                raw_results=raw_results or [],
                ranking_notes=ranking_notes or {},
            )
        )

    return SessionBundle(
        persona_id=persona_id,
        timestamp=timestamp,
        data_cache_mtime=data_cache_mtime,
        query_results=query_results,
        screenshots=[],
    )
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
CRITICS=1 python -m pytest tests/critics/test_session.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add critics/session.py tests/critics/test_session.py
git commit -m "feat(critics): session bundle dataclasses and markdown log I/O"
```

---

## Task 4: Findings backlog utilities

**Files:**
- Create: `critics/findings.py`
- Create: `tests/critics/test_findings.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/critics/test_findings.py`:

```python
from pathlib import Path

from critics.findings import (
    Finding,
    append_finding,
    list_backlog,
    move_to_done,
    next_finding_id,
)


def _bootstrap(tmp_path: Path) -> Path:
    backlog = tmp_path / "backlog.md"
    backlog.write_text(
        "# Findings Backlog\n\n"
        "## P0 — Blocks core user goal\n\n"
        "## P1 — Friction, workaround exists\n\n"
        "## P2 — Nice-to-have\n",
        encoding="utf-8",
    )
    done = tmp_path / "done.md"
    done.write_text(
        "# Resolved Findings\n\n## Completed\n",
        encoding="utf-8",
    )
    return backlog


def test_next_finding_id_empty(tmp_path):
    backlog = _bootstrap(tmp_path)
    assert next_finding_id(backlog) == "F001"


def test_append_finding_writes_under_priority(tmp_path):
    backlog = _bootstrap(tmp_path)
    f = Finding(
        id="F001",
        date="2026-04-22",
        persona_id="P001",
        priority="P0",
        symptom="Commute time missing",
        repro="Any 2b2b query near OUE Downtown",
        session_ref="sessions/2026-04-22-P001.md",
    )
    append_finding(f, backlog)

    text = backlog.read_text(encoding="utf-8")
    assert "F001" in text
    p0_section = text.split("## P0")[1].split("## P1")[0]
    assert "F001" in p0_section
    assert "Commute time missing" in p0_section


def test_next_finding_id_increments(tmp_path):
    backlog = _bootstrap(tmp_path)
    for n, prio in enumerate(["P0", "P1", "P2"], 1):
        append_finding(
            Finding(
                id=f"F00{n}",
                date="2026-04-22",
                persona_id="P001",
                priority=prio,
                symptom=f"thing {n}",
                repro="repro",
                session_ref="x",
            ),
            backlog,
        )
    assert next_finding_id(backlog) == "F004"


def test_list_backlog_preserves_priority_order(tmp_path):
    backlog = _bootstrap(tmp_path)
    append_finding(
        Finding("F001", "2026-04-22", "P001", "P2", "s1", "r1", "x"),
        backlog,
    )
    append_finding(
        Finding("F002", "2026-04-22", "P001", "P0", "s2", "r2", "x"),
        backlog,
    )
    append_finding(
        Finding("F003", "2026-04-22", "P001", "P1", "s3", "r3", "x"),
        backlog,
    )
    items = list_backlog(backlog)
    priorities = [f.priority for f in items]
    assert priorities == ["P0", "P1", "P2"]


def test_move_to_done_transfers_item(tmp_path):
    backlog = _bootstrap(tmp_path)
    done = tmp_path / "done.md"
    append_finding(
        Finding("F001", "2026-04-22", "P001", "P0", "s1", "r1", "x"),
        backlog,
    )
    move_to_done("F001", backlog, done, commit_sha="abc123")

    assert "F001" not in backlog.read_text(encoding="utf-8")
    done_text = done.read_text(encoding="utf-8")
    assert "F001" in done_text
    assert "abc123" in done_text
```

- [ ] **Step 2: Run tests, confirm fail**

```bash
CRITICS=1 python -m pytest tests/critics/test_findings.py -v
```

Expected: collection error (`ModuleNotFoundError: critics.findings`).

- [ ] **Step 3: Implement findings.py**

Create `critics/findings.py`:

```python
"""Findings backlog utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PRIORITY_ORDER = ["P0", "P1", "P2"]
_SECTION_HEADERS = {
    "P0": "## P0 — Blocks core user goal",
    "P1": "## P1 — Friction, workaround exists",
    "P2": "## P2 — Nice-to-have",
}


@dataclass
class Finding:
    id: str
    date: str
    persona_id: str
    priority: str
    symptom: str
    repro: str
    session_ref: str


def _format_finding_line(f: Finding) -> str:
    return (
        f"- [ ] `{f.id}` ({f.date}, {f.persona_id}) "
        f"{f.symptom}. Repro: {f.repro}. Source: {f.session_ref}"
    )


_ID_RE = re.compile(r"`(F\d{3,})`")


def next_finding_id(backlog_path: Path) -> str:
    text = Path(backlog_path).read_text(encoding="utf-8")
    ids = _ID_RE.findall(text)
    if not ids:
        return "F001"
    n = max(int(x[1:]) for x in ids)
    return f"F{n + 1:03d}"


def append_finding(f: Finding, backlog_path: Path) -> None:
    if f.priority not in PRIORITY_ORDER:
        raise ValueError(f"invalid priority: {f.priority}")
    path = Path(backlog_path)
    text = path.read_text(encoding="utf-8")
    header = _SECTION_HEADERS[f.priority]
    if header not in text:
        raise ValueError(f"backlog missing section header: {header}")

    next_idx = len(PRIORITY_ORDER) - PRIORITY_ORDER.index(f.priority) - 1
    later_headers = [
        _SECTION_HEADERS[p]
        for p in PRIORITY_ORDER[PRIORITY_ORDER.index(f.priority) + 1 :]
    ]
    insert_before = None
    for lh in later_headers:
        idx = text.find(lh)
        if idx != -1:
            insert_before = idx
            break

    line = _format_finding_line(f) + "\n"
    section_start = text.find(header)
    body_start = section_start + len(header) + 1  # skip header + \n
    if insert_before is not None:
        body_end = insert_before
    else:
        body_end = len(text)

    section_body = text[body_start:body_end]
    # trim trailing blank lines, append new line, pad one blank line
    trimmed = section_body.rstrip("\n")
    if trimmed:
        new_body = trimmed + "\n" + line + "\n"
    else:
        new_body = "\n" + line + "\n"

    new_text = text[:body_start] + new_body + text[body_end:]
    path.write_text(new_text, encoding="utf-8")


_LINE_RE = re.compile(
    r"- \[ \] `(F\d+)` \((\d{4}-\d{2}-\d{2}), (P\d+)\) (.*?)\. Repro: (.*?)\. Source: (\S+)"
)


def list_backlog(backlog_path: Path) -> list[Finding]:
    text = Path(backlog_path).read_text(encoding="utf-8")
    results: list[Finding] = []
    current_prio = None
    for line in text.splitlines():
        for p, hdr in _SECTION_HEADERS.items():
            if line.startswith(hdr):
                current_prio = p
                break
        m = _LINE_RE.match(line)
        if m and current_prio:
            fid, date, persona_id, symptom, repro, source = m.groups()
            results.append(
                Finding(
                    id=fid,
                    date=date,
                    persona_id=persona_id,
                    priority=current_prio,
                    symptom=symptom,
                    repro=repro,
                    session_ref=source,
                )
            )
    results.sort(key=lambda f: (PRIORITY_ORDER.index(f.priority), f.id))
    return results


def move_to_done(
    finding_id: str,
    backlog_path: Path,
    done_path: Path,
    commit_sha: str,
) -> None:
    backlog = Path(backlog_path)
    done = Path(done_path)
    text = backlog.read_text(encoding="utf-8")

    lines = text.splitlines(keepends=True)
    new_lines = []
    target_line = None
    for line in lines:
        if f"`{finding_id}`" in line and line.startswith("- [ ] "):
            target_line = line
            continue
        new_lines.append(line)
    if target_line is None:
        raise KeyError(f"finding {finding_id} not in backlog")
    backlog.write_text("".join(new_lines), encoding="utf-8")

    done_line = target_line.replace("- [ ] ", "- [x] ").rstrip("\n")
    done_line += f" — commit `{commit_sha}`\n"
    done_text = done.read_text(encoding="utf-8")
    done.write_text(done_text.rstrip("\n") + "\n" + done_line, encoding="utf-8")
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
CRITICS=1 python -m pytest tests/critics/test_findings.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add critics/findings.py tests/critics/test_findings.py
git commit -m "feat(critics): findings backlog + done utilities"
```

---

## Task 5: Session runner (orchestrator)

**Files:**
- Create: `critics/run_session.py`
- Create: `tests/critics/test_run_session.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/critics/test_run_session.py`:

```python
from pathlib import Path

from critics.run_session import run_session
from critics.session import SessionBundle


def test_run_session_returns_bundle_with_expected_shape():
    queries = ["Queenstown 1b1b 3300", "OUE Downtown 2b2b 4500"]
    bundle = run_session(persona_id="P001", queries=queries)
    assert isinstance(bundle, SessionBundle)
    assert bundle.persona_id == "P001"
    assert len(bundle.query_results) == 2
    assert bundle.query_results[0].query_text == queries[0]
    assert "bedrooms" in bundle.query_results[0].parsed_criteria


def test_run_session_landmark_query_has_smart_output():
    bundle = run_session(persona_id="P001", queries=["OUE Downtown 2b2b 4500"])
    qr = bundle.query_results[0]
    assert qr.smart_search_output is not None
    assert "strategies_count" in qr.smart_search_output
    assert "results_count" in qr.smart_search_output


def test_run_session_non_landmark_query_has_no_smart_output():
    bundle = run_session(persona_id="P001", queries=["Queenstown 1b1b 3300"])
    qr = bundle.query_results[0]
    # Queenstown alone = MRT, not a landmark; expand_query returns None.
    # Runner records None and keeps going.
    assert qr.smart_search_output is None or isinstance(qr.smart_search_output, dict)


def test_run_session_ranking_notes_present():
    bundle = run_session(persona_id="P001", queries=["Queenstown 1b1b 3300"])
    qr = bundle.query_results[0]
    assert "count" in qr.ranking_notes
    assert "price_range" in qr.ranking_notes
```

- [ ] **Step 2: Run tests, confirm fail**

```bash
CRITICS=1 python -m pytest tests/critics/test_run_session.py -v
```

Expected: collection error.

- [ ] **Step 3: Implement run_session.py**

Create `critics/run_session.py`:

```python
"""Session orchestrator: persona + queries -> SessionBundle.

No LLM calls. All LLM work happens in slash-command prompts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from critics.session import QueryResult, SessionBundle
from engine import parse_query
from smart_search import expand_query


DATA_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def _cache_mtime() -> float:
    if not DATA_CACHE_DIR.exists():
        return 0.0
    latest = 0.0
    for p in DATA_CACHE_DIR.glob("*"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue
    return latest


def _summarize_smart_search(result) -> dict | None:
    if result is None:
        return None
    return {
        "landmark_name": result.landmark_name,
        "landmark_address": result.landmark_address,
        "strategies_count": len(result.strategies),
        "results_count": len(result.results),
        "strategies": [
            {
                "station": s.station,
                "distance_m": s.distance_m,
                "reason": s.reason,
            }
            for s in result.strategies[:10]
        ],
    }


def _top_raw_results(result, limit: int = 20) -> list[dict]:
    if result is None:
        return []
    rows = []
    for r in result.results[:limit]:
        rows.append({
            "project_name": r.project_name,
            "district": r.district,
            "area_desc": r.area_desc,
            "est_rent": r.est_rent,
            "median_psf": r.median_psf,
            "contracts": r.contracts,
            "strategy": r.strategy_name,
            "url_propertyguru": r.url_propertyguru,
        })
    return rows


def _ranking_notes(result, criteria: dict) -> dict:
    if result is None or not result.results:
        return {"count": 0, "price_range": None, "median": None}
    prices = [r.est_rent for r in result.results]
    return {
        "count": len(prices),
        "price_range": [min(prices), max(prices)],
        "median": sorted(prices)[len(prices) // 2],
        "criteria_budget_max": criteria.get("price_max"),
        "in_budget_count": sum(
            1 for p in prices
            if criteria.get("price_max") is None or p <= criteria["price_max"]
        ),
    }


def run_session(
    persona_id: str,
    queries: list[str],
    with_screenshots: bool = False,
) -> SessionBundle:
    """Execute queries through the search pipeline for a given persona.

    This function is pure orchestration — no LLM calls, no markdown I/O.
    """
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(
        timespec="seconds"
    )
    bundle_results: list[QueryResult] = []

    for q in queries:
        criteria = parse_query(q)
        smart = None
        try:
            smart = expand_query(q)
        except Exception:
            smart = None

        qr = QueryResult(
            query_text=q,
            parsed_criteria=dict(criteria),
            smart_search_output=_summarize_smart_search(smart),
            raw_results=_top_raw_results(smart),
            ranking_notes=_ranking_notes(smart, criteria),
        )
        bundle_results.append(qr)

    screenshots: list[Path] = []
    if with_screenshots:
        try:
            from take_screenshots import take_all  # type: ignore[attr-defined]
            screenshots = list(take_all())
        except Exception:
            screenshots = []

    return SessionBundle(
        persona_id=persona_id,
        timestamp=timestamp,
        data_cache_mtime=_cache_mtime(),
        query_results=bundle_results,
        screenshots=screenshots,
    )
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
CRITICS=1 python -m pytest tests/critics/test_run_session.py -v
```

Expected: 4 tests PASS. (Tests exercise real `engine` and `smart_search`; they need the data cache to be warm. If data.gov fetch is blocked, `smart_search.expand_query` still returns an object with empty `results` — the test asserts only structural shape, not result counts.)

If `test_run_session_landmark_query_has_smart_output` fails because data fetch errored and `expand_query` returned None, that's an environmental issue — adjust the test query to `"SMU附近 2b2b 4500"` which has more reliable cached data, or pre-warm the cache with `python -c "from scraper.data_gov import fetch_rental_data; fetch_rental_data()"` and re-run.

- [ ] **Step 5: Commit**

```bash
git add critics/run_session.py tests/critics/test_run_session.py
git commit -m "feat(critics): session runner orchestrator"
```

---

## Task 6: CLI entry point

**Files:**
- Create: `critics/__main__.py`

- [ ] **Step 1: Implement CLI**

Create `critics/__main__.py`:

```python
"""CLI for the critics system.

Usage:
    python -m critics run --persona P001 --queries-file /tmp/queries.json
    python -m critics list-personas
    python -m critics next-persona
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from critics.persona import list_active_personas, load_persona, save_persona
from critics.run_session import run_session
from critics.session import write_session_log


REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "critics" / "personas"
SESSIONS_DIR = REPO_ROOT / "critics" / "sessions"


def cmd_run(args: argparse.Namespace) -> int:
    queries = json.loads(Path(args.queries_file).read_text(encoding="utf-8"))
    if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
        print("queries-file must be a JSON array of strings", file=sys.stderr)
        return 2

    bundle = run_session(
        persona_id=args.persona,
        queries=queries,
        with_screenshots=args.with_screenshots,
    )

    date_part = bundle.timestamp.split("T", 1)[0]
    log_path = SESSIONS_DIR / f"{date_part}-{args.persona}.md"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    write_session_log(bundle, log_path)
    print(json.dumps({"session_log": str(log_path), "query_count": len(queries)}))
    return 0


def cmd_list_personas(args: argparse.Namespace) -> int:
    personas = list_active_personas(PERSONAS_DIR)
    out = [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "last_run": p.last_run.isoformat() if p.last_run else None,
            "runs": p.runs,
        }
        for p in personas
    ]
    print(json.dumps(out, indent=2))
    return 0


def cmd_next_persona(args: argparse.Namespace) -> int:
    personas = list_active_personas(PERSONAS_DIR)
    if not personas:
        print("", end="")
        return 1
    # Sort by (last_run is None first, then oldest last_run, then lowest ID)
    personas.sort(
        key=lambda p: (
            p.last_run is not None,
            p.last_run or date.min,
            p.id,
        )
    )
    print(personas[0].id)
    return 0


def cmd_touch_persona(args: argparse.Namespace) -> int:
    """Update persona after a successful session: bump runs, set last_run, append lesson."""
    matches = list(PERSONAS_DIR.glob(f"{args.persona}-*.md"))
    if not matches:
        print(f"persona file for {args.persona} not found", file=sys.stderr)
        return 2
    p = load_persona(matches[0])
    p.runs += 1
    p.last_run = date.today()
    if args.lesson:
        p.lessons.append(f"{date.today().isoformat()}: {args.lesson}")
    save_persona(p, matches[0])
    print(json.dumps({"persona": p.id, "runs": p.runs, "last_run": p.last_run.isoformat()}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="critics")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run a session for a persona")
    run_p.add_argument("--persona", required=True)
    run_p.add_argument("--queries-file", required=True)
    run_p.add_argument("--with-screenshots", action="store_true")
    run_p.set_defaults(func=cmd_run)

    sub.add_parser("list-personas", help="list active personas").set_defaults(
        func=cmd_list_personas
    )
    sub.add_parser("next-persona", help="print ID of next persona to run").set_defaults(
        func=cmd_next_persona
    )

    touch_p = sub.add_parser("touch-persona", help="update persona after a run")
    touch_p.add_argument("--persona", required=True)
    touch_p.add_argument("--lesson", default="")
    touch_p.set_defaults(func=cmd_touch_persona)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Smoke test the CLI**

```bash
python -m critics list-personas
```

Expected: `[]` (no personas yet; P001 is added in Task 8). Exit 0.

```bash
python -m critics next-persona
```

Expected: empty output, exit 1 (no active personas yet).

- [ ] **Step 3: Commit**

```bash
git add critics/__main__.py
git commit -m "feat(critics): CLI entry point (python -m critics ...)"
```

---

## Task 7: Slash-command prompts (non-Python content)

**Files:**
- Create: `critics/prompts/generate-queries.md`
- Create: `critics/prompts/critique.md`
- Create: `critics/prompts/evolve.md`

- [ ] **Step 1: Write the query-generation prompt**

Create `critics/prompts/generate-queries.md`:

```markdown
# Prompt: Generate Queries for a Persona

You will be given a persona markdown file. Your job: produce 3–5 natural-language
search queries the persona would plausibly type into SGCondoRentalSearch.

## Constraints

- Match the persona's language mix (`archetype_axes.language`).
- Span specificity: start vague ("2 bedroom near downtown"), end precise
  ("OUE Downtown One 2b2b 4000-4500 high floor").
- Do NOT invent numbers not implied by the persona. If budget is "no financial
  pressure at 210k salary", reasonable rent cap is ~$4,500, not $8,000.
- Include at least one query the parser is likely to mishandle — the persona
  doesn't know the grammar; users speak naturally. Example cue: "with gym nearby",
  "not too far from my office".
- Avoid duplicating query shapes across personas; look at recent sessions if
  available.

## Output format

A JSON array of strings. Nothing else. Example:

```json
[
  "2 bedroom near downtown 4500",
  "OUE Downtown 2b2b 4000-4500",
  "Tanjong Pagar 2房 4500以内 朝南",
  "quiet 2b2b near CBD with supermarket nearby",
  "Downtown MRT 2 bedroom high floor 4200"
]
```
```

- [ ] **Step 2: Write the critique prompt**

Create `critics/prompts/critique.md`:

```markdown
# Prompt: Critique a Session from the Persona's POV

You will be given:
1. The persona markdown file.
2. The session bundle (queries, parsed criteria, smart-search summary, raw
   results, ranking notes).
3. Optionally: screenshots.

Your job: write a critique **as that persona would feel it**, not as an
engineer. Then emit findings.

## Score six axes (1–5, integer)

| Axis | What 5 looks like |
|---|---|
| Relevance | Top results match what this persona wants (budget, beds, area). |
| Info Density | Each row has enough to decide "viewing worth it?" without clicking out. |
| Commute Readability | Door-to-door time visible for the persona's workplace. |
| Price Transparency | Persona can tell if the estimate is a realistic ask vs. aspirational. |
| Lifestyle Signal | Evidence of amenities the persona cares about (gym, cafes, supermarket). |
| External Hop Necessity | Persona does NOT have to open PropertyGuru/Google to judge. |

One sentence of reasoning per axis.

## Emit findings

For each axis scored < 4, produce one finding:

- **Priority** P0 if the persona would abandon the tool; P1 if they'd complain
  but keep going; P2 if it's polish.
- **Symptom** — how the persona experiences it (not a code diagnosis).
- **Repro** — a specific query from this session that triggers it.

## Output format

```json
{
  "scores": {
    "relevance": 4,
    "info_density": 2,
    "commute_readability": 2,
    "price_transparency": 3,
    "lifestyle_signal": 1,
    "external_hop_necessity": 2
  },
  "reasons": {
    "relevance": "Five of top 10 are 2B2B in budget; one is 3BR noise.",
    "info_density": "Rows show project name, rent, psf — no floor, no facing.",
    "commute_readability": "MRT name visible but not minutes to OUE Downtown.",
    "price_transparency": "Median shown; P25/P75 hidden behind a chart tab.",
    "lifestyle_signal": "No signal at all for amenities near the project.",
    "external_hop_necessity": "Every promising row requires opening PropertyGuru."
  },
  "findings": [
    {
      "priority": "P1",
      "symptom": "Commute time isn't shown next to each result — I have to cross-check Google Maps for every one.",
      "repro": "OUE Downtown 2b2b 4500"
    }
  ],
  "next_run_lesson": "Users with a fixed workplace need door-to-door minutes in the result row, not just MRT name."
}
```
```

- [ ] **Step 3: Write the evolve prompt**

Create `critics/prompts/evolve.md`:

```markdown
# Prompt: Evolve the Persona Library

You will be given all persona files, recent sessions, and the current
`meta.md` coverage matrix. Propose actions.

## Actions

Exactly one of:

1. **Retire** an active persona whose last 3 sessions added no new findings.
2. **Refine** a persona whose findings are recurring but unfixed (make their
   queries harder / more specific).
3. **Add** a new persona to fill a coverage gap. A gap = a cell in the axis
   matrix with < 2 runs so far.
4. **No change** — justify why.

## Coverage matrix

Axes: `language × budget × household × work_zone × data_literacy × mobility`.
Don't try to fill the full Cartesian product — aim for ~6–10 personas long-term
covering meaningfully different user segments.

## Output format

```json
{
  "action": "add",
  "reason": "No active persona with work_zone=east or family household.",
  "proposed_persona": {
    "id": "P004",
    "name": "Nur — Changi Family Teacher",
    "archetype_axes": { "language": "en-only", "budget": "mid-tight", ... },
    "context_seed": "Teacher at CBP school, married with two teens, wants 4-room HDB...",
    "status": "draft"
  },
  "evolution_log_entry": "2026-05-03: Added P004 (Nur — Changi Family Teacher) to cover east work zone + family household."
}
```

Proposals with `action: "add"` should come out as `status: draft` so the user
approves before a real session uses them.
```

- [ ] **Step 4: Commit**

```bash
git add critics/prompts/
git commit -m "feat(critics): LLM prompts for generate/critique/evolve"
```

---

## Task 8: First persona — P001 Marcus

**Files:**
- Create: `critics/personas/P001-marcus-downtown.md`

- [ ] **Step 1: Write P001**

Create `critics/personas/P001-marcus-downtown.md`:

```markdown
---
id: P001
name: Marcus Chen — Downtown Banker
status: active
created: 2026-04-22
last_run: null
runs: 0
archetype_axes:
  language: en-primary-zh-secondary
  budget: mid-flexible
  household: single
  work_zone: CBD
  data_literacy: casual
  mobility: mrt-primary
---

## Context

- Job: mid-career analyst at a bank at OUE Downtown One (Tanjong Pagar area).
- Salary: SGD ~210k/year → take-home ~$13k/month.
- Years in SG: 4; lease-renewal season.
- Target unit: 2B2B condo.
- Budget comfort: "no financial stress" ≈ ≤30% of take-home = $4,000–$4,500/month; will flex to $5k if exceptional.
- Commute tolerance: ≤35 min door-to-door, at most 1 MRT transfer.
- Lifestyle priorities: gym / cafes / supermarket within 10-min walk; weekend cycling access is a plus.
- Household: single, occasional house guests.

## Search Style

- English-primary; occasionally drops in Chinese ("朝南", "高楼层", "附近").
- Starts vague ("2 bedroom near downtown"), tightens after seeing first results.
- Suspicious of prices that look unusually low; will compare against past rentals via PropertyGuru.
- Cross-checks commute on Google Maps before shortlisting.
- Low patience for pagination and for columns he can't interpret.

## Success Criteria

1. Sees ≥5 realistic 2B2B options in his budget, with enough info to triage without opening external tabs.
2. Door-to-door commute time to OUE Downtown visible per row, not just an MRT name.
3. Some signal of lifestyle amenity density near each project (cafes, gym, groceries).
4. Rent estimate includes a "realistic ask" marker (e.g. P25) not just median.

## Quit Triggers

- Results unsorted or overwhelming with no way to narrow by commute.
- Same project repeated across areas with no deduplication.
- Must click out to PropertyGuru for every result before being able to judge.
- Prices so wide a range (e.g. $2k–$8k for 2B2B) that the tool's value is unclear.

## Lessons

_(none yet)_
```

- [ ] **Step 2: Validate with the loader**

```bash
CRITICS=1 python -c "from critics.persona import load_persona; p = load_persona('critics/personas/P001-marcus-downtown.md'); print(p.id, p.name, p.archetype_axes['work_zone'])"
```

Expected: `P001 Marcus Chen — Downtown Banker CBD`

- [ ] **Step 3: Check CLI sees it**

```bash
python -m critics list-personas
python -m critics next-persona
```

Expected:
- `list-personas` shows P001 with `"last_run": null`, `"runs": 0`.
- `next-persona` prints `P001`.

- [ ] **Step 4: Commit**

```bash
git add critics/personas/P001-marcus-downtown.md
git commit -m "feat(critics): add P001 Marcus — Downtown Banker"
```

---

## Task 9: `/critic-run` slash command

**Files:**
- Create: `.claude/commands/critic-run.md`

- [ ] **Step 1: Write the slash command**

Create `.claude/commands/critic-run.md`:

````markdown
---
description: Run one persona session — simulate a user, log critique, add findings.
---

# /critic-run

Simulate a synthetic persona using SGCondoRentalSearch, produce a critique
from their POV, and append findings to the backlog.

Optional arg: `$ARGUMENTS` — a persona ID (e.g. `P001`). If blank, pick the
active persona with the oldest `last_run`.

## Procedure

1. **Pick the persona.** If `$ARGUMENTS` is non-empty, use it. Else:

   ```bash
   python -m critics next-persona
   ```

   Capture the ID. If empty output, stop with: "No active personas. Add one
   under `critics/personas/`."

2. **Read the persona file.** It lives at `critics/personas/<ID>-*.md`.

3. **Generate queries.** Following `critics/prompts/generate-queries.md`,
   produce 3–5 queries tailored to this persona. Emit JSON only. Save to a
   temp file:

   ```bash
   cat > /tmp/critics-queries.json <<'EOF'
   [ "<query1>", "<query2>", ... ]
   EOF
   ```

4. **Run the session:**

   ```bash
   python -m critics run --persona <ID> --queries-file /tmp/critics-queries.json
   ```

   Output is JSON with `session_log` path. Note this path.

5. **Read the session log** (it contains Queries + Results JSON blocks, but
   empty Critique/Findings sections).

6. **Critique.** Following `critics/prompts/critique.md`, produce the critique
   JSON (scores, reasons, findings, next_run_lesson). Use the Read tool on
   the persona file and the session log; if screenshots were requested, Read
   those too.

7. **Write the critique back into the session log.** Replace the placeholder
   text under `## Critique` with:

   ```markdown
   ### Scores

   | Axis | Score | Reason |
   |---|---|---|
   | Relevance | <N> | <reason> |
   | Info Density | <N> | <reason> |
   | Commute Readability | <N> | <reason> |
   | Price Transparency | <N> | <reason> |
   | Lifestyle Signal | <N> | <reason> |
   | External Hop Necessity | <N> | <reason> |

   ### Lesson

   <next_run_lesson>
   ```

   Replace the placeholder under `## Findings` with a bulleted list where
   each bullet is `(<priority>) <symptom> — repro: \`<query>\``.

8. **Append findings to backlog.** For each finding, run:

   ```bash
   python -c "
   from critics.findings import Finding, append_finding, next_finding_id
   from pathlib import Path
   backlog = Path('critics/findings/backlog.md')
   fid = next_finding_id(backlog)
   append_finding(Finding(
     id=fid, date='$(date -u +%Y-%m-%d)', persona_id='<ID>',
     priority='<P0|P1|P2>', symptom='<symptom>', repro='<query>',
     session_ref='<session_log path>',
   ), backlog)
   print(fid)
   "
   ```

9. **Update the persona:**

   ```bash
   python -m critics touch-persona --persona <ID> --lesson '<next_run_lesson>'
   ```

10. **Summarize to the user**: scorecard table, top finding, session log path,
    persona state (runs count). Do NOT commit — let the user decide when.

## Tips

- If `expand_query` returns no landmark for a query, the session log will
  show `null` under smart_search — that is data, not an error. The persona
  might still critique it.
- If the data cache needs refresh, you'll see an empty `raw_results`; critique
  should note this as a session caveat, not invent findings.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/critic-run.md
git commit -m "feat(critics): /critic-run slash command"
```

---

## Task 10: `/critic-act` slash command

**Files:**
- Create: `.claude/commands/critic-act.md`

- [ ] **Step 1: Write the slash command**

Create `.claude/commands/critic-act.md`:

````markdown
---
description: Implement top findings from the critic backlog. Usage: /critic-act [N]
---

# /critic-act

Work through the top N findings from `critics/findings/backlog.md`. Each one
becomes a small code change with a commit. Default N = 3.

`$ARGUMENTS` — optional integer. If non-numeric or blank, use 3.

## Procedure

1. **List the backlog:**

   ```bash
   python -c "
   from critics.findings import list_backlog
   from pathlib import Path
   for f in list_backlog(Path('critics/findings/backlog.md'))[:10]:
       print(f.priority, f.id, '—', f.symptom)
   "
   ```

2. **Show the top N** to the user, ask which to tackle (user may pick a
   subset, reorder, or skip). Wait for approval.

3. **For each chosen finding**:

   a. Read the session log referenced in the finding — grab the exact query
      and the user-visible symptom.

   b. Explore the relevant code path (`engine.py`, `smart_search.py`,
      `app.py`, `scraper/data_gov.py`) to find where the symptom originates.

   c. Propose a minimal fix. Show the diff to the user; on approval, apply
      it.

   d. Run tests:

      ```bash
      python -m pytest tests/ -q
      ```

      If red: fix and re-run. Do not proceed until green. Do not set `CRITICS=1`
      here — critics tests are not gating product fixes.

   e. Commit with a message referencing the finding ID:

      ```bash
      git commit -am "fix: <short description> (addresses critics/<FID>)"
      ```

      Capture the commit sha.

   f. Move the finding to done:

      ```bash
      python -c "
      from critics.findings import move_to_done
      from pathlib import Path
      move_to_done('<FID>', Path('critics/findings/backlog.md'),
                   Path('critics/findings/done.md'), commit_sha='<sha>')
      "
      ```

   g. Commit the backlog/done update:

      ```bash
      git add critics/findings/
      git commit -m "chore(critics): mark <FID> done"
      ```

4. **Summarize**: how many findings shipped, remaining backlog by priority.

## When to stop early

- If a finding requires architectural changes beyond a small fix, stop,
  re-file it with priority P0 and a `needs-design` note in the symptom,
  and tell the user.
- If a finding seems incorrect on second read (persona misjudged), move it
  to done with a `wontfix` note instead of implementing.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/critic-act.md
git commit -m "feat(critics): /critic-act slash command"
```

---

## Task 11: `/critic-evolve` slash command

**Files:**
- Create: `.claude/commands/critic-evolve.md`

- [ ] **Step 1: Write the slash command**

Create `.claude/commands/critic-evolve.md`:

````markdown
---
description: Weekly persona maintenance — retire, refine, or add personas.
---

# /critic-evolve

Run weekly-ish. Updates the coverage matrix in `critics/meta.md` and proposes
one concrete persona action.

## Procedure

1. **Gather input:**
   - Read all files under `critics/personas/` (excluding `_archive/` and
     `_template.md`).
   - Read the last 10 session logs under `critics/sessions/`.
   - Read `critics/meta.md`.
   - Read `critics/findings/backlog.md` (to spot recurring unfixed issues).

2. **Refresh coverage matrix.** Rewrite the `## Coverage Matrix` section of
   `meta.md` as a table where each row is an axis and the cells show which
   personas populate which values and how many total runs they have.

3. **Propose an action.** Following `critics/prompts/evolve.md`, produce JSON
   describing exactly one action: retire, refine, add, or no-change.

4. **Present to the user.** Show the proposal; wait for approval.

5. **On approval:**
   - **retire**: set `status: retired` in the persona file and move it to
     `critics/personas/_archive/`.
   - **refine**: edit the persona's `## Search Style` (or other relevant
     sections) to make their queries harder / more specific. Keep `status: active`.
   - **add**: create a new persona file with `status: draft`. Tell the user
     to review and flip to `active` before `/critic-run` will pick it.
   - **no-change**: log the rationale and exit.

6. **Append an evolution log entry** to `critics/meta.md`:

   ```
   - YYYY-MM-DD: <action> <persona-id> — <one-line reason>.
   ```

7. **Commit:**

   ```bash
   git add critics/personas/ critics/meta.md
   git commit -m "chore(critics): evolve — <action> <persona-id>"
   ```
````

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/critic-evolve.md
git commit -m "feat(critics): /critic-evolve slash command"
```

---

## Task 12: End-to-end dry run and README polish

**Files:**
- Modify: `critics/README.md`
- No new files.

- [ ] **Step 1: Pre-warm the data cache**

```bash
python -c "from scraper.data_gov import fetch_rental_data; fetch_rental_data(); print('cache ready')"
```

Expected: prints `cache ready`.

- [ ] **Step 2: Dry-run the runner with hand-made queries**

```bash
cat > /tmp/critics-queries.json <<'EOF'
["2b2b near OUE Downtown 4500", "Tanjong Pagar 2 bedroom 4000-5000", "OUE Downtown One 2房 4500以内"]
EOF
python -m critics run --persona P001 --queries-file /tmp/critics-queries.json
```

Expected: JSON with `session_log` path like `critics/sessions/2026-04-22-P001.md`. Open it and confirm:

- Frontmatter-style metadata lines present.
- Three `### Query N:` sections, each with four JSON code blocks (parsed_criteria, smart_search_output, ranking_notes, raw_results).
- `## Critique` and `## Findings` still show placeholders.

- [ ] **Step 3: Confirm persona state was NOT touched**

The CLI `run` subcommand does not update the persona — that's `/critic-run`'s job after critique. Verify:

```bash
python -c "from critics.persona import load_persona; p = load_persona('critics/personas/P001-marcus-downtown.md'); print(p.runs, p.last_run)"
```

Expected: `0 None`.

- [ ] **Step 4: Clean up the test session**

```bash
rm critics/sessions/2026-04-22-P001.md
```

(The first real session log comes from `/critic-run`, which includes critique. We don't commit half-baked logs.)

- [ ] **Step 5: Final pass on `critics/README.md`**

Replace with the polished version:

```markdown
# Critics — Self-Evolving Synthetic-User Critique Loop

An in-repo system where Claude Code simulates "ordinary users" trying this app,
produces a critique from their perspective, and feeds findings back into product
improvements. Runs once per day.

## Daily usage (in Claude Code)

- `/critic-run [P001]` — simulate next persona (or specified one), log critique,
  add findings to the backlog, update the persona.
- `/critic-act [N]` — implement top N findings from the backlog (default 3).
- `/critic-evolve` — weekly: review coverage, propose one persona action
  (retire / refine / add).

## Layout

| Path | Role |
|---|---|
| `personas/Pxxx-slug.md` | One persona per file. Files starting with `_` are ignored. |
| `personas/_archive/` | Retired personas. |
| `sessions/YYYY-MM-DD-Pxxx.md` | One log per run. |
| `findings/backlog.md` | Open findings, P0/P1/P2. |
| `findings/done.md` | Resolved findings with commit sha. |
| `meta.md` | Coverage matrix + append-only evolution log. |
| `prompts/*.md` | LLM prompts the slash commands load. |
| `persona.py`, `session.py`, `findings.py`, `run_session.py` | Python library. |
| `__main__.py` | CLI: `python -m critics ...`. |

## Test gating

`tests/critics/` is skipped by default. Run with:

```bash
CRITICS=1 python -m pytest tests/critics/ -v
```

## Design

See `docs/superpowers/specs/2026-04-22-critic-evolution-loop-design.md`.
```

- [ ] **Step 6: Run both test suites**

```bash
python -m pytest tests/ -q
CRITICS=1 python -m pytest tests/critics/ -q
```

Expected: both green. Main suite (~142 tests) unchanged. Critics suite shows 17 passing (5 persona + 3 session + 5 findings + 4 run_session).

- [ ] **Step 7: Commit**

```bash
git add critics/README.md
git commit -m "docs(critics): README polish after end-to-end dry run"
```

---

## Task 13: First live `/critic-run` and verification

This task is executed **manually by the user** in a fresh Claude Code session, not by an implementing agent. The implementer stops after Task 12.

- [ ] **Step 1 (user action):** Open Claude Code in the repo, run `/critic-run`.
- [ ] **Step 2 (user action):** Review the generated session log at `critics/sessions/YYYY-MM-DD-P001.md`. Verify:
  - Queries look like something Marcus would plausibly type.
  - Scores feel honest (not uniformly 5 nor uniformly 1).
  - Findings reference actual symptoms in the result data.
- [ ] **Step 3 (user action):** Commit the session log and updated persona if it all looks right.

---

## Self-Review

### Spec coverage

| Spec section | Covered by |
|---|---|
| `critics/` directory layout | Task 1 |
| Persona schema + frontmatter | Task 1 (template), Task 2 (loader) |
| Session runner API (`run_session`, `SessionBundle`, `QueryResult`) | Task 3, Task 5 |
| Session log markdown format | Task 3 |
| Findings backlog & done | Task 1 (files), Task 4 (utilities) |
| `/critic-run` slash command | Task 9 |
| `/critic-act` slash command | Task 10 |
| `/critic-evolve` slash command | Task 11 |
| Prompts (generate/critique/evolve) | Task 7 |
| First persona P001 Marcus | Task 8 |
| Coverage matrix in `meta.md` | Task 1 (skeleton), Task 11 (refresh logic) |
| Test gating via `CRITICS=1` | Task 1 (conftest) |
| PyYAML dep | Task 1 |
| Screenshot opt-in flag | Task 5 (`with_screenshots` arg), Task 6 (CLI flag) |

No gaps.

### Placeholder scan

No "TBD", "implement later", or similar. Every code step includes concrete code. Every command includes concrete invocation.

### Type consistency

- `Persona` fields (Task 2) used in `__main__.py` (Task 6): `id`, `name`, `status`, `last_run`, `runs`, `lessons`, `source_path` — all defined.
- `SessionBundle` / `QueryResult` fields (Task 3) used in `run_session.py` (Task 5) and `__main__.py` (Task 6): matching.
- `Finding` fields (Task 4) used in `/critic-run` and `/critic-act` slash commands (Tasks 9, 10): `id`, `date`, `persona_id`, `priority`, `symptom`, `repro`, `session_ref` — all match the dataclass.
- CLI subcommand names (`run`, `list-personas`, `next-persona`, `touch-persona`) used in Tasks 6, 8, 9 — consistent.
- Finding ID format `Fxxx` used consistently across Tasks 4, 9, 10.
