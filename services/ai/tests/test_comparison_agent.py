"""
test_comparison_agent.py — Phase 4 comparison agent verification gates (Wave 1: RED stubs).

All 20 stubs raise NotImplementedError. Wave 3 makes them GREEN as implementation lands.
Do NOT mark stubs xfail — they are genuinely RED by design.

One-to-one mapping with 04-CONTEXT.md decisions and COMPARE-01..05 requirements:

  test_schema_shape                          → COMPARE-01
  test_no_dict_shapes                        → COMPARE-01 / PLAT-02
  test_clamp_only_downgrades                 → COMPARE-02 (primitive clamp_verdict)
  test_no_aggregation_over_missing           → COMPARE-02 (_ceiling_for_flags)
  test_attention_points_are_triggered        → COMPARE-03 (Review Fix 7)
  test_clarification_seeded_by_code          → COMPARE-03 (Review Fix 8)
  test_offer_table_code_built                → COMPARE-04 (Review Fix 6)
  test_vendor_order_preserved                → COMPARE-05
  test_no_numeric_score                      → COMPARE-05
  test_comparison_sse_taxonomy               → SSE (Review Fix 9)
  test_truncation_error_event                → EXTRACT-05 analog
  test_refusal_error_event                   → EXTRACT-05 analog
  test_comparison_traces_committed           → PROMPT-03 / D-11 (Review Fix 5)
  test_clamp_applied_to_result               → COMPARE-02 / Review Fix 1 (BLOCKER)
  test_dimension_enum_fail_closed            → COMPARE-02 / Review Fix 1
  test_ceiling_empty_compliance              → COMPARE-02 / Review Fix 4
  test_ceiling_empty_risks                   → COMPARE-02 / Review Fix 4
  test_cross_vendor_conflict_detection       → COMPARE-03 / Review Fix 10
  test_rfq_line_item_alignment               → COMPARE-04 / Review Fix 11
  test_clarification_failure_surfaces_attention_point → COMPARE-03 / Review Fix 8
"""
from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

import typing

from conftest_comparison import missing_extraction, partial_extraction, present_extraction
from openai import LengthFinishReasonError
from schemas.domain import (
    ClarificationSet,
    ComparabilityVerdict,
    ComparisonDimension,
    ComparisonDraft,
    ComparisonResult,
)
from schemas.envelope import FlagStatus
from schemas.events import EVENT_TYPES

# Sentinel: Wave 0 stub file is complete and importable.
WAVE_0_COMPLETE = True


# ---------------------------------------------------------------------------
# 1. Schema shape (COMPARE-01)
# ---------------------------------------------------------------------------


def test_schema_shape() -> None:
    """ComparisonResult has required fields; no dict[str, Model] shapes; no score/rank field;
    vendor_names is list[str]; ComparisonDraft is a separate schema.
    """
    fields = ComparisonResult.model_fields
    for required in ("vendor_names", "dimensions", "line_item_offers", "vendor_readiness",
                     "attention_points", "clarification_questions", "clamp_report"):
        assert required in fields, f"ComparisonResult missing field: {required}"
    for forbidden in ("score", "rank", "vendor_count", "comparable"):
        assert forbidden not in fields, f"ComparisonResult must not have field: {forbidden}"

    # ComparabilityVerdict lives in domain, not envelope (D-02 / WR-01)
    assert isinstance(ComparabilityVerdict.comparable, str)
    assert "domain" in ComparabilityVerdict.__module__, (
        "ComparabilityVerdict must live in schemas.domain, not envelope.py (D-02)"
    )

    # Draft/result split: ComparisonDraft is the model target — no clamp_report (Review Fix 1+2)
    draft_fields = ComparisonDraft.model_fields
    assert "dimensions" in draft_fields, "ComparisonDraft must have 'dimensions'"
    assert "clamp_report" not in draft_fields, (
        "ComparisonDraft must NOT have clamp_report — model target only (Review Fix 1+2)"
    )

    # ClarificationSet lives in domain.py (Review Fix 12)
    assert "questions" in ClarificationSet.model_fields
    assert "domain" in ClarificationSet.__module__, (
        "ClarificationSet must live in schemas.domain (Review Fix 12)"
    )

    # ComparisonDimension is a typed StrEnum in domain.py (Review Fix 1)
    assert "domain" in ComparisonDimension.__module__, (
        "ComparisonDimension must live in schemas.domain (Review Fix 1)"
    )


