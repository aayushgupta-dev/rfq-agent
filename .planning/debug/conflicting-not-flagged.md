---
status: diagnosed
trigger: "Vendor response with two contradictory total prices (USD 1.2M vs $950,000) extracted as 'present' USD 1.2M, never flagged conflicting. $950k silently dropped. READ-ONLY diagnosis."
created: 2026-06-29T04:40:06Z
updated: 2026-06-29T04:40:06Z
---

## Current Focus

hypothesis: conflicting status depends entirely on model judgment; grounding gate only clamps ungrounded->missing/unsupported (one direction), never upgrades present->conflicting. Sample data may not exercise same-field conflict so it's untested.
test: read grounding/gate.py + sample vendor data
expecting: gate has no conflict-detection; samples have no same-field total contradiction
next_action: read grounding/gate.py and grounding/report.py and sample data

## Symptoms

expected: A clear contradiction between two stated values for the SAME field (total_price USD 1.2M vs $950,000) surfaced as status=conflicting with both values shown.
actual: total_price extracted as present "USD 1.2M", grounded to the 1.2M sentence; $950k silently dropped; never flagged conflicting.
errors: none (silent wrong behavior)
reproduction: paste vendor text with both "USD 1.2M" and "$950,000 fully inclusive" total statements into extraction flow.
started: always (design gap, not regression)

## Eliminated

## Evidence

- timestamp: 2026-06-29T04:40:06Z
  checked: extraction.v1.md prompt
  found: Prompt DOES define conflicting state (lines 54-57, example 4 lines 241-275) for "two or more statements that genuinely contradict each other on the same field". Instruction is generic, covers same-field contradictions. Conflict detection is 100% model-driven.
  implication: Prompt is not the obvious gap; it instructs conflict detection. Model judgment miss possible. But check whether grounding gate could ever produce conflicting.

- timestamp: 2026-06-29T04:40:06Z
  checked: envelope.py schema
  found: Full conflicting path exists — FlagStatus.conflicting, ConflictingValue[T], Field.values[], validator enforcing non-empty values w/ evidence (lines 72-103, 131-147). Schema fully supports conflicting.
  implication: Schema is NOT the gap.

- timestamp: 2026-06-29T04:40:06Z
  checked: extraction.py agent
  found: ground_model(raw, sources) is the only post-model code transform (line 213). Need to read gate.py to see clamp directions.
  implication: gate.py is the key file for clamp-direction question.

- timestamp: 2026-06-29T04:45:00Z
  checked: grounding/gate.py clamp directions
  found: ground_field (lines 236-317) only DOWNGRADES. present/unclear/conflicting -> unsupported if any evidence unlocatable. It NEVER upgrades present->conflicting. It has a conflicting BRANCH (lines 257-291) that grounds an already-conflicting field's per-value evidence, but it only processes status the model already set. No cross-field/cross-statement contradiction detection. By design pure & LLM-free.
  implication: Conflict DETECTION is impossible in code here — it would require semantic comparison of two free-text claims (model-judgment task). Gate is one-directional (downgrade only). Confirms grounding gate is not where conflict can be born.

- timestamp: 2026-06-29T04:45:00Z
  checked: committed sample vendors (data/*.json mess_spec) + total_price text
  found: vendor_fluff has 2 internal_conflict mess_specs but BOTH are per-line-item TIMELINE conflicts (tvc-production 8wk vs 14wk; launch-management 6wk vs 18wk) — NOT total_price. vendor_thorough has a latent number mismatch (TVC Production USD 468,500 in summary table vs USD 488,500 in breakdown) but it was injected as marketing_fluff, not flagged as a conflict the extractor is told to find, and it's a per-item not grand-total figure. NO committed sample contains two contradictory grand TOTALS. fluff total is a coherent ladder (services 849k-1,098k + media envelope -> ~1.2M total), not a contradiction.
  implication: The exact reported scenario (two contradictory total_price values) is UNTESTED by any committed sample. conflicting on total_price has never been exercised on real conflicting input.

- timestamp: 2026-06-29T04:45:00Z
  checked: test suite conflicting coverage
  found: conflicting is tested only with hand-built Field objects (test_field_envelope.py validator tests, test_grounding_gate.py grounding of pre-set conflicting field). test_extraction_agent.py:477 only branches IF status==conflicting — never asserts the model PRODUCES conflicting from contradictory input. No end-to-end test feeds contradictory text and asserts conflicting comes out.
  implication: Systemic: the conflicting->surfaced pipeline is verified structurally (schema/gate) but never behaviorally (model actually emitting it from real contradictions).

## Resolution

root_cause: >
  Conflict DETECTION is 100% model-judgment, driven solely by the extraction prompt
  (extraction.v1.md lines 54-57 + example 4 lines 241-275). There is NO code path that
  can produce status=conflicting — the grounding gate (gate.py ground_field, lines 236-317)
  is strictly one-directional: it only DOWNGRADES present/unclear/conflicting -> unsupported
  on unlocatable evidence, and its conflicting branch (257-291) merely re-grounds a field the
  model ALREADY marked conflicting. Schema (envelope.py) fully supports conflicting but is
  passive. So when the model returns total_price as present "USD 1.2M", nothing downstream
  can detect the dropped $950,000 — the gate happily grounds "USD 1.2M" (it IS in the text)
  and ships it. The miss is therefore a MODEL JUDGMENT MISS, made more likely by two prompt
  pressures: (a) total_price is a single-value Field with explicit "extract it as a decimal
  number" framing (extraction.v1.md line 129) that biases toward picking ONE number; (b) the
  only conflicting few-shot example is a TIMELINE narrative conflict, never a price conflict,
  so the model has no in-prompt anchor for treating two dollar totals as a conflict.
  Compounding it: this path is effectively UNTESTED — no committed sample injects a same-field
  total_price contradiction (the two internal_conflict samples are per-item timeline conflicts),
  so conflicting-on-price has never been observed working on real input. This is a systemic gap
  (unexercised path) surfacing as a one-off miss, not a regression.
fix: >
  READ-ONLY diagnosis — no fix applied. Smallest correct fix is PROMPT-side, in
  services/ai/prompts/extraction.v1.md, because semantic contradiction between two free-text
  totals is inherently model judgment and CANNOT be code-enforced (the gate proves the model's
  claim, it cannot invent a second claim the model didn't surface). Two concrete prompt edits:
  (1) In the total_price document-level bullet (line 128-129), add an explicit conflict
  instruction: if MORE THAN ONE distinct grand-total figure is stated anywhere in the response,
  return total_price as status=conflicting with one values[] entry per total — do NOT pick one.
  (2) Add a price-conflict few-shot example alongside example 4 (currently timeline-only) so the
  model has an in-prompt anchor for same-field numeric contradictions. Code-enforceable
  COMPLEMENT (optional, lower priority): a lightweight regex sweep could COUNT distinct
  currency-total candidates and, when total_price comes back present but >1 total-shaped figure
  exists in source, attach a soft "possible-unflagged-total" note to DowngradeReport for review
  — but it must NOT auto-rewrite status (would violate "never trust code to invent a claim";
  and false positives on per-item amounts are high). The honest division: detection is prompt;
  code can at most raise a review flag, never decide the conflict. Also recommend adding a
  same-field total_price contradiction to a committed sample + an extraction-agent test so the
  path is behaviorally covered.
verification: N/A (read-only diagnosis)
files_changed: []
