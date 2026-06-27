---
id: comparison
version: 1
intent: >
  Compare a set of ExtractionResult objects (one per vendor) across six dimensions:
  technical capability, commercial terms, scope coverage, timeline, compliance, and risk.
  Establishes comparability before any ranking — surfaces which vendors are truly
  comparable on each dimension and which require further information. Produces buyer
  attention points and a prioritised list of clarification questions. Never produces
  a misleading apples-to-oranges score.
model_tier: reasoning
failure_handling: >
  If vendor data is insufficient to compare on a dimension, the output states
  "not yet comparable — needs clarification" rather than forcing a ranking. Comparisons
  are grounded in extracted facts with evidence references; the model does not introduce
  new claims beyond what extraction produced. Vendors with missing critical fields are
  flagged as non-comparable until the gap is resolved. No fabricated scores or rankings.
---

TODO P4 / COMPARE-01: full comparison prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 4 and will include:
- Input schema: list[ExtractionResult] + the original RFQ for context.
- Per-dimension comparison instructions with explicit comparability checks.
- Output format: ComparisonResult pydantic schema with per-dimension comparisons,
  buyer attention points, and clarification questions.
- Instructions to surface differences (not normalise them away).
- Explicit prohibition on inventing numeric scores not derivable from extraction data.
- "Not comparable" signalling for dimensions with insufficient data.