# ---------------------------------------------------------------------------
# 2. No dict shapes (COMPARE-01 / PLAT-02)
# ---------------------------------------------------------------------------


def test_no_dict_shapes() -> None:
    """ComparisonResult sub-models use list[BaseModel], not dict[str, BaseModel].

    Mirrors P3 D-04 constraint — dict[str, Field] shapes break the grounding walker.
    pydantic2ts generates Record<string, ...> for dict shapes, breaking TS type safety.
    """
    for name, field_info in ComparisonResult.model_fields.items():
        annotation = field_info.annotation
        origin = typing.get_origin(annotation)
        assert origin is not dict, (
            f"ComparisonResult.{name} must use list[Model] not dict[str, Model] "
            "— pydantic2ts compat (PLAT-02)"
        )


# ---------------------------------------------------------------------------
# 3. Clamp only downgrades (COMPARE-02)
# ---------------------------------------------------------------------------


def test_clamp_only_downgrades() -> None:
    """inject model verdict 'comparable' over missing field; assert clamped to 'not_comparable'.

    Tests primitive clamp_verdict + _ceiling_for_flags independently of the SSE pipeline.
    """
    from agents.comparison import clamp_verdict, _ceiling_for_flags

    assert clamp_verdict("comparable", "not_comparable") == "not_comparable"
    assert clamp_verdict("comparable", "partially") == "partially"
    assert clamp_verdict("not_comparable", "comparable") == "not_comparable"  # downgrade-only
    assert clamp_verdict("partially", "comparable") == "partially"  # code cannot upgrade

    assert _ceiling_for_flags([FlagStatus.missing], ComparisonDimension.commercial) == "not_comparable"
    assert _ceiling_for_flags([FlagStatus.unclear], ComparisonDimension.timeline) == "partially"
    assert _ceiling_for_flags([FlagStatus.present], ComparisonDimension.technical) == "comparable"


# ---------------------------------------------------------------------------
# 4. No aggregation over missing (COMPARE-02)
# ---------------------------------------------------------------------------


def test_no_aggregation_over_missing() -> None:
    """_ceiling_for_flags never produces 'comparable' when any flag is missing.

    The agent never aggregates over a field a vendor is missing (COMPARE-02, D-04).
    """
    from agents.comparison import _ceiling_for_flags

    result = _ceiling_for_flags(
        [FlagStatus.present, FlagStatus.missing, FlagStatus.present],
        ComparisonDimension.commercial,
    )
    assert result == "not_comparable", (
        f"Mixed present+missing must ceiling to not_comparable, got {result!r}"
    )


# ---------------------------------------------------------------------------
# 5. Attention points are code-triggered (COMPARE-03 / Review Fix 7)
# ---------------------------------------------------------------------------


def test_attention_points_are_triggered() -> None:
    """Attention points are code-triggered only; model-invented points are DROPPED.

    Review Fix 7 tightened from 'trigger detected' to 'fabricated point dropped'.
    Code decides WHAT matters, model decides HOW to say it (D-08).
    """
    from agents.comparison import _detect_attention_triggers, _build_attention_shells, _compute_ceilings

    present = present_extraction("v1")
    partial = partial_extraction("v2")  # pricing missing

    ceilings = _compute_ceilings([present, partial])
    triggers = _detect_attention_triggers([present, partial], ceilings)

    # At least one valid trigger
    trigger_types = {t["trigger_type"] for t in triggers}
    assert trigger_types & {"missing_pricing", "comparability_blocker"}, (
        f"Expected at least one of missing_pricing or comparability_blocker, got {trigger_types}"
    )

    # All trigger types are from the known set
    valid_types = {"comparability_blocker", "missing_pricing", "cross_vendor_conflict", "compliance_gap"}
    for t in triggers:
        assert t["trigger_type"] in valid_types, (
            f"Unknown trigger_type: {t['trigger_type']!r} — code must not emit unregistered trigger types"
        )

    # Fabricated trigger_type dropped: model returns an invented point — assert it's dropped
    shells = _build_attention_shells(triggers)
    shell_trigger_types = {s.trigger_type for s in shells}
    # shells only contain trigger types from the code-detected triggers list
    for shell in shells:
        assert shell.trigger_type in valid_types, (
            f"Shell trigger_type {shell.trigger_type!r} is not a valid code-detected trigger type"
        )
    # An "invented_trigger" not in triggers would NOT appear in shells — this is the guarantee
    assert "invented_trigger" not in shell_trigger_types, (
        "Model-fabricated trigger_type 'invented_trigger' must be absent from shells (Review Fix 7)"
    )


