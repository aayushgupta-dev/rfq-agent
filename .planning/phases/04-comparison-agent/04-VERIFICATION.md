---
phase: 04-comparison-agent
verified: 2026-06-28T00:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Review comparison.v1.md and clarification.v1.md prompt quality against the rubric"
    expected: "comparison.v1.md has clear role framing, precise verdict definitions, model_proposed REQUIRED section, humility instruction, no-normalization prohibition, attention-points contract, field-to-dimension map, and >= 3 concrete few-shot examples. clarification.v1.md has strict-count instruction, REJECTED/ACCEPTED example pair, and ordering instruction."
    why_human: "Prompt quality assessment for the 30%-weighted rubric criterion requires a human reader to judge persuasiveness, precision, and Aerchain-reviewer readability — grep cannot score prose quality."
  - test: "Review comparison_trace_1.md for Aerchain-reviewer readability and rubric story"
    expected: "Section 3 (Verdict-Clamp Diff) shows a populated table of vendor/dimension/model_proposed/clamped-to rows that compellingly demonstrate code authority over the model. Section 6 (Fixture Mode Note) clearly explains the deterministic injection approach. The trace reads as evidence of a working system, not a constructed demo."
    why_human: "Trace readability and rubric persuasiveness are editorial judgments. The trace JSON mechanically passes (7 clamp entries, _fixture_mode: True, all required keys) but human approval was gated at Wave 4 checkpoint and the instructions ask for this to remain in human_needed."
  - test: "Confirm follow-up action from Wave 4 approval: capture a real-model comparison trace (comparison_trace_2) during Phase 4 E2E gate"
    expected: "A second trace file (comparison_trace_2.json + .md) captured from a live GPT-5.4 call appears under docs/traces/ to fully satisfy assignment §16 ('Model output') alongside the fixture trace."
    why_human: "Requires a live OpenAI API call to GPT-5.4 with real extraction inputs. Agreed at the Wave 4 human checkpoint; not yet actioned."
---

# Phase 04: Comparison Agent — Verification Report

**Phase Goal:** Vendors are compared honestly — comparability is established before any scoring, differences are surfaced without normalization, and gaps become clarification questions.
**Verified:** 2026-06-28
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Comparison consumes only code-validated ExtractionResult[] — never raw vendor text (grounding boundary holds transitively). | VERIFIED | `ExtractionResult` has no `raw_text` field (confirmed by field inspection). `_run_align_impl` asserts `isinstance(e, ExtractionResult)` for each input before proceeding. `comparison.py` imports `ExtractionResult` and `RFQ` from `schemas.domain` — `VendorResponse` (which carries `raw_text`) is never imported. |
| 2 | Non-comparable vendors are flagged as comparable\|partially\|not_comparable per dimension/line-item with reasons BEFORE any scoring; the agent never aggregates over a field a vendor is missing. | VERIFIED | `_compute_ceilings` runs before the model call in the comparability node. `_apply_verdict_clamp` pre-fills a full 6×N matrix with `not_comparable` defaults; clamping is fail-closed via `ComparisonDimension(StrEnum)` coercion. `_ceiling_for_flags([FlagStatus.missing, ...], dim) == "not_comparable"` confirmed by behavioral spot-check and 3 passing tests (`test_clamp_only_downgrades`, `test_no_aggregation_over_missing`, `test_clamp_applied_to_result`). |
| 3 | The buyer sees a qualitative comparability/readiness signal per dimension — not a numeric leaderboard or weighted score. | VERIFIED | `ComparisonResult` and `VendorReadiness` have no fields named `score`, `rank`, or `weight` (confirmed by schema inspection and `test_no_numeric_score`). `VendorReadiness.descriptor` is a prose string ("4 of 6 dimensions comparable; blocked on commercial, compliance"). No sort key on vendor list (D-07 guardrail). |
| 4 | Vendor offers are lightly aligned to the 8 RFQ line items with originals kept visible (differences surfaced, not normalized away). | VERIFIED | `_build_offer_table` builds `LineItemOffer` from `ExtractionResult.line_items` verbatim values; `pricing_verbatim` and `scope_verbatim` carry the raw extraction values or `None` for missing. `non_equivalence_flag` captures incompatibility descriptions ("bundled — not separable"). No `normalized_price`, `converted_price`, or `computed_price` fields. `_check_rfq_alignment` flags vendors whose line_item_ids don't cover the RFQ set. `test_offer_table_code_built` and `test_rfq_line_item_alignment` both pass. |
| 5 | Missing/unclear/conflicting information produces explicit buyer attention points and generated clarification questions. | VERIFIED | `_detect_attention_triggers` produces code-detected triggers (comparability_blocker, missing_pricing, cross_vendor_conflict, compliance_gap). `_collect_flagged_fields` seeds the clarification chain with flagged fields. Clarification failure surfaces an `AttentionPoint(trigger_type="clarification_generation_failed")` rather than a silent empty list. Behavioral spot-check confirmed 5 flagged fields and multiple attention triggers from `partial_extraction`. All 3 related tests pass (`test_attention_points_are_triggered`, `test_clarification_seeded_by_code`, `test_clarification_failure_surfaces_attention_point`). |

