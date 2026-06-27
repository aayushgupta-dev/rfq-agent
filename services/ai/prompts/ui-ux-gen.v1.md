---
id: ui-ux-gen
version: 1
intent: >
  Generate buyer-facing UI structure, dashboard section layouts, comparison view
  organisation, and UX copy for the Bid Desk procurement copilot. Output is captured
  as design/prompt artifacts that guide implementation of the five buyer screens:
  RFQ Overview, Vendor Upload/Input, Extraction Review, Vendor Comparison, Prompt Trace.
model_tier: reasoning
failure_handling: >
  If the model produces generic SaaS dashboard copy or ignores procurement-specific
  buyer needs, the prompt re-asserts the buyer context: sense-making under uncertainty,
  not scoring. Generated UI sections that hide or omit missing/unclear data states are
  rejected — absence must be first-class in every view. Generic terms ("N/A", "—") are
  insufficient; the UI must surface why information is absent.
---

TODO P5 / UI-01: full UI/UX generation prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 5 and will include:
- Buyer persona context: procurement professional under time pressure, grading vendors.
- Per-screen structure prompts with explicit sections for missing/unclear/conflicting states.
- UX copy guidelines: evidence-first, absence-explicit, comparability-before-ranking.
- Component naming and hierarchy for the Extraction Review and Comparison views.
- Instructions to produce structured output (JSON/Markdown) that maps to the component tree.
