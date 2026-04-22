# Prompt: Critique a Session from the Persona's POV

You will be given:
1. The persona markdown file.
2. The session bundle (queries, parsed criteria, smart-search summary, raw
   results, ranking notes).
3. Optionally: screenshots.

Your job: write a critique **as that persona would feel it**, not as an
engineer. Then emit findings.

## Score six axes (1–5, integer)

| Axis | What 5 looks like |
|---|---|
| Relevance | Top results match what this persona wants (budget, beds, area). |
| Info Density | Each row has enough to decide "viewing worth it?" without clicking out. |
| Commute Readability | Door-to-door time visible for the persona's workplace. |
| Price Transparency | Persona can tell if the estimate is a realistic ask vs. aspirational. |
| Lifestyle Signal | Evidence of amenities the persona cares about (gym, cafes, supermarket). |
| External Hop Necessity | Persona does NOT have to open PropertyGuru/Google to judge. |

One sentence of reasoning per axis.

## Emit findings

For each axis scored < 4, produce one finding:

- **Priority** P0 if the persona would abandon the tool; P1 if they'd complain
  but keep going; P2 if it's polish.
- **Symptom** — how the persona experiences it (not a code diagnosis).
- **Repro** — a specific query from this session that triggers it.

## Output format

```json
{
  "scores": {
    "relevance": 4,
    "info_density": 2,
    "commute_readability": 2,
    "price_transparency": 3,
    "lifestyle_signal": 1,
    "external_hop_necessity": 2
  },
  "reasons": {
    "relevance": "Five of top 10 are 2B2B in budget; one is 3BR noise.",
    "info_density": "Rows show project name, rent, psf — no floor, no facing.",
    "commute_readability": "MRT name visible but not minutes to OUE Downtown.",
    "price_transparency": "Median shown; P25/P75 hidden behind a chart tab.",
    "lifestyle_signal": "No signal at all for amenities near the project.",
    "external_hop_necessity": "Every promising row requires opening PropertyGuru."
  },
  "findings": [
    {
      "priority": "P1",
      "symptom": "Commute time isn't shown next to each result — I have to cross-check Google Maps for every one.",
      "repro": "OUE Downtown 2b2b 4500"
    }
  ],
  "next_run_lesson": "Users with a fixed workplace need door-to-door minutes in the result row, not just MRT name."
}
```
