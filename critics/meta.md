# Critics Meta — Coverage and Evolution

## Coverage Matrix

6 active personas as of 2026-04-24. Cells show persona IDs populating each
axis value. Blank cells are coverage gaps worth filling with future personas.

| Axis | Value | Personas |
|---|---|---|
| **language** | en-only | P003, P004 |
| | zh-only | P002, P005 |
| | en-primary-zh-secondary | P001 |
| | mixed | P006 |
| **budget** | tight | P002 |
| | mid-tight | P003, P005 |
| | mid | _(none)_ |
| | mid-flexible | P001, P006 |
| | flexible | P004 |
| **household** | single | P001, P002, P006 |
| | couple | P004, P005 |
| | family-young | P003 |
| | family-teens | _(none)_ |
| **work_zone** | CBD | P001 |
| | one-north | P006 |
| | east | P003 |
| | west | P002 |
| | north | P005 |
| | central | P004 |
| **data_literacy** | casual | P001, P002, P003 |
| | power-user | P004, P006 |
| | analyst | P005 |
| **mobility** | mrt-primary | P001, P002, P005 |
| | car | P003 |
| | bike | P006 |
| | walk-primary | P004 |

**Gaps** (axis values covered by no active persona): budget=mid, household=family-teens.

## Evolution Log

Append-only record of persona actions (add / refine / retire / rename).

- 2026-04-22: System bootstrapped. P001 (Marcus — Downtown Banker) added as first active persona.
- 2026-04-24: Added P002 (张伟 — NUS Postdoc) — zh-only / tight / west coverage. Reason: stress-test Chinese NL parsing at tight-budget constraint; academic west-side user archetype absent.
- 2026-04-24: Added P003 (The Rahmans — East-side Young Family) — en-only / mid-tight / family-young / east / car. Reason: HDB-primary family user with school-proximity needs; east side + car-mobility both uncovered.
- 2026-04-24: Added P004 (Priya — Relocating Consultant) — en-only / flexible / couple / central / power-user / walk. Reason: high-end market + power-user features (export, multi-sort, tenure filter) entirely untested by Marcus.
- 2026-04-24: Added P005 (陈阿姨 — Retired Teacher) — zh-only / mid-tight / couple / north / analyst. Reason: data-skeptic archetype who stresses data-lineage / sample-size transparency; retired North-side demographic.
- 2026-04-24: Added P006 (Dev — one-north Tech Worker) — mixed / mid-flexible / single / one-north / power-user / bike. Reason: mixed-language queries + landmark parsing ("one-north" easily misparsed as facing direction) + cycling mobility — three novel stress dimensions.
