---
id: extraction
version: 1
intent: >
  Read a single vendor response and produce a structured ExtractionResult: per-field
  extracted values across scope, pricing, commercial terms, timeline, compliance,
  assumptions, exclusions, and risks. Every extracted fact carries an evidence snippet
  (verbatim text + char offsets). Fields that are absent, ambiguous, contradictory, or
  unverifiable are explicitly flagged with the appropriate status
  (missing | unclear | conflicting | unsupported) — never silently filled or omitted.
model_tier: reasoning
failure_handling: >
  Never fill missing info. If a field cannot be traced to a verbatim snippet in the
  vendor response, its status is "missing" or "unclear" — not a fabricated value.
  Evidence offsets (char_start, char_end) are validated in code against the source text
  (P3 grounding gate) — the model is not trusted to self-attest that offsets are correct.
  Conflicting statements produce status "conflicting" with a values[] list, each entry
  referencing its own evidence snippet. Unsupported claims (assertions without backing)
  produce status "unsupported".
---

TODO P3 / EXTRACT-01: full extraction prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 3 and will include:
- A detailed system instruction establishing the evidence-over-assertion contract.
- Per-field extraction instructions for each ExtractionResult field.
- Explicit instructions for each flag status (missing/unclear/conflicting/unsupported)
  with examples of when each applies.
- Output format: structured JSON matching the ExtractionResult pydantic schema.
- Anti-hallucination instructions: if no verbatim evidence exists, the field is absent.
- Clarification question generation: for each flagged field, propose a specific question
  the buyer could send to the vendor to resolve the ambiguity.
