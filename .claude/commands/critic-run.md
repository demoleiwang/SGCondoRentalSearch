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
