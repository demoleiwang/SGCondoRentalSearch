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
