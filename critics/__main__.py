"""CLI for the critics system.

Usage:
    python -m critics run --persona P001 --queries-file /tmp/queries.json
    python -m critics list-personas
    python -m critics next-persona
    python -m critics touch-persona --persona P001 --lesson "..."
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
    """Update persona after a successful session."""
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
