---
phase: 4
slug: comparison-agent
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-28
updated: 2026-06-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Updated post cross-AI review (04-REVIEWS.md) to add 7 new test stubs and sharpen 3 existing ones.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.1.1 (services/ai) |
| **Config file** | services/ai/pyproject.toml |
| **Quick run command** | `cd /Users/aayush/projects/aerchain/services/ai && uv run pytest -q tests/test_comparison_agent.py` |
| **Full suite command** | `cd /Users/aayush/projects/aerchain/services/ai && uv run pytest -q` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest -q tests/test_comparison_agent.py`
- **After every plan wave:** Run `cd services/ai && uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 35 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| conftest_comparison | 04-01 | 1 | COMPARE-01 | T-04-01-01 | ExtractionResult builders validate via pydantic | unit | `cd services/ai && uv run python -c "from conftest_comparison import missing_extraction; print('OK')"` | ❌ W0 | ⬜ pending |
| test stubs (20 total) | 04-01 | 1 | COMPARE-01..05 | — | All 20 stubs discovered, all raise NotImplementedError | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py --collect-only -q` | ❌ W0 | ⬜ pending |
| schema shape | 04-02 | 2 | COMPARE-01 | T-04-02-01, T-04-02-04 | ComparabilityVerdict in domain.py; ComparisonDraft split; ClarificationSet in domain.py | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_schema_shape tests/test_comparison_agent.py::test_no_dict_shapes -v` | ❌ W0 | ⬜ pending |
| codegen drift | 04-02 | 2 | PLAT-02 | T-04-02-02 | pydantic2ts regenerates TS including ComparisonDraft + ComparisonDimension | integration | `cd services/ai && uv run pytest tests/test_codegen_drift.py -x` | ✅ (exists) | ⬜ pending |
| clamp only downgrades | 04-03 | 3 | COMPARE-02 | T-04-03-01 | clamp_verdict("comparable","not_comparable")=="not_comparable"; _ceiling_for_flags primitives | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clamp_only_downgrades -v` | ❌ W0 | ⬜ pending |
| no aggregation over missing | 04-03 | 3 | COMPARE-02 | T-04-03-01 | any missing field caps ceiling regardless of other present fields | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_no_aggregation_over_missing -v` | ❌ W0 | ⬜ pending |
| **clamp applied to result** (NEW Fix-1) | 04-03 | 3 | COMPARE-02 | T-04-03-01 | mock ComparisonDraft proposing comparable → emitted result verdict is not_comparable; model_proposed preserved; ClampEntry exists | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clamp_applied_to_result -v` | ❌ W0 | ⬜ pending |
| **dimension enum fail closed** (NEW Fix-1) | 04-03 | 3 | COMPARE-02 | T-04-03-03 | mis-cased "Commercial" dimension → not_comparable; no exception | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_dimension_enum_fail_closed -v` | ❌ W0 | ⬜ pending |
| **empty compliance ceiling** (NEW Fix-4) | 04-03 | 3 | COMPARE-02 | T-04-03-01 | _ceiling_for_flags([],compliance) == "partially" | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_ceiling_empty_compliance -v` | ❌ W0 | ⬜ pending |
| **empty risk ceiling** (NEW Fix-4) | 04-03 | 3 | COMPARE-02 | T-04-03-01 | _ceiling_for_flags([],risk)=="comparable"; _ceiling_for_flags([],technical)=="not_comparable" | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_ceiling_empty_risks -v` | ❌ W0 | ⬜ pending |
| attention triggers (tightened Fix-7) | 04-03 | 3 | COMPARE-03 | T-04-03-04 | trigger list from code only; fabricated trigger_type dropped from result | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_attention_points_are_triggered -v` | ❌ W0 | ⬜ pending |
| clarification seeded by code (tightened Fix-8) | 04-03 | 3 | COMPARE-03 | T-04-03-05 | count + identity match _collect_flagged_fields; model extras dropped | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clarification_seeded_by_code -v` | ❌ W0 | ⬜ pending |
| offer table code built (sharpened Fix-6) | 04-03 | 3 | COMPARE-04 | T-04-03-07 | _build_offer_table from ExtractionResult verbatim; pricing_verbatim=None where missing; no normalized fields | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_offer_table_code_built -v` | ❌ W0 | ⬜ pending |
| vendor order preserved | 04-03 | 3 | COMPARE-05 | T-04-03-01 | vendor_readiness list preserves input order after JSON round-trip | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_vendor_order_preserved -v` | ❌ W0 | ⬜ pending |
| no numeric score | 04-03 | 3 | COMPARE-05 | T-04-03-01 | no score/rank/weight field on ComparisonResult or VendorReadiness | unit (schema) | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_no_numeric_score -v` | ❌ W0 | ⬜ pending |
| SSE taxonomy + one result (Fix-9) | 04-03 | 3 | PLAT-04 | T-04-03-06 | all /compare/vendors event types in EVENT_TYPES; exactly one result event | integration | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_comparison_sse_taxonomy -v` | ❌ W0 | ⬜ pending |
| truncation error | 04-03 | 3 | EXTRACT-05 analog | T-04-03-01 | truncation → safe error event; recoverable=True | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_truncation_error_event -v` | ❌ W0 | ⬜ pending |
| refusal error | 04-03 | 3 | EXTRACT-05 analog | T-04-03-01 | refusal → safe error event; recoverable=False | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_refusal_error_event -v` | ❌ W0 | ⬜ pending |
| **cross vendor conflict** (NEW Fix-10) | 04-03 | 3 | COMPARE-03 | T-04-03-04 | different present timeline values across vendors → cross_vendor_conflict trigger | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_cross_vendor_conflict_detection -v` | ❌ W0 | ⬜ pending |
| **RFQ line item alignment** (NEW Fix-11) | 04-03 | 3 | COMPARE-04 | T-04-03-07 | vendor line_item_ids not matching RFQ → scope not_comparable with reason | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_rfq_line_item_alignment -v` | ❌ W0 | ⬜ pending |
| **clarification failure AttentionPoint** (NEW Fix-8) | 04-03 | 3 | COMPARE-03 | T-04-03-05 | clarification call failure → AttentionPoint(trigger_type="clarification_generation_failed"); result still emitted | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clarification_failure_surfaces_attention_point -v` | ❌ W0 | ⬜ pending |
| comparison traces committed (Fix-5) | 04-04 | 4 | COMPARE-02 / PROMPT-03 | T-04-04-05 | >=1 comparison_*.json with clamp_step.entries >= 1; fixture mode documented | file assertion | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_comparison_traces_committed -v` | ❌ W0 | ⬜ pending |
| prompt quality (human) | 04-04 | 4 | COMPARE-01..05 | T-04-04-01, T-04-04-02 | comparison.v1.md has model_proposed requirement, humility, no-normalization, 3 verdicts; human approves | manual | Human checkpoint in 04-04-PLAN.md | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/ai/tests/test_comparison_agent.py` — 20 named stubs (04-01)
- [ ] `services/ai/tests/conftest_comparison.py` — missing_extraction, present_extraction, partial_extraction builders (04-01)

*Existing pytest infrastructure (Phases 1–3) covers the framework; only comparison-specific test files are new.*

---

## New Stubs Added by Cross-AI Review (04-REVIEWS.md)

| Stub Name | Review Fix | Consensus Concern | Plan | Wave |
|-----------|-----------|-------------------|------|------|
| test_clamp_applied_to_result | Fix 1 (BLOCKER) | E2E clamp on emitted result | 04-03 | 3 |
| test_dimension_enum_fail_closed | Fix 1 (BLOCKER) | StrEnum dimension fail-closed | 04-03 | 3 |
| test_ceiling_empty_compliance | Fix 4 (HIGH) | Empty compliance ceiling = partially | 04-03 | 3 |
| test_ceiling_empty_risks | Fix 4 (HIGH) | Empty risk ceiling explicit | 04-03 | 3 |
| test_cross_vendor_conflict_detection | Fix 10 (MEDIUM) | Cross-vendor value comparison | 04-03 | 3 |
| test_rfq_line_item_alignment | Fix 11 (MEDIUM) | RFQ line item coverage | 04-03 | 3 |
| test_clarification_failure_surfaces_attention_point | Fix 8 (MEDIUM) | Clarification failure → AttentionPoint | 04-03 | 3 |

## Existing Stubs Sharpened by Cross-AI Review

| Stub Name | Review Fix | What Changed |
|-----------|-----------|--------------|
| test_attention_points_are_triggered | Fix 7 (MEDIUM) | Now asserts fabricated trigger_type is DROPPED from result |
| test_clarification_seeded_by_code | Fix 8 (MEDIUM) | Now asserts model extras are rejected (count + identity) |
| test_offer_table_code_built | Fix 6 (HIGH) | Renamed; now asserts _build_offer_table is code-built from ExtractionResult |
| test_comparison_sse_taxonomy | Fix 9 (MEDIUM) | Now asserts exactly ONE result event in sequence |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Comparison prompt quality: model_proposed requirement, humility, no-normalization, verdict precision, few-shot quality | COMPARE-01..05, 30% grade | Prompt design quality is a deliverable judgement | Open comparison.v1.md; confirm model_proposed section present and marked REQUIRED; confirm all 10 required sections; confirm >=3 specific few-shot examples |
| Comparison trace readability for an Aerchain reviewer | COMPARE-02 (clamp), COMPARE-05 | Trace narrative quality is a deliverable judgement | Open docs/traces/comparison_trace_1.md; confirm clamp diff table is populated; confirm Fixture Mode Note explains deterministic injection; confirm trace tells a coherent "code disproves the model" story |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 35s
- [x] `nyquist_compliant: true` set in frontmatter
- [x] All review fixes incorporated: stubs 14-20 added; stubs 5, 6, 7, 10 sharpened

**Approval:** ready for execution (pending review-mode replan)
