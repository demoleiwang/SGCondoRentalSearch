# Real-User Rental Tracker — Analysis (2026-04-28)

The repo owner shared a personal spreadsheet of 30+ condos they have been
tracking while shopping for a 2BR (mostly 2b2b/2b1b/1b1b) rental in central
Singapore. This is direct evidence of how a real shopper uses the data —
substantially richer than what the synthetic personas have surfaced so far.

## Inferred user profile

- Workplace likely near **Dhoby Ghaut / Sophia / Bras Basah** (fastest commutes:
  Sophia Hills 8 min, Haus On Handy 5 min, Nathan Residences 14 min, Aspen LinQ
  19 min, Killiney 118 19 min). Marcus's OUE Downtown profile is close but
  not identical — this user's anchor is more central than CBD.
- Budget band **$2,800–$4,500/mo** depending on bedroom config; happy to bend.
- Tracking three configs simultaneously: 1b1b ~$3,300, 2b1b ~$3,800–$4,300,
  2b2b ~$3,500–$4,500.
- Bilingual annotations: 牛车水 (Chinatown), 富康宁 (Fort Canning),
  多美歌 (Dhoby Ghaut), 乌节路 (Orchard), 西海岸 (West Coast).
- Goes deep enough to bookmark specific PropertyGuru listing URLs, not
  project pages.

## Raw data snapshot

| Project | Area | Year, lease (yrs) | Sqft | Commute (min) | 1b1b | Target | 2b1b | 2b2b | URL |
|---|---|---|---|---|---|---|---|---|---|
| The Scala | | 2013, 3.5 | 474 | 38 | 3300–3400 | 3100 | | 4480 | |
| Forest Woods | | 2021, 4.5 | 667 | 31 | | 3200 | | 3900 | |
| THE TRE VER | | 2023, 5 | 743 | 34 | | 3000 | 3800 | | |
| Botanique at Bartley | | 2019, 3.9 | 657 | 36 | | 3000 | | 3600–3800 | |
| Parc Esta | | 2022, 4.2 | 624 | 32 | | 3200 | | 4300 | |
| Sophia Hills | | 2018, 3.9 | 450 | 8 | 3600 | 3400 | | | |
| Nathan Residences | great world | 2015, 4.1 | 592 | 14 | | 3300 | | | |
| The Landmark | 牛车水 | 2025, 5 | | 20+ | | 3400 | | | |
| Archipelago | bedok 旁边 | 2015, 4.1 | 840 | 35 | | 3000 | 4000 | | listing URL |
| Sky Vue | bishan | 2017, 4.3 | 484 | 33 | 3500 | 3300 | | | |
| Verticus | bishan | 2024, 5 | 441 | 37 | 3400 | 3100 | | 4000 | listing URL |
| Stirling Residences | queenstown | 2022, 4 | | 39 | | 3400 | | | |
| Commonwealth Towers | queenstown | 2017, 5 | | 34 | | 3300 | | | |
| The Mercury | beauty world | | 635 | 29 | 3950 | 3600 | | | listing URL |
| Aspen LinQ | 富康宁 | | 722 | 19 | | 2800 | 4200 | | listing URL |
| Sky Habitat | bishan | | 710 | 33 | 3900 | 3700 | | | listing URL |
| Gem Residences | bishan | | 570 | 35 | | 2800 | | 3700 | listing URL |
| Fourth Avenue Residence | | , 4.3 | 689/624 | 43 | | 3500 | 4500 | 4500 | |
| RoyalGreen | | | 721/667 | 46 | | | | 4200–4400 | |
| Normanton Park | 西海岸旁边 | | 657 | 45 | | 3100 | | 4100 | listing URL |
| The Glades | bedok 旁边 | | 721/591 | 44 | | 2800 | 3850 | 3500 | listing URL |
| Midwood | | | 635 | 53 | | 3000 | | 3900 | |
| The Navian | | | 657 | 35 | | | 3900 | | |
| euHabitat | | | 904 | 40 | | | 3800 | | |
| 26 Newton | | | 560 | 25 | | | 3500 | | |
| Haus On Handy | 多美歌 | | 614/517 | 5 | | | | 4300–4500 | |
| The Woodleigh Residences | | | 592 | 28 | | | | 4200 | |
| Killiney 118 | 乌节路 | | 900 | 19 | | | 4250 | | listing URL |
| Waterfront Gold | | | 667 | 39 | | | | 3500 | |
| Devonshire Residences | 富康宁 (有建筑工地) | | 495 | | 3400 | | | | listing URL |
| Cosmo | 乌节路 (房子太老了) | | | | | | | | |
| Robin Residence | | | 538 | 38 | | | | 4000 | |

## Field-by-field gap analysis vs current app

### 1. Year built + remaining lease — **NEW gap, P1**

The user records every project's TOP year and lease balance ("2013, 3.5",
"2025, 5"). The app surfaces neither. For a rental, lease balance affects
landlord behavior (last-stretch lease often = aggressive renewal pricing or
delayed maintenance). For a condo's resale value framing, age matters too.

**File as:** `F011 (P1) Year built and remaining lease not shown — users
manually look these up on PropertyGuru and annotate sidecar spreadsheets.`

### 2. Per-unit sqft and size variants — **REINFORCES F005, NEW REFINEMENT P2**

The app uses `TYPICAL_SIZES` (one number per bedroom count). The user records
real sqft per project and crucially **multiple sizes per project**: "689/624"
for Fourth Avenue Residence, "721/667" for RoyalGreen, "721/591" for The Glades.
The same project rents at very different prices depending on stack. Forcing
one typical size per bedroom count erases this signal entirely.

