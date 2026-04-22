# Critic-Driven Evolution Loop — Design Spec

Date: 2026-04-22
Status: Design approved by user, pending spec review

## Purpose

Build an in-repo system where Claude Code simulates "ordinary users" trying SGCondoRentalSearch, produces a critique from that user's perspective, and feeds findings back into product improvements. The system is self-evolving: personas are maintained, refined, retired, and added over time so coverage broadens and insights stay fresh.

The user invokes this once per day. Each run either (a) executes a new persona session or (b) implements previously-logged findings. The system should leverage Claude Code's native strengths (file I/O, code reading, running Python, git) rather than reinvent a separate orchestration layer.

## Goals

1. Daily, low-friction: one slash command per day is enough to keep the loop alive.
2. Each session produces durable artifacts (session log, findings) that Claude can re-read in future sessions.
3. Findings are actionable — each one can become a concrete code change.
4. Personas self-evolve: coverage gaps trigger new personas; stale personas retire; repeated unresolved findings refine a persona's pickiness.
5. First concrete persona: a banker working at OUE Downtown One, ~SGD 210k salary, wants a 2B2B condo, no financial stress, reasonable commute, good lifestyle amenities.

## Non-Goals

- No CI-based daily trigger (user runs Claude Code manually).
- No web dashboard (markdown is the UI; Claude Code reads it natively).
- No LLM-graded rubric autotuning (fixed six-axis scoring).
- No browser automation in v1 (screenshots are opt-in via flag).
- No multi-user / team concurrency model — single-user single-machine.

## Architecture

```
SGCondoRentalSearch/
├── critics/                        # NEW top-level module
│   ├── README.md                   # How the system works (for humans and for Claude)
│   ├── personas/
│   │   ├── _template.md            # Canonical persona schema
│   │   ├── P001-marcus-downtown.md # First persona (active)
│   │   └── _archive/               # Retired personas kept for coverage history
│   ├── sessions/
│   │   └── YYYY-MM-DD-Pxxx.md      # One per run; includes queries, results, critique, findings
│   ├── findings/
│   │   ├── backlog.md              # Open items (P0/P1/P2)
│   │   └── done.md                 # Resolved items with commit sha
│   ├── meta.md                     # Coverage matrix + evolution log
│   ├── run_session.py              # Python orchestrator: persona -> queries -> pipeline -> results
│   └── prompts/
│       ├── generate-queries.md     # Given a persona, produce 3-5 queries they'd type
│       ├── critique.md             # Given (persona, queries, results), produce critique + findings
│       └── evolve.md               # Given all sessions, decide persona retire/refine/add
├── .claude/commands/
│   ├── critic-run.md               # NEW: run a persona session
│   ├── critic-act.md               # NEW: implement findings from backlog
│   └── critic-evolve.md            # NEW: weekly persona maintenance pass
└── tests/critics/
    ├── test_persona_schema.py      # Persona frontmatter parses, required fields present
    ├── test_session_log_schema.py  # Session log schema stable
    └── test_run_session.py         # run_session.py end-to-end with a fixture persona
```

Top-level `critics/` sits next to `scraper/` — existing project style is flat.

## Components

### 1. Persona Library (`critics/personas/`)

A persona is a single markdown file with YAML frontmatter. One file per persona, named `Pxxx-short-slug.md`.

**Schema:**

```yaml
---
id: P001                             # Stable ID, auto-incremented
name: Marcus Chen — Downtown Banker  # Human-readable
status: active                       # draft | active | refined | retired
created: 2026-04-22                  # ISO date
last_run: null                       # ISO date or null
runs: 0                              # Count of completed sessions
archetype_axes:
  language: en-primary-zh-secondary  # en-only | zh-only | en-primary-zh-secondary | mixed
  budget: mid-flexible               # tight | mid-tight | mid | mid-flexible | flexible
  household: single                  # single | couple | family-young | family-teens
  work_zone: CBD                     # CBD | one-north | east | west | north | central
  data_literacy: casual              # casual | power-user | analyst
  mobility: mrt-primary              # mrt-primary | car | bike | walk-primary
---
```

Body sections (required):