**Score:** 5/5 truths verified

### Deferred Items

None — all 5 success criteria verified in this phase.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `services/ai/agents/comparison.py` | 4-node LangGraph StateGraph; ComparisonDraft model target; fail-closed clamp; code-built surfaces | VERIFIED | 1052 lines. Exports `comparison_graph`, `run_comparison`, `generate_comparison_with_trace`. All 7 key functions present and behaviorally correct. `ComparisonState` TypedDict fixes the production `astream`/route graph-state bug (CR-01 from code review). |
| `services/ai/api/app.py` | POST /compare/vendors SSE route + ComparisonRequest with 2–5 vendor guard | VERIFIED | Route at line 209. `ComparisonRequest._check_vendor_count` enforces n >= 2 and n <= 5 (both CR-02 lower-bound fix and original upper-bound). Clarify node owns the terminal `done` event; route does NOT append one (CR-01 fix). |
| `services/ai/schemas/domain.py` | Full ComparisonResult + ComparisonDraft schema family (15 models + 2 StrEnums) | VERIFIED | All 15 models present: `ComparabilityVerdict`, `ComparisonDimension`, `ClampEntry`, `ClampReport`, `DimensionVerdictDraft`, `DimensionComparisonDraft`, `ComparisonDraft`, `DimensionVerdict`, `DimensionComparison`, `LineItemOffer`, `VendorReadiness`, `AttentionPoint`, `ClarificationQuestion`, `ClarificationSet`, `FlaggedField`, `ComparisonResult`. Draft/result split enforced at schema level. |
| `packages/shared-types/index.d.ts` | TS contract regenerated from ComparisonResult + ComparisonDraft | VERIFIED | Codegen ran; `test_codegen_drift.py` passes. `ComparabilityVerdict`, `ComparisonDimension` appear as TS string unions. No `Record<string, ...>` shapes. |
| `services/ai/tests/test_comparison_agent.py` | 22 tests all GREEN | VERIFIED | 22 passed (20 original stubs + 2 added by code-review for CR-01/CR-02). 0 failures. |
| `services/ai/tests/conftest_comparison.py` | ExtractionResult fixture builders | VERIFIED | `missing_extraction`, `present_extraction`, `partial_extraction` confirmed working by behavioral spot-checks and test runs. |
| `services/ai/prompts/comparison.v1.md` | Full prompt >= 120 lines with model_proposed requirement | VERIFIED (automated) | 193 lines, 8293 chars. Key sections present: role framing, 3 verdict definitions, field-to-dimension map, comparability-first instruction, "REQUIRED: model_proposed per verdict" section, humility instruction, no-normalization prohibition, attention points contract, output format, examples. Prompt quality requires human review — see Human Verification section. |
| `services/ai/prompts/clarification.v1.md` | Full prompt >= 60 lines with strict-count instruction | VERIFIED (automated) | 90 lines, 3744 chars. "MUST produce exactly as many ClarificationQuestion objects as there are flagged fields" at line 79. REJECTED/ACCEPTED example pair present. Prompt quality requires human review — see Human Verification section. |
| `services/ai/scripts/capture_comparison_trace.py` | Fixture-mode trace script; fails hard if has_downgrades == False | VERIFIED | 214 lines. `sys.exit(1)` on `has_downgrades == False`. Fixture draft proposes "comparable" for all vendors on all dimensions; real clamp runs against real ExtractionResults. |
| `docs/traces/comparison_trace_1.json` | Committed trace with clamp_step.entries >= 1 and _fixture_mode marker | VERIFIED | `_fixture_mode: True`. `clamp_step.entries`: 7 entries. All required keys present: `_fixture_mode`, `input`, `resolved_prompt`, `raw_model_output`, `clamp_step`, `clarification_step`, `final_result`. Sample entry shows `model_proposed: comparable` clamped to `clamped_to: not_comparable`. |
| `docs/traces/comparison_trace_1.md` | Markdown trace with verdict-clamp diff table and Fixture Mode Note | VERIFIED | File exists. Sections present per Wave 4 plan: Input, Resolved Prompt, Verdict-Clamp Diff table (7 rows), Clarification step, Final Result, Fixture Mode Note. Human readability assessment deferred to human checkpoint. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `comparison.py` | `schemas/domain.py` | `from schemas.domain import ComparisonResult, ComparisonDraft, ...` | WIRED | Imports 18 symbols from domain. `_comparison_chain` uses `.with_structured_output(ComparisonDraft, ...)` — NOT ComparisonResult. |
| `api/app.py` | `agents/comparison.py` | `from agents.comparison import comparison_graph` (line 37) | WIRED | Route uses `comparison_graph.astream(...)`. |
| `comparison.py` | `schemas/domain.py (ComparisonDimension StrEnum)` | `ComparisonDimension(dim_draft.dimension)` in `_apply_verdict_clamp` | WIRED | StrEnum coercion at line 274; `ValueError` caught and skipped (fail-closed). |
| `comparison.py` | `grounding/gate.py pattern` | `_collect_flagged_fields` mirrors `_walk_and_ground` | WIRED | Read-only recursive walker implemented inline (lines 427–477). Sorts blockers first. |
| `prompts/comparison.v1.md` | `agents/comparison.py` | `load("comparison")` at line 89 | WIRED | `_comparison_chain` built from loaded prompt. `model_proposed` field required by prompt text. |
| `docs/traces/comparison_trace_1.json` | `agents/comparison.py` | `capture_comparison_trace.py` calls `_apply_verdict_clamp` and `_compute_ceilings` directly | WIRED | Fixture draft feeds real clamp; 7 downgrade entries written. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `comparison.py` / clarify node | `final_result: ComparisonResult` | `_run_compare_impl` → `_apply_verdict_clamp` (code) → stored in `state["result"]` | Yes — clamped from real extraction statuses | FLOWING |
| `comparison.py` / `_build_offer_table` | `line_item_offers` | `ExtractionResult.line_items` verbatim values | Yes — reads extraction verbatim, never model-authored | FLOWING |
| `comparison.py` / `_collect_flagged_fields` | `flagged_fields` | Recursive walk of all `EnvelopeField` in `ExtractionResult` | Yes — produces real flagged fields from extraction statuses | FLOWING |
| `comparison.py` / `_clarification_chain` | `clar_parsed.questions` | Model call seeded by code-collected `flagged_fields` | Yes — count+identity validated; extras dropped; failure → AttentionPoint | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| clamp_verdict primitives | `clamp_verdict("comparable","not_comparable") == "not_comparable"` etc. | All 4 assertions pass | PASS |
| _ceiling_for_flags empty compliance | `_ceiling_for_flags([], compliance) == "partially"` | "partially" | PASS |
| _ceiling_for_flags empty risk | `_ceiling_for_flags([], risk) == "comparable"` | "comparable" | PASS |
| _ceiling_for_flags empty other | `_ceiling_for_flags([], technical) == "not_comparable"` | "not_comparable" | PASS |
| No raw_text in ExtractionResult | `"raw_text" in ExtractionResult.model_fields` | False | PASS |
| Draft/result split | `"clamp_report" not in ComparisonDraft.model_fields` | True | PASS |
| No numeric score fields | `forbidden & ComparisonResult.model_fields == empty` | True | PASS |
| RFQ alignment detection | `_check_rfq_alignment([missing-li vendor], rfq)` returns vendor name | "vendor-x" in mismatches | PASS |
| Flagged field collection | `_collect_flagged_fields([partial_extraction])` | 5 items, blockers first | PASS |
| Attention triggers | `_detect_attention_triggers([partial, present], ceilings)` | comparability_blocker, missing_pricing, cross_vendor_conflict | PASS |
| Full test suite | `uv run pytest -q` | 138 passed, 1 xfailed | PASS |
| Comparison test suite | `uv run pytest tests/test_comparison_agent.py -v` | 22 passed | PASS |
| Prompt quality assertions | `load("comparison"); assert "model_proposed" in body` etc. | All 6 assertions pass | PASS |
| Trace integrity | `clamp_step.entries >= 1, _fixture_mode == True` | 7 entries, True | PASS |

