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

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.1.1 (services/ai) |
| **Config file** | services/ai/pyproject.toml |
| **Quick run command** | `cd /Users/aayush/projects/aerchain/services/ai && uv run pytest -q tests/test_comparison_agent.py` |
| **Full suite command** | `cd /Users/aayush/projects/aerchain/services/ai && uv run pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest -q tests/test_comparison_agent.py`
- **After every plan wave:** Run `cd services/ai && uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| conftest_comparison | 04-01 | 1 | COMPARE-01 | T-04-01-01 | ExtractionResult builders validate via pydantic | unit | `cd services/ai && uv run python -c "from conftest_comparison import missing_extraction; print('OK')"` | ❌ W0 | ⬜ pending |
| test stubs | 04-01 | 1 | COMPARE-01..05 | — | All 13 stubs discovered, all raise NotImplementedError | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py --collect-only -q` | ❌ W0 | ⬜ pending |
| schema shape | 04-02 | 2 | COMPARE-01 | T-04-02-01 | ComparabilityVerdict in domain.py not envelope.py; no dict shapes | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_schema_shape tests/test_comparison_agent.py::test_no_dict_shapes -v` | ❌ W0 | ⬜ pending |
| codegen drift | 04-02 | 2 | PLAT-02 | T-04-02-02 | pydantic2ts regenerates TS without Record<string,...> shapes | integration | `cd services/ai && uv run pytest tests/test_codegen_drift.py -x` | ✅ (exists) | ⬜ pending |
| clamp only downgrades | 04-03 | 3 | COMPARE-02 | T-04-03-01 | clamp_verdict("comparable","not_comparable")=="not_comparable"; code cannot upgrade | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clamp_only_downgrades -v` | ❌ W0 | ⬜ pending |
| no aggregation over missing | 04-03 | 3 | COMPARE-02 | T-04-03-01 | any missing field on a dimension caps ceiling regardless of other present fields | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_no_aggregation_over_missing -v` | ❌ W0 | ⬜ pending |
| attention triggers | 04-03 | 3 | COMPARE-03 | T-04-03-04 | trigger list from code only; no fabricated triggers | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_attention_points_are_triggered -v` | ❌ W0 | ⬜ pending |
| clarification seeded by code | 04-03 | 3 | COMPARE-03 | T-04-03-02 | flagged fields from _collect_flagged_fields; model receives code-supplied list only | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_clarification_seeded_by_code -v` | ❌ W0 | ⬜ pending |
| offer table verbatim | 04-03 | 3 | COMPARE-04 | T-04-03-04 | LineItemOffer has verbatim fields; no normalized/computed fields | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_offer_table_verbatim -v` | ❌ W0 | ⬜ pending |
| vendor order preserved | 04-03 | 3 | COMPARE-05 | T-04-03-01 | vendor_readiness list preserves input order after JSON round-trip | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_vendor_order_preserved -v` | ❌ W0 | ⬜ pending |
| no numeric score | 04-03 | 3 | COMPARE-05 | T-04-03-01 | no score/rank/weight field on ComparisonResult or VendorReadiness | unit (schema) | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_no_numeric_score -v` | ❌ W0 | ⬜ pending |
| SSE taxonomy | 04-03 | 3 | PLAT-04 | T-04-03-05 | all /compare/vendors event types in EVENT_TYPES | integration | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_comparison_sse_taxonomy -v` | ❌ W0 | ⬜ pending |
| truncation error | 04-03 | 3 | EXTRACT-05 analog | T-04-03-05 | truncation → safe error event; recoverable=True | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_truncation_error_event -v` | ❌ W0 | ⬜ pending |
| refusal error | 04-03 | 3 | EXTRACT-05 analog | T-04-03-05 | refusal → safe error event; recoverable=False | unit | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_refusal_error_event -v` | ❌ W0 | ⬜ pending |
| comparison traces committed | 04-04 | 4 | COMPARE-02 / PROMPT-03 | T-04-04-04 | >=1 comparison_*.json with clamp_step.entries >= 1 | file assertion | `cd services/ai && uv run pytest tests/test_comparison_agent.py::test_comparison_traces_committed -v` | ❌ W0 | ⬜ pending |
| prompt quality (human) | 04-04 | 4 | COMPARE-01..05 | T-04-04-01 | comparison.v1.md has humility, no-normalization, 3 verdicts; human approves | manual | Human checkpoint in 04-04-PLAN.md | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/ai/tests/test_comparison_agent.py` — 13 named stubs (04-01)
- [ ] `services/ai/tests/conftest_comparison.py` — missing_extraction, present_extraction, partial_extraction builders (04-01)

*Existing pytest infrastructure (Phases 1–3) covers the framework; only comparison-specific test files are new.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Comparison prompt quality: humility framing, no-normalization instruction, verdict precision, few-shot quality | COMPARE-01..05, 30% grade | Prompt design quality is a deliverable judgement, not a code assertion | Open comparison.v1.md; confirm all 9 required sections; confirm >=3 specific few-shot examples |
| Comparison trace readability for an Aerchain reviewer | COMPARE-02 (clamp), COMPARE-05 | Trace narrative quality is a deliverable judgement | Open docs/traces/comparison_trace_1.md; confirm clamp diff table is populated; confirm trace tells a coherent "code disproves the model" story |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready for execution