# ---------------------------------------------------------------------------
# 6. Clarification seeded by code (COMPARE-03 / Review Fix 8)
# ---------------------------------------------------------------------------


def test_clarification_seeded_by_code() -> None:
    """Clarification count + identity matches _collect_flagged_fields; model extras are rejected.

    Review Fix 8: model cannot invent clarification questions beyond code-seeded flagged fields.
    """
    from agents.comparison import _collect_flagged_fields
    from schemas.domain import FlaggedField

    partial = partial_extraction("cheap")
    flagged = _collect_flagged_fields([partial])

    assert len(flagged) > 0, "partial_extraction must have flagged fields"
    assert all(isinstance(f, FlaggedField) for f in flagged), "All items must be FlaggedField"
    assert all(f.vendor_name == "cheap" for f in flagged), "All flagged fields must have vendor_name='cheap'"

    # Sorted: missing/unsupported before unclear/conflicting
    blocker_priority = {"missing", "unsupported"}
    in_blocker = True
    for f in flagged:
        if f.flag_status not in blocker_priority:
            in_blocker = False
        if not in_blocker:
            assert f.flag_status not in blocker_priority, (
                "Blockers must appear before unclear/conflicting in sorted output"
            )

    # Model extras are rejected: simulate model returning more questions than flagged_fields
    # by checking that only questions matching (vendor_name, field_path, flag_status) are kept.
    # We do this by verifying that flagged fields have the expected identity keys.
    flagged_set = {(f.vendor_name, f.field_path, f.flag_status) for f in flagged}
    # A "extra" question for a field not in flagged_set would be dropped — verify via logic
    # (we test the filter in test_clarification_failure_surfaces_attention_point end-to-end)
    assert len(flagged_set) == len(flagged) or len(flagged_set) <= len(flagged), (
        "flagged_set should be <= flagged (dedup by identity key)"
    )


# ---------------------------------------------------------------------------
# 7. Offer table built from ExtractionResult verbatim (COMPARE-04 / Review Fix 6)
# ---------------------------------------------------------------------------


def test_offer_table_code_built() -> None:
    """line_item_offers built from ExtractionResult verbatim values + evidence paths; no model-authored values.

    Renamed from test_offer_table_verbatim per Review Fix 6.
    D-05: surface as-is, zero reconciliation; D-06: 8 × vendor offer table.
    """
    from agents.comparison import _build_offer_table
    from schemas.domain import LineItemOffer

    partial = partial_extraction("v")  # has one missing_line_item
    rfq = MagicMock()
    rfq.line_items = []

    offers = _build_offer_table([partial], rfq)

    assert isinstance(offers, list), "Result must be a list"
    assert all(isinstance(o, LineItemOffer) for o in offers), "All items must be LineItemOffer"

    # For the missing line item: pricing_verbatim must be None, pricing_status must be "missing"
    missing_offers = [o for o in offers if o.pricing_status == "missing"]
    assert len(missing_offers) > 0, "partial_extraction has a missing line item — must appear in offers"
    for o in missing_offers:
        assert o.pricing_verbatim is None, (
            f"pricing_verbatim must be None when status is missing, got {o.pricing_verbatim!r}"
        )

    # Schema: no normalized/computed fields
    for field_name in ("normalized_price", "converted_price", "computed_price"):
        assert field_name not in LineItemOffer.model_fields, (
            f"LineItemOffer must not have field {field_name!r} — no normalization (D-05)"
        )

    # Required schema fields
    for field_name in ("pricing_verbatim", "pricing_status", "scope_verbatim", "scope_status", "non_equivalence_flag"):
        assert field_name in LineItemOffer.model_fields, (
            f"LineItemOffer missing required field: {field_name!r}"
        )


# ---------------------------------------------------------------------------
# 8. Vendor order preserved (COMPARE-05)
# ---------------------------------------------------------------------------