- `## Context` — life facts: job, salary, household, time in SG, target unit.
- `## Search Style` — language mix, specificity progression, habits (e.g., cross-checks on Google Maps).
- `## Success Criteria` — numbered list of what would make them recommend the tool.
- `## Quit Triggers` — what would make them give up.
- `## Lessons (appended per run)` — one bullet per session with key takeaway.

Persona files are the primary evolution surface — edits happen here, not in code.

### 2. Session Runner (`critics/run_session.py`)

Pure Python script (no LLM calls). Takes a persona ID and a list of queries, runs them through the existing pipeline, returns a structured result bundle. The LLM work (generating queries, writing critique) happens in the slash command prompts; the runner is deterministic and testable.

**Public API:**

```python
def run_session(persona_id: str, queries: list[str],
                with_screenshots: bool = False) -> SessionBundle:
    """Execute queries against the pipeline for a given persona."""

@dataclass
class SessionBundle:
    persona_id: str
    timestamp: str                    # ISO datetime
    data_cache_mtime: float           # For replay-awareness
    query_results: list[QueryResult]
    screenshots: list[Path]           # Empty unless with_screenshots=True

@dataclass
class QueryResult:
    query_text: str
    parsed_criteria: dict             # From engine.parse_query
    smart_search_output: dict | None  # From smart_search.expand_query (None if no landmark)
    raw_results: list[dict]           # Top 20 results, JSON-safe
    ranking_notes: dict               # Counts, price range, median, distribution
```

Stores session bundle as markdown at `critics/sessions/YYYY-MM-DD-Pxxx.md` using a stable schema (so future sessions can grep prior ones).

**Error handling:**

- Streamlit not needed for the data path; if `with_screenshots=True`, start it headless first.
- Data cache refresh failure: log and continue with whatever is on disk.
- `expand_query` returning None: recorded as a result with `smart_search_output=None`, not an error.

### 3. Slash Commands

All three under `.claude/commands/`.

**`/critic-run [persona-id]`** — The daily driver.

Flow in the prompt:
1. If `persona-id` given, use it. Else: pick persona from `critics/personas/*.md` (excluding `_template.md` and anything under `_archive/`) with `status: active` and oldest `last_run` (ties: lowest ID, null `last_run` sorts earliest).
2. Read persona file. Load `prompts/generate-queries.md` and produce 3–5 queries in that persona's voice, spanning specificity (vague → precise) and possibly mixing languages.
3. Invoke `python -m critics.run_session --persona Pxxx --queries-file /tmp/queries.json` (queries written to a tmp file to survive quoting).
4. Read returned session bundle. Load `prompts/critique.md` and produce:
   - Six-axis scorecard (1–5 each): **Relevance / Info Density / Commute Readability / Price Transparency / Lifestyle Signal / External Hop Necessity**.
   - One sentence of reasoning per axis.
   - For each axis < 4: one finding (P0/P1/P2), phrased as user-observable symptom + minimal repro.
5. Append critique section to `critics/sessions/YYYY-MM-DD-Pxxx.md`.
6. Append new findings to `critics/findings/backlog.md` (each with session ref).
7. Update persona: `last_run`, `runs++`, one-bullet lesson in `## Lessons`.
8. Print summary to user (scores, top finding).

**`/critic-act [N]`** — Implement N top findings (default 3).

Flow:
1. Read `findings/backlog.md`, sort by P0→P1→P2 then FIFO.
2. Show user the top N and ask which to tackle.
3. For each chosen: read code context, propose a fix, implement, run `pytest tests/ -q` (excluding `tests/critics/`), commit.
4. Move completed findings to `findings/done.md` with commit sha.

**`/critic-evolve`** — Weekly-ish persona maintenance pass.

Flow:
1. Read `meta.md`, all personas, recent sessions.
2. Refresh coverage matrix in `meta.md`.
3. Propose actions:
   - Retire: active persona with 3+ consecutive runs producing no new findings.
   - Refine: persona whose findings keep getting filed but not fixed → add a harder query style to their Search Style section.
   - Add: any row in the coverage matrix with < 2 runs.
4. Present proposals to user; on approval, apply edits to persona files and append to evolution log in `meta.md`.