### Probe Execution

No `probe-*.sh` scripts declared or found for Phase 4. Step 7c: SKIPPED (no conventional probe files).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| COMPARE-01 | 04-01, 04-02, 04-03 | Comparison agent compares across 6 dimensions consuming only code-validated ExtractionResult[] | SATISFIED | `_run_align_impl` isinstance check; no VendorResponse import; ExtractionResult has no raw_text; `test_schema_shape` passes |
| COMPARE-02 | 04-01, 04-02, 04-03 | Comparability gate emits comparable\|partially\|not_comparable per dimension/line-item; never aggregates over missing | SATISFIED | `_compute_ceilings` runs before model; `_apply_verdict_clamp` is fail-closed 6×N; `test_clamp_applied_to_result`, `test_clamp_only_downgrades`, `test_no_aggregation_over_missing`, `test_ceiling_empty_compliance`, `test_ceiling_empty_risks`, `test_dimension_enum_fail_closed` all pass |
| COMPARE-03 | 04-01, 04-03 | Surfaces buyer attention points and generates clarification questions for missing/unclear/conflicting info | SATISFIED | `_detect_attention_triggers` (4 types), `_collect_flagged_fields` seeds clarification, failure → AttentionPoint; `test_attention_points_are_triggered`, `test_clarification_seeded_by_code`, `test_clarification_failure_surfaces_attention_point` pass |
| COMPARE-04 | 04-01, 04-03 | Light alignment to 8 RFQ line items; originals visible; no heavy normalization | SATISFIED | `_build_offer_table` uses verbatim values; `non_equivalence_flag` for incompatibilities; no normalized price fields; `_check_rfq_alignment` detects mismatches; `test_offer_table_code_built`, `test_rfq_line_item_alignment` pass |
| COMPARE-05 | 04-01, 04-02, 04-03 | Qualitative comparability/readiness signal per dimension, not numeric leaderboard | SATISFIED | No score/rank/weight fields in ComparisonResult or VendorReadiness; VendorReadiness.descriptor is prose; `test_no_numeric_score`, `test_vendor_order_preserved` pass |

