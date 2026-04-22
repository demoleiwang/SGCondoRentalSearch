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
    "archetype_axes": { "language": "en-only", "budget": "mid-tight", "...": "..." },
    "context_seed": "Teacher at CBP school, married with two teens, wants 4-room HDB...",
    "status": "draft"
  },
  "evolution_log_entry": "2026-05-03: Added P004 (Nur — Changi Family Teacher) to cover east work zone + family household."
}
```

Proposals with `action: "add"` should come out as `status: draft` so the user
approves before a real session uses them.