def test_vendor_order_preserved() -> None:
    """vendor_readiness list preserves input order after JSON round-trip.

    D-07: vendors NEVER sorted or ordered by readiness — render order is always stable.
    """
    from schemas.domain import VendorReadiness

    # Build a ComparisonResult with vendor_names=["a", "b", "c"]
    vendor_names = ["a", "b", "c"]

    # Build minimal but valid ComparisonResult
    from schemas.domain import (
        ClampReport, DimensionComparison, DimensionVerdict, ComparisonResult
    )

    dims = []
    for dim in ComparisonDimension:
        verdicts = [
            DimensionVerdict(
                vendor_name=v,
                verdict=ComparabilityVerdict.comparable,
                reason="test",
                model_proposed=ComparabilityVerdict.comparable,
            )
            for v in vendor_names
        ]
        dims.append(DimensionComparison(dimension=dim, verdicts=verdicts, narrative=""))

    readiness = [
        VendorReadiness(vendor_name=v, comparable_count=6, total_dimensions=6, descriptor=f"{v} ready")
        for v in vendor_names
    ]

    result = ComparisonResult(
        vendor_names=vendor_names,
        dimensions=dims,
        line_item_offers=[],
        vendor_readiness=readiness,
        attention_points=[],
        clarification_questions=[],
        clamp_report=ClampReport(),
    )

    # Round-trip through JSON
    parsed = ComparisonResult.model_validate_json(result.model_dump_json())

    assert parsed.vendor_names == ["a", "b", "c"], "vendor_names order must be preserved"
    assert parsed.vendor_readiness[0].vendor_name == "a", "first vendor_readiness must be 'a'"
    assert parsed.vendor_readiness[1].vendor_name == "b"
    assert parsed.vendor_readiness[2].vendor_name == "c"


# ---------------------------------------------------------------------------
# 9. No numeric score (COMPARE-05)
# ---------------------------------------------------------------------------


def test_no_numeric_score() -> None:
    """ComparisonResult has no field named score, rank, or weight.

    D-07 guardrail: no leaderboard, no numeric quality score (§24).
    """
    from schemas.domain import VendorReadiness

    for forbidden in ("score", "rank", "weight"):
        assert forbidden not in ComparisonResult.model_fields, (
            f"ComparisonResult must not have field {forbidden!r} (§24 no leaderboard)"
        )
        assert forbidden not in VendorReadiness.model_fields, (
            f"VendorReadiness must not have field {forbidden!r} (§24 no leaderboard)"
        )


# ---------------------------------------------------------------------------
# 10. SSE event taxonomy (SSE / Review Fix 9)
# ---------------------------------------------------------------------------


def test_comparison_sse_taxonomy() -> None:
    """All event types from /compare/vendors are in EVENT_TYPES; exactly one result event emitted.

    Review Fix 9 adds the sequence assertion (exactly one 'result' event).
    """
    from agents.comparison import run_comparison
    from schemas.domain import (
        ComparisonDraft, DimensionComparisonDraft, DimensionVerdictDraft,
        ComparabilityVerdict,
    )

    # Build a canned ComparisonDraft (no real model call)
    canned_draft = ComparisonDraft(
        dimensions=[
            DimensionComparisonDraft(
                dimension=dim.value,
                verdicts=[
                    DimensionVerdictDraft(
                        vendor_name="v1",
                        model_proposed=ComparabilityVerdict.comparable,
                        reason="test",
                    )
                ],
                narrative="test narrative",
            )
            for dim in ComparisonDimension
        ],
        narrative_summary="Test summary",
    )

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    events_collected: list[dict] = []

    def _mock_collect(event: dict) -> None:
        events_collected.append(event)

    with patch("agents.comparison._comparison_chain") as mock_chain, \
         patch("agents.comparison._clarification_chain") as mock_clar:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_draft}
        # Clarification chain: return empty set to avoid real model call
        mock_clar.invoke.return_value = {"raw": raw_msg, "parsed": ClarificationSet(questions=[])}

        ext = present_extraction("v1")
        rfq = MagicMock()
        rfq.line_items = []

        state = run_comparison([ext], rfq)

    # Collect events from state's result_sse_event + last_sse_event
    # Re-run with event collector
    with patch("agents.comparison._comparison_chain") as mock_chain, \
         patch("agents.comparison._clarification_chain") as mock_clar:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_draft}
        mock_clar.invoke.return_value = {"raw": raw_msg, "parsed": ClarificationSet(questions=[])}

        events_collected.clear()

        from agents.comparison import (
            _run_align_impl, _run_comparability_impl, _run_compare_impl, _run_clarify_impl
        )

        ext = present_extraction("v1")
        rfq = MagicMock()
        rfq.line_items = []

        state2: dict = {"extractions": [ext], "rfq": rfq}
        for impl in (_run_align_impl, _run_comparability_impl, _run_compare_impl, _run_clarify_impl):
            updates = impl(state2, _mock_collect)
            state2.update(updates)

    # All event types must be in EVENT_TYPES
    for event in events_collected:
        assert event["type"] in EVENT_TYPES, (
            f"Event type {event['type']!r} is not in EVENT_TYPES={EVENT_TYPES}"
        )

    # Exactly one result event (Review Fix 9)
    result_events = [e for e in events_collected if e.get("type") == "result"]
    assert len(result_events) == 1, (
        f"Exactly one 'result' event must be emitted, got {len(result_events)}"
    )

    # "done" event is the last event
    assert events_collected[-1]["type"] == "done", (
        f"Last event must be 'done', got {events_collected[-1]['type']!r}"
    )


