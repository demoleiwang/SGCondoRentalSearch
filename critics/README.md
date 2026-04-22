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