All 5 COMPARE requirements: SATISFIED. No orphaned requirements — REQUIREMENTS.md maps COMPARE-01..05 exclusively to Phase 4 and marks all Complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `schemas/domain.py` | 136 | String literal `"TBD"` in comment (as a value example) | Info | Not a debt marker — appears in the comment: `conditional text ("TBD", "USD 110,000 – 135,000") that Decimal rejects`. It is an example of vendor input text, not an unresolved work item. |

No TBD/FIXME/XXX debt markers in implementation files. No placeholder patterns. No `return null` / `return []` stubs in production code paths (the `if not flag_statuses: return "not_comparable"` branch is correct logic, not a stub).

### Human Verification Required

#### 1. Comparison Prompt Quality (Rubric: 30%)

**Test:** Open `services/ai/prompts/comparison.v1.md`. Read the full prompt from the buyer's perspective and ask: "Would an Aerchain reviewer reading this understand exactly how the model should behave?"

**Expected:** Role framing is precise. The three verdict definitions (comparable / partially / not_comparable) have enum-exact language — especially not_comparable explicitly stating "DO NOT output comparable or partially when contributing fields are missing." The "REQUIRED: model_proposed per verdict" section is present and states the field is mandatory for the audit trail. The humility instruction explicitly prefers not_comparable over comparable on thin evidence. The no-normalization prohibition forbids currency conversion, bundle splitting, and unit price computation. The attention points section says "Do NOT invent additional trigger types." Three or more few-shot examples with specific, non-generic values are present. Overall: a procurement analyst who read only this prompt would produce the output the system expects.