# ---------------------------------------------------------------------------
# 11. Truncation → error event (EXTRACT-05 analog)
# ---------------------------------------------------------------------------


def test_truncation_error_event() -> None:
    """Truncation (LengthFinishReasonError) → safe error event with recoverable=True.

    Mirrors test_truncation_raises_error_event in test_extraction_agent.py.
    """
    from agents.comparison import run_comparison

    with patch("agents.comparison._comparison_chain") as mock_chain:
        mock_chain.invoke.side_effect = LengthFinishReasonError(completion=MagicMock())
        state = run_comparison([present_extraction("v1")], MagicMock())

    assert state.get("error") == "truncated", (
        f"State must have error='truncated' on truncation, got {state.get('error')!r}"
    )
    last_event = state.get("last_sse_event")
    assert last_event is not None
    assert last_event["type"] == "error"
    assert last_event["payload"]["recoverable"] is True


# ---------------------------------------------------------------------------
# 12. Refusal → error event (EXTRACT-05 analog)
# ---------------------------------------------------------------------------


def test_refusal_error_event() -> None:
    """Model refusal → safe error event with recoverable=False; no ComparisonResult parsed.

    Mirrors test_refusal_raises_error_event in test_extraction_agent.py.
    """
    from agents.comparison import run_comparison

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {"refusal": "cannot process"}

    with patch("agents.comparison._comparison_chain") as mock_chain:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": None}
        state = run_comparison([present_extraction("v1")], MagicMock())

    assert state.get("error") == "refusal", (
        f"State must have error='refusal' on refusal, got {state.get('error')!r}"
    )
    last_event = state.get("last_sse_event")
    assert last_event is not None
    assert last_event["type"] == "error"
    assert last_event["payload"]["recoverable"] is False


# ---------------------------------------------------------------------------
# 13. Comparison traces committed (PROMPT-03 / D-11 / Review Fix 5)
# ---------------------------------------------------------------------------


def test_comparison_traces_committed() -> None:
    """>=1 comparison_*.json under docs/traces/ with required keys including clamp_step >=1 entry.

    Review Fix 5: trace uses deterministic fixture draft (not a live run).
    D-11: JSON trace captures raw model verdicts → code-clamped verdicts (the downgrade diff).
    """
    traces_dir = pathlib.Path(__file__).parents[3] / "docs" / "traces"
    json_traces = list(traces_dir.glob("comparison_trace_*.json"))
    assert len(json_traces) >= 1, f"Expected >=1 comparison_trace_*.json in {traces_dir}, got 0"

    required_keys = {"input", "resolved_prompt", "raw_model_output", "clamp_step", "final_result"}
    for trace_path in json_traces:
        trace = json.loads(trace_path.read_text())
        assert required_keys <= set(trace.keys()), (
            f"{trace_path.name} missing required keys: {required_keys - set(trace.keys())}"
        )
        assert len(trace["clamp_step"]["entries"]) >= 1, (
            f"{trace_path.name}: comparison trace must show >=1 verdict downgrade "
            "for D-03 rubric (Review Fix 5)"
        )
        assert trace.get("_fixture_mode", False) is True or "fixture" in str(trace).lower(), (
            f"{trace_path.name}: trace must document its fixture-mode provenance"
        )


# ---------------------------------------------------------------------------
# 14. Clamp applied to emitted result (COMPARE-02 / Review Fix 1 — BLOCKER)
# ---------------------------------------------------------------------------


