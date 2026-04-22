# Prompt: Generate Queries for a Persona

You will be given a persona markdown file. Your job: produce 3–5 natural-language
search queries the persona would plausibly type into SGCondoRentalSearch.

## Constraints

- Match the persona's language mix (`archetype_axes.language`).
- Span specificity: start vague ("2 bedroom near downtown"), end precise
  ("OUE Downtown One 2b2b 4000-4500 high floor").
- Do NOT invent numbers not implied by the persona. If budget is "no financial
  pressure at 210k salary", reasonable rent cap is ~$4,500, not $8,000.
- Include at least one query the parser is likely to mishandle — the persona
  doesn't know the grammar; users speak naturally. Example cue: "with gym nearby",
  "not too far from my office".
- Avoid duplicating query shapes across personas; look at recent sessions if
  available.

## Output format

A JSON array of strings. Nothing else. Example:

```json
[
  "2 bedroom near downtown 4500",
  "OUE Downtown 2b2b 4000-4500",
  "Tanjong Pagar 2房 4500以内 朝南",
  "quiet 2b2b near CBD with supermarket nearby",
  "Downtown MRT 2 bedroom high floor 4200"
]
```
