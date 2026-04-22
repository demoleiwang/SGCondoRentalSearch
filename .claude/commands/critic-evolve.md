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