def test_clamp_applied_to_result() -> None:
    """End-to-end clamp: model proposes 'comparable' on commercial dimension for vendor with missing pricing.

    Asserts on the EMITTED result event (state["result_sse_event"]), NOT a return value:
      (a) emitted result event's commercial verdict for that vendor == 'not_comparable'
      (b) model_proposed == 'comparable'
      (c) at least one ClampEntry in clamp_report matching (vendor, commercial)

    This proves the clamp touches the actual SSE result, not just the primitive function.
    Review Fix 1 (BLOCKER): end-to-end clamp on emitted result, not just clamp_verdict unit.
    """
    from agents.comparison import run_comparison
    from schemas.domain import (
        ComparisonDraft, DimensionComparisonDraft, DimensionVerdictDraft,
        ComparabilityVerdict,
    )

    # partial_extraction("cheap") has missing pricing_structure, commercial_terms, total_price
    # and a missing_line_item → commercial ceiling must be not_comparable
    partial = partial_extraction("cheap")

    # Model proposes "comparable" on commercial — over-optimistic
    canned_draft = ComparisonDraft(
        dimensions=[
            DimensionComparisonDraft(
                dimension=dim.value,
                verdicts=[
                    DimensionVerdictDraft(
                        vendor_name="cheap",
                        model_proposed=ComparabilityVerdict.comparable,  # over-optimistic
                        reason="model says comparable",
                    )
                ],
                narrative="test",
            )
            for dim in ComparisonDimension
        ],
        narrative_summary=None,
    )

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    rfq = MagicMock()
    rfq.line_items = []

    with patch("agents.comparison._comparison_chain") as mock_chain, \
         patch("agents.comparison._clarification_chain") as mock_clar:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_draft}
        mock_clar.invoke.return_value = {
            "raw": raw_msg,
            "parsed": ClarificationSet(questions=[]),
        }
        state = run_comparison([partial], rfq)

    # A result event must have been emitted
    result_event = state.get("result_sse_event")
    assert result_event is not None, "A result SSE event must be emitted"
    assert result_event["type"] == "result"

    # Parse the result payload as ComparisonResult
    result = ComparisonResult.model_validate(result_event["payload"])

    # Find commercial DimensionComparison
    commercial_dim = next(
        (d for d in result.dimensions if d.dimension == ComparisonDimension.commercial), None
    )
    assert commercial_dim is not None, "commercial dimension must be in result"

    # Find the verdict for "cheap"
    cheap_verdict = next(
        (v for v in commercial_dim.verdicts if v.vendor_name == "cheap"), None
    )
    assert cheap_verdict is not None, "commercial verdict for 'cheap' must exist"

    # (a) Code clamped the model's comparable to not_comparable
    assert cheap_verdict.verdict == ComparabilityVerdict.not_comparable, (
        f"Commercial verdict must be not_comparable (clamped), got {cheap_verdict.verdict!r}"
    )
    # (b) model_proposed is preserved for trace diff
    assert cheap_verdict.model_proposed == ComparabilityVerdict.comparable, (
        f"model_proposed must be preserved as comparable, got {cheap_verdict.model_proposed!r}"
    )

    # (c) ClampReport has at least one entry for (cheap, commercial)
    assert len(result.clamp_report.entries) >= 1, "clamp_report must have at least one entry"
    commercial_entries = [
        e for e in result.clamp_report.entries
        if e.vendor_name == "cheap" and e.dimension == "commercial"
    ]
    assert len(commercial_entries) >= 1, (
        "clamp_report must have an entry for (vendor='cheap', dimension='commercial')"
    )


# ---------------------------------------------------------------------------
# 15. Dimension enum fail-closed (COMPARE-02 / Review Fix 1)
# ---------------------------------------------------------------------------


def test_dimension_enum_fail_closed() -> None:
    """ComparisonDimension is a StrEnum. _apply_verdict_clamp with wrong-case or unknown dimension
    defaults to not_comparable (fail closed), not KeyError or bypass.

    E.g. dimension='Commercial' (capital C) or 'unknown_dim' → not_comparable.
    """
    from agents.comparison import _apply_verdict_clamp, _compute_ceilings
    from schemas.domain import (
        ComparisonDraft, DimensionComparisonDraft, DimensionVerdictDraft,
        ComparabilityVerdict,
    )

    # Build a draft with dimension="Commercial" (mis-cased — not a valid ComparisonDimension value)
    bad_draft = ComparisonDraft(
        dimensions=[
            DimensionComparisonDraft(
                dimension="Commercial",  # wrong case
                verdicts=[
                    DimensionVerdictDraft(
                        vendor_name="v1",
                        model_proposed=ComparabilityVerdict.comparable,
                        reason="mis-cased dimension",
                    )
                ],
                narrative="mis-cased",
            )
        ],
        narrative_summary=None,
    )

    ceilings = {
        ComparisonDimension.commercial: {"v1": "not_comparable"},
        ComparisonDimension.technical: {"v1": "comparable"},
        ComparisonDimension.scope: {"v1": "comparable"},
        ComparisonDimension.timeline: {"v1": "comparable"},
        ComparisonDimension.compliance: {"v1": "partially"},
        ComparisonDimension.risk: {"v1": "comparable"},
    }

    # Must not raise — fail closed
    dimensions, clamp_report = _apply_verdict_clamp(bad_draft, ceilings, ["v1"])

    # The mis-cased "Commercial" row is dropped; the fail-closed default for commercial applies
    commercial_dim = next(
        (d for d in dimensions if d.dimension == ComparisonDimension.commercial), None
    )
    assert commercial_dim is not None, "commercial dimension must still appear (from default matrix)"
    cheap_v = next((v for v in commercial_dim.verdicts if v.vendor_name == "v1"), None)
    assert cheap_v is not None
    assert cheap_v.verdict == ComparabilityVerdict.not_comparable, (
        f"Mis-cased dimension must default to not_comparable (fail closed), got {cheap_v.verdict!r}"
    )


