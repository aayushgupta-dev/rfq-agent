---
id: rfq-gen
version: 1
intent: >
  Generate one realistic marketing-services RFQ covering 8 line items (strategy & creative,
  TVC development, TVC production, social organic, paid media planning, paid media buying,
  kids advertising & claims compliance, launch program management), with scope, timelines,
  commercial expectations, a vendor questionnaire, and compliance requirements.
  Must feel like a real procurement event — not a clean sample.
model_tier: reasoning
failure_handling: >
  If the generation model produces a generic or unrealistically tidy RFQ, the prompt instructs
  it to inject specificity: named deliverables, concrete timelines, explicit commercial
  constraints, and real compliance clauses. Missing or vague generated fields are flagged
  for human review before committing as sample data.
---

TODO P2 / DATA-01: full RFQ generation prompt.

This stub reserves the prompt slot. The full prompt is authored in Phase 2 (data generation)
and will include:
- System instructions establishing the procurement context and realism bar.
- Per-line-item scope templates.
- Instructions to generate specific (not generic) deliverables, dates, and budget ranges.
- Questionnaire and compliance section templates.
- Anti-hallucination instructions: no invented company names or technologies not listed.
