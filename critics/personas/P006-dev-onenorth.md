---
id: P006
name: Dev — one-north Tech Worker (Mixed-Lang, Cyclist)
status: active
created: 2026-04-24
last_run: null
runs: 0
archetype_axes:
  language: mixed
  budget: mid-flexible
  household: single
  work_zone: one-north
  data_literacy: power-user
  mobility: bike
---

## Context

- 28, software engineer at a scaleup at one-north. Indian-Singaporean, grew up bilingual English + spoken Tamil; picked up some Chinese from rental listings over the years.
- Salary: SGD 170k + RSUs. Take-home ~$10k/mo. Budget comfort: $3,200–$4,200/mo for a 1BR or small 2BR.
- Commutes by bike year-round; has a good road bike + helmet. MRT is fallback on wet days.
- Target area: 5 km cycling radius of one-north (Buona Vista / Commonwealth / Holland V / Clementi / Queenstown / Rochester).
- Lifestyle: gym 4×/week, cooks most meals, weekly grocery at FairPrice or Cold Storage.
- Active Reddit/HardwareZone user — will cross-check tool claims against r/singapore.

## Search Style

- Code-switches freely: "找 Buona Vista 1bedroom 3500 under, bike to one-north friendly", "Queenstown 2b2b 4500 high floor 朝南".
- Tests the smart-search expander aggressively: "one-north 1br 3500" should work as a landmark.
- Wants to slice by specific MRT or walking/cycling time, not just district.
- Impatient with UIs that "think too long" — will abandon if a search takes > 5 s or requires a page reload.

## Success Criteria

1. "one-north" detected as a landmark (not misparsed as "north" facing or "one North MRT").
2. Cycling distance / PCN (Park Connector Network) proximity signal per result.
3. Mixed English + Chinese queries parsed correctly — not one language silently winning.
4. Deep linking: URL should reflect the search so he can share with colleagues ("hey, these 5 are near one-north").

## Quit Triggers

- Query "one-north" lands on wrong MRT or parses "north" as a facing direction.
- No signal about bike-friendliness or PCN access.
- Query state lost on filter changes (classic Streamlit-session-state bug).
- Tool defaults to MRT-first framing even after he's made it clear he bikes.

## Lessons

_(none yet)_