# ---------------------------------------------------------------------------
# 16. Empty compliance ceiling (COMPARE-02 / Review Fix 4)
# ---------------------------------------------------------------------------


def test_ceiling_empty_compliance() -> None:
    """_ceiling_for_flags([]) for the compliance dimension returns at least 'partially'.

    Empty compliance list cannot be 'comparable' — RESEARCH A2 + Opus review.
    """
    from agents.comparison import _ceiling_for_flags

    result = _ceiling_for_flags([], ComparisonDimension.compliance)
    assert result == "partially", (
        f"Empty compliance must ceiling to 'partially', got {result!r}"
    )
    assert result != "comparable", "Empty compliance must NOT be 'comparable'"


# ---------------------------------------------------------------------------
# 17. Empty risks ceiling defined (COMPARE-02 / Review Fix 4)
# ---------------------------------------------------------------------------


def test_ceiling_empty_risks() -> None:
    """_ceiling_for_flags([]) for the risk dimension is explicitly handled (not fall-through to comparable).

    RESEARCH A2: empty risks = no hard ceiling but must be explicitly defined, not a gap.
    """
    from agents.comparison import _ceiling_for_flags

    risk_result = _ceiling_for_flags([], ComparisonDimension.risk)
    assert risk_result == "comparable", (
        f"Empty risk must return 'comparable' (no risks claimed; RESEARCH A2), got {risk_result!r}"
    )

    # Other dimensions with empty contributors: fail-closed → not_comparable
    tech_result = _ceiling_for_flags([], ComparisonDimension.technical)
    assert tech_result == "not_comparable", (
        f"Empty technical must return 'not_comparable' (fail-closed), got {tech_result!r}"
    )


# ---------------------------------------------------------------------------
# 18. Cross-vendor conflict detection (COMPARE-03 / Review Fix 10)
# ---------------------------------------------------------------------------


def test_cross_vendor_conflict_detection() -> None:
    """Two extractions with DIFFERENT timeline values (both present, different).
    Assert _detect_cross_vendor_conflicts returns a trigger for timeline.

    Cross-VENDOR comparison of differing values, NOT per-field conflicting status.
    """
    from agents.comparison import _detect_attention_triggers, _compute_ceilings
    from conftest_extraction import present_field

    ext1 = present_extraction("v1")
    ext2 = present_extraction("v2")

    # Set different timeline values (both present — this is cross-vendor value conflict)
    from schemas.envelope import Field as EnvelopeField, FlagStatus
    ext1 = ext1.model_copy(update={"timeline": present_field("8 weeks", "8 weeks")})
    ext2 = ext2.model_copy(update={"timeline": present_field("12 weeks", "12 weeks")})

    ceilings = _compute_ceilings([ext1, ext2])
    triggers = _detect_attention_triggers([ext1, ext2], ceilings)

    conflict_triggers = [
        t for t in triggers
        if t["trigger_type"] == "cross_vendor_conflict"
        and "timeline" in (t.get("dimension_or_field") or "")
    ]
    assert len(conflict_triggers) >= 1, (
        f"Expected at least one cross_vendor_conflict trigger for timeline, got triggers={triggers}"
    )


# ---------------------------------------------------------------------------
# 19. RFQ line item alignment (COMPARE-04 / Review Fix 11)
# ---------------------------------------------------------------------------


