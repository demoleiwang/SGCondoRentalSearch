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
        if content_start < len(text) and text[content_start] == "\n":
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
