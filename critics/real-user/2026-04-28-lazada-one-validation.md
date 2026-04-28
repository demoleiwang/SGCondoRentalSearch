# Lazada One Validation — Smart Search vs Real Shortlist (2026-04-28)

After fixing F016 (LANDMARKS dict expansion to include "Lazada One"), I ran
`expand_query("Lazada One <config> <budget>")` for the configurations and
budget bands the real user actually shops, then cross-referenced the
returned projects against the user's hand-curated tracker (32 projects).

## Setup

- LANDMARKS now resolves "Lazada One" → `Lazada One Singapore 51 Bras Basah Road`.
- OneMap geocodes it to `(1.2979, 103.8502)` — Bras Basah / Sophia / Dhoby Ghaut area.
- Smart search expands to 13 nearby MRT stations (Bras Basah, City Hall,
  Dhoby Ghaut, Esplanade, Bencoolen, Bugis, Rochor, Jalan Besar, Fort
  Canning, Promenade, Little India, Clarke Quay, Nicoll Highway, Raffles
  Place — all within ~1.5 km).

## Cross-reference

| Query | Tool results | Tracker overlap |
|---|---|---|
| `Lazada One 2b2b 4500` | 35 | **0** |
| `Lazada One 2b1b 4000` | 31 | **0** |
| `Lazada One 1b1b 3500` | 0 | 0 (no results at all) |
| `Lazada One 2br 5000` | 0 | 0 |

**Zero overlap.** The tool returns 35 candidates the user has not tracked,
and zero of the 32 the user has tracked.

## Why — three stacked reasons

### 1. Premium D9 projects exceed 2BR budget by 10–40%

Of the user's 32 tracker projects, the 3 closest to Lazada One geographically
(Sophia Hills, Haus On Handy, Devonshire Residences) are all in District 9.
Their 2BR estimates are:

| Project | Median psf | Est 2BR @ 750sqft | User's actual targeting |
|---|---|---|---|
| Sophia Hills | 6.79 | **$5,092** | 1b1b @ $3,400 |
| Haus On Handy | 8.63 | **$6,473** | 2b2b @ $4,300–4,500 |
| Devonshire Residences | 6.79 | **$5,092** | 1b1b @ $3,400 |

The user is shopping these projects at smaller configurations. The tool is
hard-coded to "one bedroom count per query"; the user's reality is "1BR here,
2BR there, same shortlist".

**This is F013** (multi-config shortlist) demonstrated end-to-end.

### 2. The 1.5 km radius drops projects 5–10 km away that the user tolerates

The user's tracker has 13 projects with 30–53 minute commutes — they live in
districts 3 (Queenstown), 12 (Toa Payoh), 13 (Potong Pasir), 14 (Eunos), 19
(Serangoon/Bartley), 20 (Bishan). Smart search's 1.5 km radius cannot reach
any of them. From the user's perspective, "near Lazada One" means **≤35 minute
door-to-door**, which by MRT can be 6–10 km.

**This is F002** (commute time, not distance) and **F004** (radius
uncontrollable) demonstrated end-to-end.

### 3. The 1b1b query returned zero results

`Lazada One 1b1b 3500` returned 0 results despite Sophia Hills and Devonshire
both fitting (median_psf 6.79 × 500 sqft = $3,395). Likely cause: query parser
default-budget bracket is too tight (±10 %) for "3500" — anything outside
$3,150–$3,850 is filtered. Sophia Hills D9 1BR contracts span wider stacks.

This is a separate parser issue worth filing.

## New finding from this validation

- **(P1) `F017` Default ±10 % price bracket on bare-number budgets is too
  tight for premium-district 1BR queries** — `Lazada One 1b1b 3500` returns
  zero results even though projects with median 1BR rent of $3,395 exist
  within the search radius. Either widen the default bracket to ±15 %, or
  surface the bracket explicitly with a slider.

## Big-picture interpretation

Adding Lazada One to the LANDMARKS dict fixed the **landmark-detection** half
of the user's behavior. The deeper half — that the user's actual shortlist
spans 6 districts, 3 bedroom configs, and 30–50 minute commutes — is not a
landmark-dictionary problem. It needs:

1. **Door-to-door commute filter** (F002, P0) replacing the 1.5 km radius as
   the primary geographic filter.
2. **Multi-config shortlist** (F013, P2) so the same project can appear with
   different configurations.
3. **Looser default budget bracket** (F017, P1, new).

Until those land, the smart-search recommendation will be a different list
from the one a thoughtful real shopper actually keeps.

## Implication for persona prioritization

The real-user evidence we now have is structurally richer than any persona
critique. Recommendation: when picking the next persona to run, prioritize
those whose archetype amplifies these gaps — **P002 张伟** (tight budget,
zh-only landmarks, will hit F017 hard) and **P006 Dev** (one-north landmark
parsing, mixed-language). If a persona run produces findings already implied
by the real-user evidence, log them once and don't double-count.