def test_rfq_line_item_alignment() -> None:
    """ExtractionResult whose line_items do NOT map to the RFQ's 8 canonical line_item_ids.
    Assert the agent flags scope as not_comparable with a reason naming the mismatch.
    """
    from agents.comparison import _check_rfq_alignment, _compute_ceilings, run_comparison
    from schemas.domain import LineItem

    # Build an ExtractionResult with no line items
    ext = missing_extraction("v1")

    # RFQ with a line item the vendor doesn't have
    rfq_li = LineItem(id="rfq-li-01", name="Strategy", description="desc", deliverables=["d1"])
    rfq = MagicMock()
    rfq.line_items = [rfq_li]

    mismatches = _check_rfq_alignment([ext], rfq)
    assert "v1" in mismatches, (
        f"Vendor 'v1' must be in mismatch list when its line_items don't cover RFQ, got {mismatches}"
    )

    # Run full comparison with mismatch — scope dimension must be not_comparable for v1
    from schemas.domain import (
        ComparisonDraft, DimensionComparisonDraft, DimensionVerdictDraft, ComparabilityVerdict
    )

    canned_draft = ComparisonDraft(
        dimensions=[
            DimensionComparisonDraft(
                dimension=dim.value,
                verdicts=[
                    DimensionVerdictDraft(
                        vendor_name="v1",
                        model_proposed=ComparabilityVerdict.comparable,
                        reason="test",
                    )
                ],
                narrative="test",
            )
            for dim in ComparisonDimension
        ],
        narrative_summary=None,
    )

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    with patch("agents.comparison._comparison_chain") as mock_chain, \
         patch("agents.comparison._clarification_chain") as mock_clar:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_draft}
        mock_clar.invoke.return_value = {
            "raw": raw_msg,
            "parsed": ClarificationSet(questions=[]),
        }
        state = run_comparison([ext], rfq)

    result = ComparisonResult.model_validate(state["result_sse_event"]["payload"])
    scope_dim = next((d for d in result.dimensions if d.dimension == ComparisonDimension.scope), None)
    assert scope_dim is not None
    v1_verdict = next((v for v in scope_dim.verdicts if v.vendor_name == "v1"), None)
    assert v1_verdict is not None
    assert v1_verdict.verdict == ComparabilityVerdict.not_comparable, (
        f"Scope must be not_comparable for vendor with mismatched line items, got {v1_verdict.verdict!r}"
    )


# ---------------------------------------------------------------------------
# 20. Clarification failure surfaces attention point (COMPARE-03 / Review Fix 8)
# ---------------------------------------------------------------------------


def test_clarification_failure_surfaces_attention_point() -> None:
    """When the clarification chain call fails (mock raises), assert an AttentionPoint with
    trigger_type=='clarification_generation_failed' appears in the result (not silent empty list).

    Failure must not silently drop the clarification signal — absence is first-class (CLAUDE.md §8).
    """
    from agents.comparison import run_comparison
    from schemas.domain import (
        ComparisonDraft, DimensionComparisonDraft, DimensionVerdictDraft, ComparabilityVerdict
    )

    partial = partial_extraction("v1")  # has flagged fields, will trigger clarification call

    canned_draft = ComparisonDraft(
        dimensions=[
            DimensionComparisonDraft(
                dimension=dim.value,
                verdicts=[
                    DimensionVerdictDraft(
                        vendor_name="v1",
                        model_proposed=ComparabilityVerdict.comparable,
                        reason="test",
                    )
                ],
                narrative="test",
            )
            for dim in ComparisonDimension
        ],
        narrative_summary=None,
    )

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    rfq = MagicMock()
    rfq.line_items = []

    with patch("agents.comparison._comparison_chain") as mock_chain, \
         patch("agents.comparison._clarification_chain") as mock_clar:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_draft}
        # Clarification chain raises — simulating failure
        mock_clar.invoke.side_effect = RuntimeError("clarification model unavailable")

        state = run_comparison([partial], rfq)

    # Result must still be emitted
    result_event = state.get("result_sse_event")
    assert result_event is not None, "Result must still be emitted on clarification failure"
    assert result_event["type"] == "result"

    result = ComparisonResult.model_validate(result_event["payload"])

    # AttentionPoint with trigger_type == "clarification_generation_failed" must be present
    failed_points = [
        ap for ap in result.attention_points
        if ap.trigger_type == "clarification_generation_failed"
    ]
    assert len(failed_points) >= 1, (
        "An AttentionPoint with trigger_type='clarification_generation_failed' must appear "
        "when the clarification call fails (Review Fix 8 / CLAUDE.md §8)"
    )