**Why human:** Prompt persuasiveness and rubric fit are editorial judgments. Automated checks confirm key phrases are present (model_proposed, humility, normali, required — all pass) but cannot assess whether the prompt is compelling or complete to a human reviewer.

#### 2. Clarification Prompt Quality

**Test:** Open `services/ai/prompts/clarification.v1.md`. Confirm: strict-count instruction ("MUST produce exactly as many ClarificationQuestion objects as there are flagged fields"), REJECTED/ACCEPTED example pair is specific and illustrative, and the identity-match requirement (vendor_name + field_path + flag_status) is stated.

**Expected:** A model reading this prompt would understand it must produce exactly N questions for N flagged fields, match each question to its flagged field by identity, and reject generic questions like "please clarify pricing."

**Why human:** Same as above — editorial quality judgment on prompt design.

#### 3. Comparison Trace Readability (Aerchain reviewer perspective)

**Test:** Open `docs/traces/comparison_trace_1.md`. Read Section 3 (THE VERDICT-CLAMP DIFF) and Section 6 (Fixture Mode Note).

**Expected:** Section 3 has a populated 7-row table showing vendor / dimension / Model Proposed / Code Ceiling / Clamped To / Ceiling Reason. The table should be immediately legible as evidence that code, not the model, decides comparability. The "Model Proposed: comparable" → "Clamped To: not_comparable" contrast should be clear. Section 6 should explain the fixture-mode approach honestly so an Aerchain reviewer understands this is a deterministic demonstration, not fabricated evidence.

**Why human:** "Is this compelling to an Aerchain reviewer?" is a rubric judgment that automated checks cannot make. Wave 4 human checkpoint approved this (2026-06-28) but approval was gated before the verification step — it should be reconfirmed here.

#### 4. Real-Model Trace (Follow-up from Wave 4 approval)

**Test:** Capture a live GPT-5.4 comparison trace (`comparison_trace_2.json` + `.md`) using `services/ai/scripts/capture_comparison_trace.py` with `--live` mode (or by calling `generate_comparison_with_trace` with real extraction inputs and a real model key).

**Expected:** `docs/traces/comparison_trace_2.json` exists with a real `raw_model_output` from GPT-5.4, real clamp entries, and real clarification questions. This satisfies assignment §16's requirement for a trace showing "Model output" — the fixture trace demonstrates code authority but uses a synthetic model output.

**Why human:** Requires a live OpenAI API call. Agreed at Wave 4 checkpoint; the user must decide when and whether to action this before submission.

### Gaps Summary

No blocking gaps. All 5 roadmap success criteria are verified against the codebase with behavioral and test evidence. The 22 tests (20 planned + 2 added by code review) all pass. The full suite (138 tests) has 0 failures.

The `human_needed` status reflects three human items: (1) prompt quality assessment for the 30%-weighted rubric criterion, (2) trace readability confirmation for Aerchain submission, and (3) the agreed follow-up action of capturing a live-model trace. None of these block the codebase from being correct — they gate submission readiness and rubric scoring.

---

_Verified: 2026-06-28_
_Verifier: Claude (gsd-verifier)_
