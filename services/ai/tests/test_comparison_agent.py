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

from conftest_comparison import missing_extraction, partial_extraction, present_extraction
from openai import LengthFinishReasonError
from schemas.domain import ComparisonResult
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

    Wave 2 fleshes out ComparisonResult; Wave 3 makes this GREEN.
    """
    raise NotImplementedError("stub: COMPARE-01 — ComparisonResult schema shape")


# ---------------------------------------------------------------------------
# 2. No dict shapes (COMPARE-01 / PLAT-02)
# ---------------------------------------------------------------------------


def test_no_dict_shapes() -> None:
    """ComparisonResult sub-models use list[BaseModel], not dict[str, BaseModel].

    Mirrors P3 D-04 constraint — dict[str, Field] shapes break the grounding walker.
    """
    raise NotImplementedError("stub: COMPARE-01/PLAT-02 — no dict[str, BaseModel] shapes")


# ---------------------------------------------------------------------------
# 3. Clamp only downgrades (COMPARE-02)
# ---------------------------------------------------------------------------


def test_clamp_only_downgrades() -> None:
    """inject model verdict 'comparable' over missing field; assert clamped to 'not_comparable'.

    Tests primitive clamp_verdict + _ceiling_for_flags independently of the SSE pipeline.
    """
    raise NotImplementedError("stub: COMPARE-02 — clamp only downgrades (primitive)")


# ---------------------------------------------------------------------------
# 4. No aggregation over missing (COMPARE-02)
# ---------------------------------------------------------------------------


def test_no_aggregation_over_missing() -> None:
    """_ceiling_for_flags never produces 'comparable' when any flag is missing.

    The agent never aggregates over a field a vendor is missing (COMPARE-02, D-04).
    """
    raise NotImplementedError("stub: COMPARE-02 — no aggregation over missing (_ceiling_for_flags)")


# ---------------------------------------------------------------------------
# 5. Attention points are code-triggered (COMPARE-03 / Review Fix 7)
# ---------------------------------------------------------------------------


def test_attention_points_are_triggered() -> None:
    """Attention points are code-triggered only; model-invented points are DROPPED.

    Review Fix 7 tightened from 'trigger detected' to 'fabricated point dropped'.
    Code decides WHAT matters, model decides HOW to say it (D-08).
    """
    raise NotImplementedError("stub: COMPARE-03 / Fix-7 — model-fabricated attention point dropped")


# ---------------------------------------------------------------------------
# 6. Clarification seeded by code (COMPARE-03 / Review Fix 8)
# ---------------------------------------------------------------------------


def test_clarification_seeded_by_code() -> None:
    """Clarification count + identity matches _collect_flagged_fields; model extras are rejected.

    Review Fix 8: model cannot invent clarification questions beyond code-seeded flagged fields.
    """
    raise NotImplementedError("stub: COMPARE-03 / Fix-8 — clarification seeded by code, model extras rejected")


# ---------------------------------------------------------------------------
# 7. Offer table built from ExtractionResult verbatim (COMPARE-04 / Review Fix 6)
# ---------------------------------------------------------------------------


def test_offer_table_code_built() -> None:
    """line_item_offers built from ExtractionResult verbatim values + evidence paths; no model-authored values.

    Renamed from test_offer_table_verbatim per Review Fix 6.
    D-05: surface as-is, zero reconciliation; D-06: 8 × vendor offer table.
    """
    raise NotImplementedError("stub: COMPARE-04 / Fix-6 — offer table built from ExtractionResult verbatim")


# ---------------------------------------------------------------------------
# 8. Vendor order preserved (COMPARE-05)
# ---------------------------------------------------------------------------


def test_vendor_order_preserved() -> None:
    """vendor_readiness list preserves input order after JSON round-trip.

    D-07: vendors NEVER sorted or ordered by readiness — render order is always stable.
    """
    raise NotImplementedError("stub: COMPARE-05 — vendor order preserved after JSON round-trip")


# ---------------------------------------------------------------------------
# 9. No numeric score (COMPARE-05)
# ---------------------------------------------------------------------------


def test_no_numeric_score() -> None:
    """ComparisonResult has no field named score, rank, or weight.

    D-07 guardrail: no leaderboard, no numeric quality score (§24).
    """
    raise NotImplementedError("stub: COMPARE-05 — no score/rank/weight field in ComparisonResult")


# ---------------------------------------------------------------------------
# 10. SSE event taxonomy (SSE / Review Fix 9)
# ---------------------------------------------------------------------------


def test_comparison_sse_taxonomy() -> None:
    """All event types from /compare/vendors are in EVENT_TYPES; exactly one result event emitted.

    Review Fix 9 adds the sequence assertion (exactly one 'result' event).
    """
    raise NotImplementedError("stub: SSE / Fix-9 — comparison SSE taxonomy + exactly one result event")


# ---------------------------------------------------------------------------
# 11. Truncation → error event (EXTRACT-05 analog)
# ---------------------------------------------------------------------------


def test_truncation_error_event() -> None:
    """Truncation (LengthFinishReasonError) → safe error event with recoverable=True.

    Mirrors test_truncation_raises_error_event in test_extraction_agent.py.
    """
    raise NotImplementedError("stub: EXTRACT-05 analog — truncation → error event recoverable=True")


# ---------------------------------------------------------------------------
# 12. Refusal → error event (EXTRACT-05 analog)
# ---------------------------------------------------------------------------


def test_refusal_error_event() -> None:
    """Model refusal → safe error event with recoverable=False; no ComparisonResult parsed.

    Mirrors test_refusal_raises_error_event in test_extraction_agent.py.
    """
    raise NotImplementedError("stub: EXTRACT-05 analog — refusal → error event recoverable=False")


# ---------------------------------------------------------------------------
# 13. Comparison traces committed (PROMPT-03 / D-11 / Review Fix 5)
# ---------------------------------------------------------------------------


def test_comparison_traces_committed() -> None:
    """>=1 comparison_*.json under docs/traces/ with required keys including clamp_step >=1 entry.

    Review Fix 5: trace uses deterministic fixture draft (not a live run).
    D-11: JSON trace captures raw model verdicts → code-clamped verdicts (the downgrade diff).
    """
    raise NotImplementedError("stub: PROMPT-03 / D-11 / Fix-5 — comparison trace committed with clamp_step")


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
    raise NotImplementedError("stub: COMPARE-02 / Fix-1 — e2e clamp on emitted result")


# ---------------------------------------------------------------------------
# 15. Dimension enum fail-closed (COMPARE-02 / Review Fix 1)
# ---------------------------------------------------------------------------


def test_dimension_enum_fail_closed() -> None:
    """ComparisonDimension is a StrEnum. _apply_verdict_clamp with wrong-case or unknown dimension
    defaults to not_comparable (fail closed), not KeyError or bypass.

    E.g. dimension='Commercial' (capital C) or 'unknown_dim' → not_comparable.
    """
    raise NotImplementedError("stub: COMPARE-02 / Fix-1 — StrEnum dimension fail-closed")


# ---------------------------------------------------------------------------
# 16. Empty compliance ceiling (COMPARE-02 / Review Fix 4)
# ---------------------------------------------------------------------------


def test_ceiling_empty_compliance() -> None:
    """_ceiling_for_flags([]) for the compliance dimension returns at least 'partially'.

    Empty compliance list cannot be 'comparable' — RESEARCH A2 + Opus review.
    """
    raise NotImplementedError("stub: COMPARE-02 / Fix-4 — empty compliance ceiling")


# ---------------------------------------------------------------------------
# 17. Empty risks ceiling defined (COMPARE-02 / Review Fix 4)
# ---------------------------------------------------------------------------


def test_ceiling_empty_risks() -> None:
    """_ceiling_for_flags([]) for the risk dimension is explicitly handled (not fall-through to comparable).

    RESEARCH A2: empty risks = no hard ceiling but must be explicitly defined, not a gap.
    """
    raise NotImplementedError("stub: COMPARE-02 / Fix-4 — empty risk ceiling defined")


# ---------------------------------------------------------------------------
# 18. Cross-vendor conflict detection (COMPARE-03 / Review Fix 10)
# ---------------------------------------------------------------------------


def test_cross_vendor_conflict_detection() -> None:
    """Two extractions with DIFFERENT timeline values (both present, different).
    Assert _detect_cross_vendor_conflicts returns a trigger for timeline.

    Cross-VENDOR comparison of differing values, NOT per-field conflicting status.
    """
    raise NotImplementedError("stub: COMPARE-03 / Fix-10 — cross-vendor value conflict")


# ---------------------------------------------------------------------------
# 19. RFQ line item alignment (COMPARE-04 / Review Fix 11)
# ---------------------------------------------------------------------------


def test_rfq_line_item_alignment() -> None:
    """ExtractionResult whose line_items do NOT map to the RFQ's 8 canonical line_item_ids.
    Assert the agent flags scope as not_comparable with a reason naming the mismatch.
    """
    raise NotImplementedError("stub: COMPARE-04 / Fix-11 — vendor line item RFQ alignment")


# ---------------------------------------------------------------------------
# 20. Clarification failure surfaces attention point (COMPARE-03 / Review Fix 8)
# ---------------------------------------------------------------------------


def test_clarification_failure_surfaces_attention_point() -> None:
    """When the clarification chain call fails (mock raises), assert an AttentionPoint with
    trigger_type=='clarification_generation_failed' appears in the result (not silent empty list).

    Failure must not silently drop the clarification signal — absence is first-class (CLAUDE.md §8).
    """
    raise NotImplementedError("stub: COMPARE-03 / Fix-8 — clarification failure → AttentionPoint")
