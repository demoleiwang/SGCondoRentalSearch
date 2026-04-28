# Findings Backlog

Open findings from critic sessions. Sorted by priority then FIFO.
New findings are appended below. Resolved findings move to `done.md`.

## P0 — Blocks core user goal

- [ ] `F001` (2026-04-22, P001) No lifestyle amenity signal per project — gym, cafe, supermarket within 10-min walk nowhere shown. Repro: 2b2b near OUE Downtown 4500. Source: critics/sessions/2026-04-22-P001.md
- [ ] `F002` (2026-04-22, P001) Commute time to the workplace (e.g. OUE Downtown) is missing — only walking distance to nearest MRT is shown. Repro: 2b2b near OUE Downtown 4500. Source: critics/sessions/2026-04-22-P001.md (escalated 2026-04-28 by real-user evidence: every row of the user's own tracker carries a manually-computed commute-minutes column)

## P1 — Friction, workaround exists

- [ ] `F004` (2026-04-22, P001) Smart-search radius includes 1088m-away projects without a control to tighten to walkable-only. Repro: 2b2b near OUE Downtown 4500. Source: critics/sessions/2026-04-22-P001.md
- [ ] `F006` (2026-04-22, P001) Features-showcase Smart Commute card advertises two-location search but Streamlit UI has no such input — clicking the example runs a normal query. Repro: click Smart Commute example. Source: critics/sessions/2026-04-22-P001-round2.md
- [ ] `F011` (2026-04-28, real-user) Year built and remaining lease not shown — real shoppers manually annotate sidecar spreadsheets with TOP year + lease balance for every project. Repro: any rental query. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md
- [ ] `F016` (2026-04-28, real-user) Chinese landmark synonyms (富康宁, 多美歌, 牛车水, 乌节路, 西海岸) and mall/area names (Great World, Beauty World) missing from LANDMARKS dict — 7/7 user terms miss the dict. Repro: 富康宁 1br 3000 / great world 2br. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md

## P2 — Nice-to-have

- [ ] `F005` (2026-04-22, P001) Result rows lack floor / facing / sqft / facilities / year-built — forces PropertyGuru click per candidate. Repro: OUE Downtown One 2房 4500以内. Source: critics/sessions/2026-04-22-P001.md
- [ ] `F007` (2026-04-22, P001) Condo+HDB Data card describes a data source, not a feature — feels like table-stakes reassurance in a capability grid. Repro: welcome page features grid. Source: critics/sessions/2026-04-22-P001-round2.md
- [ ] `F009` (2026-04-22, P001) No visual cue that example buttons auto-submit the search — a newcomer may think it only copies text. Repro: welcome page features grid. Source: critics/sessions/2026-04-22-P001-round2.md
- [ ] `F010` (2026-04-22, P001) P75 label lacks a tooltip explaining the percentile meaning — non-data-literate users may misread the bargaining target emoji. Repro: hover over P25 target emoji. Source: critics/sessions/2026-04-22-P001-round3.md
- [ ] `F012` (2026-04-28, real-user) Multiple sqft variants per project (e.g. 689/624, 721/591) not surfaced — single-typical-size assumption hides per-stack rent spread. Repro: Fourth Avenue Residence / The Glades / RoyalGreen. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md
- [ ] `F013` (2026-04-28, real-user) No multi-config shortlist — real shoppers track 1b1b, 2b1b, 2b2b targets per project on one row; tool shows one est_rent per bedroom count globally. Repro: multi-config shopping behavior. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md
- [ ] `F014` (2026-04-28, real-user) PropertyGuru link is project search; real shortlists track specific listing URLs once a stack/floor is picked. Repro: any project after shortlisting. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md
- [ ] `F015` (2026-04-28, real-user) No adjacency / nuisance signal — projects manually excluded for adjacent construction or excessive age (Cosmo too-old, Devonshire under construction). Repro: Devonshire Residences / Cosmo. Source: critics/real-user/2026-04-28-rental-tracker-analysis.md

