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

2. **Show the top N** to the user, ask which to tackle. Wait for approval.

3. **For each chosen finding**:

   a. Read the session log referenced in the finding — grab the exact query
      and the user-visible symptom.

   b. Explore the relevant code path (`engine.py`, `smart_search.py`,
      `app.py`, `scraper/data_gov.py`) to find where the symptom originates.

   c. Propose a minimal fix. Show the diff; on approval, apply it.

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
