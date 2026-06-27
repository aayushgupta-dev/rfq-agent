---
id: messy-data-gen
version: 1
intent: >
  Given a vendor response draft and a "mess spec" (a list of specific complexity
  injections), transform the response to embed real-world data quality problems:
  missing pricing for selected line items, unclear or bundled scope, conflicting
  statements, vague timelines, weak compliance language, unstated assumptions.
  The output is the messied vendor response that the extraction agent must then parse.
model_tier: reasoning
failure_handling: >
  If the model fails to inject all specified mess points or produces output that
  is still clearly structured, the prompt instructs it to re-read the mess spec
  and confirm each injection is present and genuinely ambiguous. Partial injections
  are listed as extraction-flagging targets in the sample data notes.
---

TODO P2 / DATA-03: full messy-data generation prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 2 and will include:
- A structured mess-spec input: [{line_item, issue_type, injection_instruction}, ...].
- Instructions for each issue_type: "missing_price" → omit the number entirely;
  "bundled_scope" → merge two line items without naming them; "conflicting_timeline"
  → state two different dates in different sections; etc.
- A verification pass: re-read the output and confirm each mess point is present and
  that the injected ambiguity cannot be resolved without querying the vendor.
