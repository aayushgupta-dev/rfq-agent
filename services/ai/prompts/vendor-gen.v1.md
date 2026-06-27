---
id: vendor-gen
version: 1
intent: >
  Generate a single vendor response to a given RFQ — deliberately realistic and messy.
  Each vendor responds in a different format with different levels of completeness,
  pricing structure, scope coverage, timeline specificity, assumptions, and clarity.
  Outputs must feel like real vendor proposals, not sanitised templates.
model_tier: reasoning
failure_handling: >
  If the generation model produces a clean, complete, or uniformly-formatted response,
  the prompt instructs it to introduce realistic flaws: missing line items, bundled vs
  per-item pricing ambiguity, vague timelines ("Q3"), assumptions buried in footnotes,
  currency/tax ambiguity. A response that answers every question precisely is rejected
  as unrealistic.
---

TODO P2 / DATA-02: full vendor response generation prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 2 and will include:
- A "vendor persona" parameter controlling the response style (e.g. thorough-but-vague,
  aggressive-on-price, missing-scope, over-promising timelines).
- Instructions to vary pricing label conventions (day rate vs project fee vs retainer),
  scope granularity, and completeness per persona.
- Explicit anti-patterns to generate: partial scope coverage, unstated assumptions,
  tax/currency ambiguity, conflicting statements within the same response.
