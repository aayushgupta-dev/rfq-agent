---
id: clarification
version: 1
intent: >
  Given a set of flagged fields (missing | unclear | conflicting | unsupported) from
  an ExtractionResult or ComparisonResult, draft specific, actionable clarification
  questions the buyer can send to the vendor. Each question is tied to a specific
  flagged field and references the ambiguous or missing information by name. Questions
  are phrased neutrally and professionally — not accusatory.
model_tier: cheap
failure_handling: >
  If a flagged field has insufficient context to generate a meaningful question,
  the output notes the field as "clarification not possible without more context"
  rather than generating a vague generic question. Questions are grounded in the
  extraction data — no new claims or assumptions are introduced. Generic questions
  ("Please clarify your pricing") are rejected; questions must name the specific
  field, line item, and the nature of the ambiguity.
---

TODO P4 / COMPARE-04: full clarification prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 4 and will include:
- Input: list of flagged ExtractionField objects with their flag status and context.
- Output: list of {field_id, vendor_id, question, why_needed} objects.
- Instructions to produce one specific question per flagged field (not a bulk ask).
- Style guide: professional, specific, non-accusatory, with the field name and
  the exact ambiguity described so the vendor knows precisely what to address.
- Fallback: if a question cannot be drafted meaningfully, explain why (not enough context).
