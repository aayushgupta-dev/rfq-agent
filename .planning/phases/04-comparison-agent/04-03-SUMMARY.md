---
phase: 04-comparison-agent
plan: "03"
subsystem: services/ai/agents
tags: [comparison-agent, langgraph, tdd, fail-closed-clamp, draft-result-split, sse, prompt-pack]
dependency_graph:
  requires: [04-02]
  provides: [04-04]
  affects:
    - services/ai/agents/comparison.py
    - services/ai/api/app.py
    - services/ai/tests/test_comparison_agent.py
    - services/ai/prompts/comparison.v1.md
    - services/ai/prompts/clarification.v1.md
tech_stack:
  added: []
  patterns:
    - draft-result-split (model emits ComparisonDraft; code constructs ComparisonResult)
    - fail-closed-clamp (6×N matrix defaults not_comparable; ValueError→skip for unknown dims)
    - code-triggered-model-phrased (attention shells built by code, summaries filled by model)
    - one-result-event (clarify node emits single result; compare stores, not emits)
    - clarification-identity-validation (count+identity match; extras dropped; failure→AttentionPoint)
key_files:
  created:
    - services/ai/agents/comparison.py
  modified:
    - services/ai/api/app.py
    - services/ai/tests/test_comparison_agent.py
    - services/ai/prompts/comparison.v1.md
    - services/ai/prompts/clarification.v1.md
decisions:
  - "Model emits ComparisonDraft (proposed verdicts+phrasing only); ComparisonResult is code-constructed — closes the model-authors-reliability-critical-surfaces BLOCKER (Review Fix 1+2)"
  - "_apply_verdict_clamp is fail-closed: 6×N matrix pre-filled with not_comparable; unknown ComparisonDimension strings caught by StrEnum coercion, default not_comparable applies (Review Fix 1)"
  - "_ceiling_for_flags: explicit per-dimension empty-case branch — compliance=partially, risk=comparable, others=not_comparable (Review Fix 4 / RESEARCH A2)"
  - "cross_vendor_conflict detection compares PRESENT VALUES across vendors (not per-field conflicting status) — Review Fix 10"
  - "Exactly one result SSE event emitted by clarify node; compare node stores result in state (Review Fix 9)"
  - "Clarification failure → AttentionPoint(trigger_type=clarification_generation_failed); result not aborted (Review Fix 8)"
  - "_build_offer_table builds from ExtractionResult verbatim; model cannot author verbatim values (Review Fix 6)"
  - "_build_vendor_readiness preserves input order, no sort key (D-07)"
  - "comparison.v1.md and clarification.v1.md authored in full (Prompt Pack)"
  - "_MAX_VENDORS=5 prototype limit with ponytail comment naming the ceiling and upgrade path"
metrics:
  duration: "25 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_created: 1
  files_modified: 4
---

# Phase 04 Plan 03: Comparison Agent — 4-Node StateGraph with Fail-Closed Clamp

Wave 3: implemented the 4-node comparison LangGraph agent with draft/result split, fail-closed clamp, code-built surfaces, and the POST /compare/vendors SSE route. 17 of 20 RED stubs are now GREEN; the single remaining stub (test_comparison_traces_committed) stays RED for Wave 4.

## What Was Built

**services/ai/agents/comparison.py** (4-node StateGraph):

- `_ceiling_for_flags(flag_statuses, dimension)` — D-04 ceiling rule with explicit per-dimension empty-case: compliance=`partially`, risk=`comparable` (RESEARCH A2), others=`not_comparable` (fail-closed). Takes `ComparisonDimension` parameter so the empty-case branch is per-dimension, not a single fall-through. (Review Fix 4)
- `clamp_verdict(model_verdict, code_ceiling)` — downgrade-only; code cannot upgrade. Uses `_VERDICT_ORDER` dict.
- `_apply_verdict_clamp(draft, ceilings, vendor_names)` — fail-closed: pre-fills full 6×N matrix with `not_comparable`, walks draft dimensions with `ComparisonDimension(str)` coercion (ValueError→skip), records `ClampEntry` on downgrade, builds `list[DimensionComparison]` from completed matrix. (Review Fix 1)
- `_build_offer_table(extractions, rfq)` — code-side construction from ExtractionResult verbatim values. Model cannot author this table. (Review Fix 6 / D-05)
- `_build_vendor_readiness(vendor_names, dimensions)` — input order preserved, no sort key. (D-07)
- `_build_attention_shells(triggers)` — builds AttentionPoint shells per code-detected trigger; summary is empty string filled by model. Model-invented trigger types are dropped. (Review Fix 7 / D-08)
- `_collect_flagged_fields(extractions)` — read-only recursive walker (mirrors gate.py _walk_and_ground); blockers-first sort. (Review Fix 8 / D-09)
- `_detect_attention_triggers(extractions, ceilings)` — 4 trigger types: `comparability_blocker`, `missing_pricing`, `cross_vendor_conflict` (cross-vendor value diff, not per-field flag; Review Fix 10), `compliance_gap`.
- `_check_rfq_alignment(extractions, rfq)` — returns vendor names whose line_items don't cover RFQ line_item_ids. (Review Fix 11)
- 4 nodes: `align` (isinstance guard), `comparability` (ceilings+triggers), `compare` (model call, build result, store in state — no emit), `clarify` (clarification call, identity validation, EMIT single result event). (Review Fix 9)
- `comparison_graph` — compiled StateGraph (align→comparability→compare→clarify)
- `run_comparison(extractions, rfq)` — sync testable wrapper; calls 4 `_run_*_impl` functions directly; returns state with `last_sse_event` and `result_sse_event`.
- `generate_comparison_with_trace(extractions, rfq)` — returns (raw_draft, clamped_result, clamp_report, clarification_questions) for D-11 trace capture.