**File as:** `F012 (P2) Size variants within a project (e.g. 689/624 sqft for
2B2B) not surfaced — single-typical-size assumption hides per-stack rent
spread that real shoppers care about.`

### 3. Door-to-door commute time — **PROMOTE F002 from P1 to P0**

Every single row in the user's tracker has a commute-minutes column, manually
copied from Google Maps. This is the single most-tracked field. F002 is
already filed but as P1 (Marcus's framing was "still shoppable without it").
Real-user evidence shows it is **the universal organizing dimension** — users
won't merely tolerate its absence, they will rebuild it themselves on the
side. Bump priority.

**Action:** re-prioritize `F002` from P1 to P0.

### 4. Per-bedroom-config target prices — **NEW gap, P2**

The user's columns are `1b1b`, `Target`, `2b1b`, `2b2b` — they track different
configurations of the same project as separate rows of data. The app shows one
est-rent per bedroom count globally. There is no concept of a "shortlist
across configs for the same project".

**File as:** `F013 (P2) No way to track multiple bedroom configs for the same
project on a single shortlist — the user's spreadsheet has separate columns
for 1b1b / 2b1b / 2b2b targets per project.`

### 5. Specific listing URLs vs project search — **NEW gap, P2**

The app's PropertyGuru link is a project-name + bedroom + price-range search.
The user records direct listing URLs (`/listing/for-rent-archipelago-19342387`)
because that is the actionable artifact. Once the user identifies a viable
unit they want a stable bookmark, not a list that may have moved.

**File as:** `F014 (P2) PropertyGuru integration links to project search but
real shortlists track specific listing URLs (deeper than project name) — once
a user picks a stack/floor, they want a stable per-listing bookmark.`

### 6. Adjacency / nuisance signals — **NEW gap, P2**

User explicitly excludes projects with "有建筑工地" (adjacent construction)
and "房子太老了" (too old) — Cosmo and Devonshire Residences are both on the
spreadsheet but greyed out because of these. The app has no field for either.
Construction-adjacent data is genuinely hard (would need a planning-permit
data source); building-age data is easy (we have TOP year if we add it).

**File as:** `F015 (P2) No nuisance / adjacency signal — adjacent construction
sites and "too old" stigma are common manual exclusions; the building-age half
becomes free if F011 ships.`

### 7. Chinese landmark variants and shopping-mall names — **NEW gap, P1**

The user annotates with `great world`, `beauty world`, `富康宁`, `多美歌`,
`牛车水`, `乌节路`, `西海岸`. Cross-checking `LANDMARKS` in `smart_search.py`:

| User's term | English | In LANDMARKS dict? |
|---|---|---|
| great world | Great World City | ❌ |
| beauty world | Beauty World MRT/Mall | ❌ |
| 富康宁 | Fort Canning | ❌ |
| 多美歌 | Dhoby Ghaut | ❌ |
| 牛车水 | Chinatown | ❌ |
| 乌节路 | Orchard | ❌ as Chinese (only "orchard" works) |
| 西海岸 | West Coast | ❌ |

7 of 7 user-volunteered landmark terms miss the dict. This is the gap that
turns a "smart" search into a "lucky" one.

**File as:** `F016 (P1) Chinese-language landmark synonyms (富康宁, 多美歌,
牛车水, 乌节路, 西海岸) and common Singapore mall/area names (Great World,
Beauty World) are missing from the LANDMARKS dict — Chinese-speaking and
local-vernacular users get silent fall-through to plain MRT search.`

## Cross-validation against synthetic personas

| Real-user gap | Synthetic persona predicted? |
|---|---|
| Year built / lease | No persona has flagged it yet (would expect P004 Priya for tenure, P005 陈阿姨 for data lineage). |
| Sqft variants | Aligns with Marcus F005 + new refinement F012. |
| Commute mins | Marcus F002 (already filed) — real user confirms intensity. |
| Per-config tracking | No persona — emerges from genuine cross-config shopping. |
| Specific listing URLs | No persona — Marcus quit-trigger was "must click PG", but at level of project not listing. |
| Adjacency / age | No persona — yet. Could feed P005 陈阿姨 next run (data-skeptic). |
| Chinese landmarks | Predicted by P002 张伟 / P005 陈阿姨 (zh-only); first run will validate. |

## Implications for the persona library

- **P002 张伟 and P005 陈阿姨** should run NEXT — they are the personas best
  positioned to find F016 organically. If they fail to (because they default
  to using Pinyin or English), that itself is a finding.
- The real user is roughly **a budget-tighter Marcus** (lower budget,
  central-not-CBD anchor). Worth considering whether to retire / refine
  Marcus toward this real profile, or add a new persona modeled on it.
- **Per-config shortlist tracking (F013)** isn't a feature any persona has
  thought to ask for. Real shoppers cross-track configs because budget at
  1b1b ($3,300) vs 2b2b ($4,500) maps to different lifestyle decisions.
  This deserves to be a future persona prompt: "shopping multiple configs
  in parallel".

## Suggested next moves (in priority order)

1. **Implement F002 (P0): door-to-door commute minutes per result.** Highest
   ROI based on real-user evidence; touches every persona's review.
2. **Implement F016 (P1): expand LANDMARKS dict with Chinese + mall variants.**
   ~30-min change, instantly validates P002/P005's first runs.
3. **Implement F011 (P1): year built + remaining lease columns.** URA dataset
   does not include this — would need a join to a separate lease-tenure
   source. Easier alternative: scrape from PropertyGuru (fragile) or
   data.gov.sg property-info dataset (need to investigate).
4. Schedule the next /critic-run as **P002 张伟** (because F016 directly
   affects him) instead of going strict round-robin.
