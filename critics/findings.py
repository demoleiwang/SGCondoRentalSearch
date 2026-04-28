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

    later_headers = [
        _SECTION_HEADERS[p]
        for p in PRIORITY_ORDER[PRIORITY_ORDER.index(f.priority) + 1:]
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
    trimmed = section_body.rstrip("\n")
    if trimmed:
        new_body = trimmed + "\n" + line + "\n"
    else:
        new_body = "\n" + line + "\n"

    new_text = text[:body_start] + new_body + text[body_end:]
    path.write_text(new_text, encoding="utf-8")


_LINE_RE = re.compile(
    r"- \[ \] `(F\d+)` \((\d{4}-\d{2}-\d{2}), ([\w-]+)\) (.*?)\. Repro: (.*?)\. Source: (\S+)"
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