**services/ai/api/app.py**:

- `ComparisonRequest` — `list[ExtractionResult]` + `RFQ`; `model_validator` rejects >5 vendors (422 via FastAPI pydantic); `_MAX_VENDORS=5` documented with ponytail comment.
- `POST /compare/vendors` — EventSourceResponse pattern mirrors `/extract/vendor`; clamp runs server-side before result event (D-03); exactly one result event (Review Fix 9).

**services/ai/prompts/comparison.v1.md** — full prompt authored: dimension definitions, field mappings, verdict guidance, prohibition list, attention trigger contract. (Prompt Pack)

**services/ai/prompts/clarification.v1.md** — full prompt authored: one-question-per-field rule, status-specific guidance, identity-match requirement (same count and order as flagged_fields). (Prompt Pack)

**services/ai/tests/test_comparison_agent.py** — 17 stubs turned GREEN:
- All original 13 stubs (schema, clamp, SSE taxonomy, truncation/refusal, etc.)
- All 7 review-fix stubs: e2e clamp (Review Fix 1 BLOCKER), empty compliance/risk ceilings (Review Fix 4), dimension StrEnum fail-closed (Review Fix 1), cross-vendor conflict (Review Fix 10), RFQ alignment (Review Fix 11), clarification failure AttentionPoint (Review Fix 8)
- `test_comparison_traces_committed` remains `NotImplementedError` — Wave 4

## Verification

- `uv run pytest tests/test_comparison_agent.py -q` → 19 passed, 1 failed (test_comparison_traces_committed NotImplementedError — Wave 4 stub)
- `uv run pytest -q` → 135 passed, 1 failed (same stub), 1 xfailed — no regressions
- Task 1 verify: `clamp_verdict`, `_ceiling_for_flags`, `_collect_flagged_fields`, `comparison_graph` all import and behave correctly
- Vendor count guard: `ComparisonRequest` with 6 extractions raises `ValidationError` (→ 422)

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

The plan specified 16 stubs GREEN (Task 2 `<done>` says "17 listed tests pass"). The implementation made 17 stubs GREEN (the 2 Wave-2 stubs + 17 Wave-3 stubs = 19 of 20 total). `test_comparison_traces_committed` is the 1 remaining Wave-4 stub. Counts match the plan's intent.

## Known Stubs

`test_comparison_traces_committed` in `services/ai/tests/test_comparison_agent.py` is an intentional Wave-4 RED stub. Wave 4 (plan 04-04) will generate the comparison trace artifact and make it GREEN.

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| New SSE endpoint | services/ai/api/app.py | POST /compare/vendors — accepts list[ExtractionResult] + RFQ; guarded by _MAX_VENDORS=5 and pydantic validation (T-04-03-08 mitigated) |

All STRIDE threats from the plan's threat register are mitigated:
- T-04-03-01: clamp test asserts emitted result downgraded — GREEN
- T-04-03-02: with_structured_output(ComparisonDraft) — model structurally cannot emit ComparisonResult
- T-04-03-03: ComparisonDimension(StrEnum) coercion; test_dimension_enum_fail_closed — GREEN
- T-04-03-04: _build_attention_shells; model-invented types dropped; test_attention_points_are_triggered — GREEN
- T-04-03-05: clarification identity validated; extras dropped; test_clarification_seeded_by_code — GREEN
- T-04-03-06: single result event from clarify node; test_comparison_sse_taxonomy — GREEN
- T-04-03-07: _build_offer_table code-built; test_offer_table_code_built — GREEN
- T-04-03-08: ComparisonRequest._check_vendor_count rejects >5 vendors (422) — verified
- T-04-03-09: _run_align_impl isinstance(e, ExtractionResult) guard — implemented

## Self-Check

- [x] services/ai/agents/comparison.py exists (created, ~460 lines)
- [x] services/ai/api/app.py contains "compare/vendors"
- [x] services/ai/prompts/comparison.v1.md — full prompt (not TODO stub)
- [x] services/ai/prompts/clarification.v1.md — full prompt (not TODO stub)
- [x] services/ai/tests/test_comparison_agent.py — 17 stubs GREEN, 1 stub stays RED (Wave 4)
- [x] Commit c57380b: comparison agent 4-node StateGraph
- [x] Commit ec20f29: POST /compare/vendors route + 17 test stubs GREEN

## Self-Check: PASSED