### 4. Findings Format (`critics/findings/backlog.md`)

New findings are appended; when resolved they are moved to `done.md` (not deleted in place). Backlog format:

```markdown
## P0 — Blocks core user goal

- [ ] `F023` (2026-04-22, P001) Commute time missing — user sees MRT name but not door-to-door minutes; forces Google Maps cross-check. Repro: any 2b2b query near OUE Downtown. Source: sessions/2026-04-22-P001.md

## P1 — Friction, workaround exists

- [ ] `F024` ...

## P2 — Nice-to-have
```

Each finding: ID, date, persona, symptom, repro, session ref. Links to source session enable Claude to pull full context when acting.

### 5. Meta / Evolution Log (`critics/meta.md`)

Two sections:

**Coverage matrix** — a table of archetype axes × personas × run counts. Updated by `/critic-evolve`.

**Evolution log** — append-only list of events: persona added / refined / retired / renamed, with date and reason. This is the system's memory of why it looks the way it does.

## Data Flow

```
/critic-run
    │
    ▼
pick persona ──► read persona file ──► generate queries (LLM)
                                              │
                                              ▼
                               critics/run_session.py
                              (engine.parse_query,
                               smart_search.expand_query,
                               scraper.data_gov.fetch_rental_data)
                                              │
                                              ▼
                                     SessionBundle (JSON)
                                              │
                                              ▼
                    write session log ◄──── critique (LLM) ────► append findings
                          │
                          ▼
                    update persona (last_run, lesson)
```

Nothing in this loop writes to existing code paths — critics is fully additive.

## Testing

In `tests/critics/`, excluded from default `pytest tests/` run via a `tests/critics/conftest.py` that calls `pytest.skip("set CRITICS=1 to run", allow_module_level=True)` unless `CRITICS=1` env var is set (keeps main CI fast and keeps critics errors from breaking development). `/critic-act` runs `pytest tests/` without `CRITICS=1`, so critics tests are not gating for product fixes; they are gated separately.

- `test_persona_schema.py`: every file in `critics/personas/` parses, has required frontmatter keys and body sections.
- `test_session_log_schema.py`: every file in `critics/sessions/` parses into the documented sections (Queries, Results, Critique, Findings).
- `test_run_session.py`: uses a fixture persona and a stubbed data cache to verify `run_session` returns a valid `SessionBundle`.

## First Persona (P001)

`critics/personas/P001-marcus-downtown.md` — Marcus Chen, mid-career finance professional at OUE Downtown One, SGD 210k annual salary, targets 2B2B condo without financial stress, wants ≤35-min commute and 10-min-walk amenities. Full body content follows the schema above.

Initial predicted failure modes (to be validated by first run):
- Commute shown as MRT name only, not door-to-door minutes.
- No lifestyle-amenity signal (gym/cafe/supermarket density near project).
- Queries mentioning "with gym nearby" silently dropped by parser.
- Price transparency: unclear whether P25 is a realistic negotiation target for this specific project.

## Dependencies

No new runtime deps for v1. `run_session.py` uses existing `engine`, `smart_search`, `scraper.data_gov`. Screenshots path (optional) uses existing `take_screenshots.py` + its Playwright dep.

## Success Metrics

- After 2 weeks: ≥ 3 active personas, ≥ 10 completed sessions, ≥ 5 shipped findings (in `done.md`).
- Each session produces a findable, greppable artifact.
- `/critic-run` one-shot time < 3 minutes (excluding Claude reasoning).
- Zero modifications to existing user-facing code paths caused by the critic infrastructure itself.

## Open Questions Resolved

- **Interaction mode:** Hybrid (Python API + optional screenshots). Settled.
- **Directory:** `critics/`. Settled.
- **Run vs act separation:** Two commands (`/critic-run`, `/critic-act`). Settled.
- **Screenshots default:** Off; opt-in via `--with-screenshots`. Settled.

## Out of Scope for This Spec

- Measuring persona diversity quantitatively (covered qualitatively in `meta.md`).
- Adapting scoring rubric based on past sessions.
- Multi-language persona prompts (prompts are English; generated queries can be any language).
- Any integration with issue trackers outside the repo.
