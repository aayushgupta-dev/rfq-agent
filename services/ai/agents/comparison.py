"""
comparison.py — Comparison agent: LangGraph StateGraph (Phase 4, Plan 04-03).

4-node graph: align → comparability → compare → clarify.

The model emits ComparisonDraft (proposed verdicts + phrasing only). Code constructs
ComparisonResult — the offer table, vendor_readiness, attention_point shells,
clarification validation, and clamp_report are ALL code-built. (CLAUDE.md §2 / D-03 /
Review Fix 1+2)

Comparability ceiling rule (D-04 / Review Fix 4):
  missing|unsupported on any contributing field → not_comparable
  unclear|conflicting on any contributing field → at most partially
  empty compliance list → at most partially (cannot be verified as compliant)
  empty risk list → comparable (no risks claimed; per RESEARCH A2)
  other empty contributor → not_comparable (fail-closed)
  all present → comparable allowed

_apply_verdict_clamp is fail-closed (Review Fix 1):
  - Builds full 6×N matrix defaulting to not_comparable
  - Unknown dimension strings (e.g. 'Commercial') caught via ComparisonDimension(StrEnum)
    and silently skipped — the default not_comparable applies
  - Unknown vendor names from model output are dropped

Exactly ONE result SSE event is emitted by the clarify node (Review Fix 9). The compare
node stores the pre-clarification result in state but does NOT emit it.

Grounding boundary: the agent never reads raw vendor text — only ExtractionResult[].
The align node asserts isinstance(e, ExtractionResult) for each input (COMPARE-01).

_MAX_VENDORS = 5
# ponytail: prototype limit — 5 vendors keeps the single-call context window manageable.
# Increase if multi-vendor truncation is observed (RESEARCH Pitfall 7 / Review Fix LOW).

Exported:
  comparison_graph                  — compiled LangGraph StateGraph
  run_comparison                    — sync testable wrapper (test/script use only)
  generate_comparison_with_trace    — sync trace capture surface (D-11)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypedDict

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from openai import LengthFinishReasonError
from pydantic import BaseModel as _BaseModel

from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import (
    RFQ,
    AttentionPoint,
    ClampEntry,
    ClampReport,
    ClarificationQuestion,
    ClarificationSet,
    ComparabilityVerdict,
    ComparisonDimension,
    ComparisonDraft,
    ComparisonResult,
    DimensionComparison,
    DimensionVerdict,
    ExtractionResult,
    FlaggedField,
    LineItemOffer,
    VendorReadiness,
)
from schemas.envelope import Field as EnvelopeField
from schemas.envelope import FlagStatus
from schemas.events import EVENT_TYPES, ErrorPayload

logger = logging.getLogger(__name__)

_MAX_VENDORS = 5
# ponytail: prototype limit — 5 vendors keeps the single-call context window manageable.
# Increase if multi-vendor truncation is observed (RESEARCH Pitfall 7 / Review Fix LOW).

# ---------------------------------------------------------------------------
# Module-level chains (patched in tests)
# ---------------------------------------------------------------------------

_comp_post = load("comparison")
_comp_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=_comp_post.content),
        ("human", "{input}"),
    ]
)
# CRITICAL: with_structured_output(ComparisonDraft, ...) — NOT ComparisonResult.
# The model proposes verdicts + phrasing only; code constructs ComparisonResult. (Review Fix 1+2)
_comparison_chain = (
    _comp_prompt
    | get_llm("reasoning").with_structured_output(
        ComparisonDraft, method="json_schema", include_raw=True
    )
)

_clar_post = load("clarification")
_clar_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=_clar_post.content),
        ("human", "{flagged_fields}"),
    ]
)
_clarification_chain = (
    _clar_prompt
    | get_llm("cheap").with_structured_output(
        ClarificationSet, method="json_schema", include_raw=True
    )
)

# ---------------------------------------------------------------------------
# Verdict clamp utilities
# ---------------------------------------------------------------------------

_VERDICT_ORDER: dict[str, int] = {
    "comparable": 2,
    "partially": 1,
    "not_comparable": 0,
}


def _ceiling_for_flags(
    flag_statuses: list[FlagStatus],
    dimension: ComparisonDimension,
) -> str:
    """Compute the comparability ceiling for a vendor on one dimension.

    Implements D-04 ceiling rule WITH explicit per-dimension empty-case handling
    (Review Fix 4). Returns one of 'comparable', 'partially', 'not_comparable'.
    """
    if any(s in (FlagStatus.missing, FlagStatus.unsupported) for s in flag_statuses):
        return "not_comparable"
    if any(s in (FlagStatus.unclear, FlagStatus.conflicting) for s in flag_statuses):
        return "partially"
    if not flag_statuses:
        if dimension == ComparisonDimension.compliance:
            # ponytail: empty compliance list cannot be verified as compliant — Review Fix 4
            return "partially"
        if dimension == ComparisonDimension.risk:
            # ponytail: no risks claimed — per RESEARCH A2 empty risk is not auto-blocking; Review Fix 4
            return "comparable"
        # fail-closed: unknown empty dimension — Review Fix 4
        return "not_comparable"
    return "comparable"


def clamp_verdict(model_verdict: str, code_ceiling: str) -> str:
    """Return the lower of model_verdict and code_ceiling by _VERDICT_ORDER.

    Downgrade-only: code cannot upgrade the model's verdict, only downgrade.

    Fail-closed: an unknown model_verdict string (not one of the three valid
    verdicts) yields the code_ceiling rather than the raw string — code is the
    guard, and a verbatim unknown string would later raise in ComparabilityVerdict.
    """
    if model_verdict not in _VERDICT_ORDER:
        return code_ceiling
    mv = _VERDICT_ORDER[model_verdict]
    cc = _VERDICT_ORDER.get(code_ceiling, 0)
    if mv <= cc:
        return model_verdict
    return code_ceiling


# Field → dimension contribution map (from 04-RESEARCH.md / 04-CONTEXT.md D-04)
_DIM_FIELDS: dict[ComparisonDimension, list[str]] = {
    ComparisonDimension.technical: ["scope_summary"],
    ComparisonDimension.commercial: ["pricing_structure", "total_price", "commercial_terms"],
    ComparisonDimension.scope: [],      # derived from line_items per-item below
    ComparisonDimension.timeline: ["timeline"],
    ComparisonDimension.compliance: [],  # derived from compliance_points list below
    ComparisonDimension.risk: [],        # derived from risks list below
}


def _collect_field_statuses_for_dim(
    extraction: ExtractionResult,
    dimension: ComparisonDimension,
) -> list[FlagStatus]:
    """Collect FlagStatus values for the fields contributing to a dimension."""
    statuses: list[FlagStatus] = []

    # Scalar fields
    for field_name in _DIM_FIELDS.get(dimension, []):
        val = getattr(extraction, field_name, None)
        if isinstance(val, EnvelopeField):
            statuses.append(val.status)

    # Special per-dimension list/nested handling
    if dimension == ComparisonDimension.technical:
        for li in extraction.line_items:
            if isinstance(li.scope_coverage, EnvelopeField):
                statuses.append(li.scope_coverage.status)

    elif dimension == ComparisonDimension.scope:
        for li in extraction.line_items:
            if isinstance(li.scope_coverage, EnvelopeField):
                statuses.append(li.scope_coverage.status)

    elif dimension == ComparisonDimension.commercial:
        for li in extraction.line_items:
            if isinstance(li.pricing, EnvelopeField):
                statuses.append(li.pricing.status)

    elif dimension == ComparisonDimension.compliance:
        # compliance_points is list[Field[str]] — each item's status counts
        for cp in extraction.compliance_points:
            if isinstance(cp, EnvelopeField):
                statuses.append(cp.status)
        # ponytail: empty list → no statuses → _ceiling_for_flags handles with explicit compliance branch

    elif dimension == ComparisonDimension.risk:
        for r in extraction.risks:
            if isinstance(r, EnvelopeField):
                statuses.append(r.status)
        # ponytail: empty list → no statuses → _ceiling_for_flags handles with explicit risk branch

    return statuses


def _compute_ceilings(
    extractions: list[ExtractionResult],
) -> dict[ComparisonDimension, dict[str, str]]:
    """Compute {ComparisonDimension: {vendor_name: ceiling_str}} for all 6 dimensions.

    Key type is ComparisonDimension (typed StrEnum) — downstream fail-closed
    key lookup uses this typed key. (Review Fix 1)
    """
    ceilings: dict[ComparisonDimension, dict[str, str]] = {}
    for dim in ComparisonDimension:
        ceilings[dim] = {}
        for ext in extractions:
            statuses = _collect_field_statuses_for_dim(ext, dim)
            ceilings[dim][ext.vendor_name] = _ceiling_for_flags(statuses, dim)
    return ceilings


def _apply_verdict_clamp(
    draft: ComparisonDraft,
    ceilings: dict[ComparisonDimension, dict[str, str]],
    vendor_names: list[str],
) -> tuple[list[DimensionComparison], ClampReport]:
    """Fail-closed clamp: build full 6×N matrix, validate and fill all pairs. (Review Fix 1)

    1. Initialise the full matrix with default "not_comparable" for all (dim, vendor) pairs.
    2. For each DimensionComparisonDraft in draft.dimensions:
       a. Try ComparisonDimension(dim_draft.dimension) — ValueError → skip (fail closed).
       b. For each DimensionVerdictDraft in dim_draft.verdicts:
          - Unknown vendor → skip.
          - Clamp model_proposed against code_ceiling.
          - Record ClampEntry if downgraded.
    3. Build list[DimensionComparison] from the complete matrix.
    """
    # (dim, vendor) → (verdict, model_proposed, reason, ceiling)
    matrix: dict[tuple[ComparisonDimension, str], tuple[str, str, str, str]] = {}
    # Fill defaults
    for dim in ComparisonDimension:
        for vname in vendor_names:
            ceiling = ceilings.get(dim, {}).get(vname, "not_comparable")
            matrix[(dim, vname)] = ("not_comparable", "not_comparable", "dimension not provided by model", ceiling)

    clamp_entries: list[ClampEntry] = []

    for dim_draft in draft.dimensions:
        try:
            dim_enum = ComparisonDimension(dim_draft.dimension)
        except ValueError:
            # Unknown dimension string from model → skip; default not_comparable applies (fail closed)
            logger.warning("Unknown dimension from model: %r — skipped (fail closed)", dim_draft.dimension)
            continue

        dim_ceilings = ceilings.get(dim_enum, {})
        for vd in dim_draft.verdicts:
            if vd.vendor_name not in vendor_names:
                # Unknown vendor from model → skip (fail closed)
                logger.warning("Unknown vendor from model: %r — skipped", vd.vendor_name)
                continue
            code_ceiling = dim_ceilings.get(vd.vendor_name, "not_comparable")
            model_str = vd.model_proposed.value if isinstance(vd.model_proposed, ComparabilityVerdict) else str(vd.model_proposed)
            clamped = clamp_verdict(model_str, code_ceiling)
            if clamped != model_str:
                clamp_entries.append(
                    ClampEntry(
                        vendor_name=vd.vendor_name,
                        dimension=dim_enum.value,
                        model_proposed=model_str,
                        code_ceiling=code_ceiling,
                        clamped_to=clamped,
                        ceiling_reason=f"{dim_enum.value} ceiling={code_ceiling} for {vd.vendor_name}",
                    )
                )
            matrix[(dim_enum, vd.vendor_name)] = (clamped, model_str, vd.reason, code_ceiling)

    # Build DimensionComparison list from matrix (all 6 dims × all N vendors)
    # Narratives from model draft for matched dims; fallback empty string
    draft_narratives: dict[str, str] = {}
    for dd in draft.dimensions:
        try:
            de = ComparisonDimension(dd.dimension)
            draft_narratives[de.value] = dd.narrative
        except ValueError:
            pass

    dim_comparisons: list[DimensionComparison] = []
    for dim in ComparisonDimension:
        verdicts: list[DimensionVerdict] = []
        for vname in vendor_names:
            verdict_str, model_proposed_str, reason, _ceiling = matrix[(dim, vname)]
            verdicts.append(
                DimensionVerdict(
                    vendor_name=vname,
                    verdict=ComparabilityVerdict(verdict_str),
                    reason=reason,
                    model_proposed=ComparabilityVerdict(model_proposed_str),
                )
            )
        dim_comparisons.append(
            DimensionComparison(
                dimension=dim,
                verdicts=verdicts,
                narrative=draft_narratives.get(dim.value, ""),
            )
        )

    return dim_comparisons, ClampReport(entries=clamp_entries)


# ---------------------------------------------------------------------------
# Code construction helpers (Review Fix 2+6+7)
# ---------------------------------------------------------------------------


def _build_offer_table(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> list[LineItemOffer]:
    """Build the offer table CODE-SIDE from ExtractionResult verbatim values (Review Fix 6 / D-05).

    # ponytail: offer table is built here from ExtractionResult, never from model output.
    # Model cannot author verbatim values — they come from the extraction directly. (Review Fix 6)
    """
    offers: list[LineItemOffer] = []
    for ext in extractions:
        for li in ext.line_items:
            pricing_val = li.pricing.value if li.pricing.status == FlagStatus.present else None
            scope_val = li.scope_coverage.value if li.scope_coverage.status == FlagStatus.present else None
            offers.append(
                LineItemOffer(
                    line_item_id=li.line_item_id,
                    line_item_name=li.line_item_name,
                    vendor_name=ext.vendor_name,
                    pricing_verbatim=pricing_val,
                    pricing_status=li.pricing.status.value,
                    scope_verbatim=scope_val,
                    scope_status=li.scope_coverage.status.value,
                    non_equivalence_flag=None,
                )
            )
    return offers


def _build_vendor_readiness(
    vendor_names: list[str],
    dimensions: list[DimensionComparison],
) -> list[VendorReadiness]:
    """Build vendor readiness in INPUT ORDER (never sorted). (D-07)

    # ponytail: list order follows vendor_names input order. No sort key. (D-07)
    """
    readiness: list[VendorReadiness] = []
    for vname in vendor_names:
        comparable_count = 0
        blocked_dims: list[str] = []
        for dc in dimensions:
            for dv in dc.verdicts:
                if dv.vendor_name == vname:
                    if dv.verdict == ComparabilityVerdict.comparable:
                        comparable_count += 1
                    else:
                        blocked_dims.append(dc.dimension.value)
        total = 6
        if blocked_dims:
            descriptor = f"{comparable_count} of {total} dimensions comparable; blocked on {', '.join(blocked_dims)}"
        else:
            descriptor = f"{comparable_count} of {total} dimensions comparable"
        readiness.append(
            VendorReadiness(
                vendor_name=vname,
                comparable_count=comparable_count,
                total_dimensions=total,
                descriptor=descriptor,
            )
        )
    return readiness


def _build_attention_shells(triggers: list[dict]) -> list[AttentionPoint]:
    """Build one AttentionPoint shell per code-detected trigger.

    Model fills only the summary field in the compare node.
    Model-invented points (not in trigger list) are dropped. (Review Fix 7)
    """
    return [
        AttentionPoint(
            trigger_type=t["trigger_type"],
            summary="",  # filled by model in compare node
            vendors_affected=t.get("vendors_affected", []),
            dimension_or_field=t.get("dimension_or_field"),
        )
        for t in triggers
    ]


# ---------------------------------------------------------------------------
# Flag collector
# ---------------------------------------------------------------------------


def _collect_flagged_fields(
    extractions: list[ExtractionResult],
) -> list[FlaggedField]:
    """Read-only variant of gate.py's _walk_and_ground. (Review Fix 8 / D-09)

    Recursively walks all BaseModel fields in each ExtractionResult.
    When isinstance(value, EnvelopeField) and value.status != FlagStatus.present,
    appends a FlaggedField.

    Sorted: comparability-blockers (missing|unsupported) first, then unclear|conflicting.
    """
    results: list[FlaggedField] = []

    def _walk(obj: Any, path: str, vendor_name: str) -> None:
        for field_name in type(obj).model_fields:
            value = getattr(obj, field_name)
            field_path = f"{path}.{field_name}" if path else field_name

            if isinstance(value, EnvelopeField):
                if value.status != FlagStatus.present:
                    results.append(
                        FlaggedField(
                            vendor_name=vendor_name,
                            field_path=field_path,
                            flag_status=value.status.value,
                        )
                    )
            elif isinstance(value, _BaseModel):
                _walk(value, field_path, vendor_name)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    item_path = f"{field_path}[{i}]"
                    if isinstance(item, EnvelopeField):
                        if item.status != FlagStatus.present:
                            results.append(
                                FlaggedField(
                                    vendor_name=vendor_name,
                                    field_path=item_path,
                                    flag_status=item.status.value,
                                )
                            )
                    elif isinstance(item, _BaseModel):
                        _walk(item, item_path, vendor_name)

    for ext in extractions:
        _walk(ext, "", ext.vendor_name)

    # Sort: missing/unsupported (blockers) first, then unclear/conflicting
    _priority = {"missing": 0, "unsupported": 1, "unclear": 2, "conflicting": 3}
    results.sort(key=lambda f: _priority.get(f.flag_status, 99))
    return results


# ---------------------------------------------------------------------------
# Attention trigger detection
# ---------------------------------------------------------------------------


def _detect_attention_triggers(
    extractions: list[ExtractionResult],
    ceilings: dict[ComparisonDimension, dict[str, str]],
) -> list[dict]:
    """Detect code-side attention triggers. (D-08 / Review Fix 7+10)

    Returns list of {trigger_type, dimension_or_field, vendors_affected} dicts.
    Trigger types:
      comparability_blocker: any dim ceiling == not_comparable for any vendor
      missing_pricing: any vendor with missing/unsupported pricing
      cross_vendor_conflict: same field has DIFFERENT present values across vendors (Review Fix 10)
      compliance_gap: all vendors have empty or missing compliance_points
    """
    triggers: list[dict] = []
    vendor_names = [ext.vendor_name for ext in extractions]

    # a. comparability_blocker
    for dim, vendor_ceilings in ceilings.items():
        blocked_vendors = [v for v, c in vendor_ceilings.items() if c == "not_comparable"]
        if blocked_vendors:
            triggers.append(
                {
                    "trigger_type": "comparability_blocker",
                    "dimension_or_field": dim.value,
                    "vendors_affected": blocked_vendors,
                }
            )

    # b. missing_pricing
    pricing_missing_vendors: list[str] = []
    for ext in extractions:
        has_missing = False
        if ext.pricing_structure.status in (FlagStatus.missing, FlagStatus.unsupported):
            has_missing = True
        for li in ext.line_items:
            if li.pricing.status in (FlagStatus.missing, FlagStatus.unsupported):
                has_missing = True
        if has_missing:
            pricing_missing_vendors.append(ext.vendor_name)
    if pricing_missing_vendors:
        triggers.append(
            {
                "trigger_type": "missing_pricing",
                "dimension_or_field": "pricing_structure / line_items[*].pricing",
                "vendors_affected": pricing_missing_vendors,
            }
        )

    # c. cross_vendor_conflict (Review Fix 10)
    # For timeline and commercial_terms: collect present values across vendors.
    # Different present values = cross-vendor conflict (NOT per-field conflicting status).
    # ponytail: Review Fix 10 — conflicting status is per-vendor; cross-vendor conflict is different values
    for field_name in ("timeline", "commercial_terms"):
        present_values: dict[str, str] = {}  # vendor_name → value
        for ext in extractions:
            fld = getattr(ext, field_name, None)
            if isinstance(fld, EnvelopeField) and fld.status == FlagStatus.present and fld.value is not None:
                present_values[ext.vendor_name] = str(fld.value)
        if len(set(present_values.values())) > 1:
            triggers.append(
                {
                    "trigger_type": "cross_vendor_conflict",
                    "dimension_or_field": field_name,
                    "vendors_affected": list(present_values.keys()),
                }
            )

    # d. compliance_gap: all vendors have empty or missing compliance_points
    all_have_gap = all(
        len(ext.compliance_points) == 0
        or all(
            cp.status
            in (
                FlagStatus.missing,
                FlagStatus.unclear,
                FlagStatus.unsupported,
                FlagStatus.conflicting,
            )
            for cp in ext.compliance_points
            if isinstance(cp, EnvelopeField)
        )
        for ext in extractions
    )
    if all_have_gap and extractions:
        triggers.append(
            {
                "trigger_type": "compliance_gap",
                "dimension_or_field": "compliance_points",
                "vendors_affected": vendor_names,
            }
        )

    return triggers


# ---------------------------------------------------------------------------
# RFQ line item alignment check (Review Fix 11)
# ---------------------------------------------------------------------------


def _check_rfq_alignment(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> list[str]:
    """Return vendor names whose line_items do not cover all RFQ line_item_ids. (Review Fix 11)"""
    rfq_ids = {li.id for li in rfq.line_items}
    mismatches: list[str] = []
    for ext in extractions:
        vendor_ids = {li.line_item_id for li in ext.line_items}
        if not rfq_ids.issubset(vendor_ids):
            mismatches.append(ext.vendor_name)
    return mismatches


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _run_align_impl(state: dict[str, Any], emit: Callable[[dict], None]) -> dict[str, Any]:
    """Node 1: validate all inputs are ExtractionResult instances. (COMPARE-01)"""
    assert {"status", "result", "error"} <= set(EVENT_TYPES)

    emit({"type": "status", "payload": {"message": "validating inputs", "phase": "align"}})

    extractions = state.get("extractions", [])
    for i, e in enumerate(extractions):
        if not isinstance(e, ExtractionResult):
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="comparison_invalid_input",
                        message=f"extractions[{i}] is not an ExtractionResult (got {type(e).__name__})",
                        recoverable=False,
                    ).model_dump(),
                }
            )
            return {"error": "invalid_input"}

    return {}


def _run_comparability_impl(state: dict[str, Any], emit: Callable[[dict], None]) -> dict[str, Any]:
    """Node 2: compute ceilings, RFQ alignment, attention triggers."""
    emit(
        {
            "type": "status",
            "payload": {"message": "computing comparability ceilings", "phase": "comparability"},
        }
    )

    extractions: list[ExtractionResult] = state["extractions"]
    rfq: RFQ = state["rfq"]

    ceilings = _compute_ceilings(extractions)
    scope_alignment_issues = _check_rfq_alignment(extractions, rfq)
    if scope_alignment_issues:
        # Tighten scope ceiling to not_comparable for mismatched vendors
        for vname in scope_alignment_issues:
            if ComparisonDimension.scope in ceilings:
                ceilings[ComparisonDimension.scope][vname] = "not_comparable"

    triggers = _detect_attention_triggers(extractions, ceilings)

    # Add a comparability_blocker trigger for mismatched vendors if not already present
    if scope_alignment_issues:
        existing_blocker_dims = {
            t["dimension_or_field"] for t in triggers if t["trigger_type"] == "comparability_blocker"
        }
        if "scope" not in existing_blocker_dims:
            triggers.append(
                {
                    "trigger_type": "comparability_blocker",
                    "dimension_or_field": "scope",
                    "vendors_affected": scope_alignment_issues,
                }
            )

    return {
        "ceilings": ceilings,
        "scope_alignment_issues": scope_alignment_issues,
        "triggers": triggers,
    }


def _run_compare_impl(state: dict[str, Any], emit: Callable[[dict], None]) -> dict[str, Any]:
    """Node 3: call model with ComparisonDraft target, build ComparisonResult (pre-clarify).

    Stores result in state — does NOT emit result event here (Review Fix 9).
    The clarify node emits the single final result event.
    """
    if state.get("error"):
        return {}

    assert {"status", "result", "error"} <= set(EVENT_TYPES)

    extractions: list[ExtractionResult] = state["extractions"]
    rfq: RFQ = state["rfq"]
    ceilings: dict = state.get("ceilings", {})
    triggers: list[dict] = state.get("triggers", [])
    vendor_names = [e.vendor_name for e in extractions]

    emit(
        {
            "type": "status",
            "payload": {"message": "calling comparison model", "phase": "compare"},
        }
    )

    # Build model input — serialise extractions and triggers as JSON for the prompt
    input_payload = json.dumps(
        {
            "rfq": rfq.model_dump(mode="json"),
            "extractions": [e.model_dump(mode="json") for e in extractions],
            "attention_triggers": triggers,
        },
        default=str,
    )

    try:
        try:
            raw_output = _comparison_chain.invoke({"input": input_payload})
        except LengthFinishReasonError:
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="comparison_truncated",
                        message="Model output was truncated (finish_reason=length).",
                        recoverable=True,
                    ).model_dump(),
                }
            )
            return {"error": "truncated"}

        raw_msg = raw_output["raw"]
        if raw_msg.additional_kwargs.get("refusal"):
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="comparison_refused",
                        message="Model refused to process the comparison request.",
                        recoverable=False,
                    ).model_dump(),
                }
            )
            return {"error": "refusal"}

        parsed = raw_output.get("parsed")
        parsing_error = raw_output.get("parsing_error")
        if parsed is None or parsing_error is not None:
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="comparison_parse_error",
                        message=f"Structured output parse failed: {parsing_error!r}",
                        recoverable=True,
                    ).model_dump(),
                }
            )
            return {"error": "parse_error"}

        if not isinstance(parsed, ComparisonDraft):
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="comparison_unexpected_type",
                        message=f"Expected ComparisonDraft, got {type(parsed).__name__}",
                        recoverable=False,
                    ).model_dump(),
                }
            )
            return {"error": "unexpected_type"}

        # SUCCESS PATH (CR-01)
        # a. Fail-closed clamp
        dimensions, clamp_report = _apply_verdict_clamp(parsed, ceilings, vendor_names)

        # b. Code-built offer table (Review Fix 6)
        line_item_offers = _build_offer_table(extractions, rfq)

        # c. Code-built vendor readiness in input order (D-07)
        vendor_readiness = _build_vendor_readiness(vendor_names, dimensions)

        # d. Build attention shells from code-detected triggers
        attention_shells = _build_attention_shells(triggers)

        # e. Attach model phrasing to code-detected shells only; drop model-invented points (Review Fix 7)
        # ponytail: attaches model's phrasing to code-detected shells; extras dropped (Review Fix 7)
        model_attention: list[AttentionPoint] = getattr(parsed, "attention_points", []) or []
        model_by_type: dict[str, str] = {
            ap.trigger_type: ap.summary
            for ap in model_attention
            if hasattr(ap, "trigger_type") and hasattr(ap, "summary")
        }
        attention_points: list[AttentionPoint] = []
        for shell in attention_shells:
            summary = model_by_type.get(shell.trigger_type, "")
            attention_points.append(
                AttentionPoint(
                    trigger_type=shell.trigger_type,
                    summary=summary,
                    vendors_affected=shell.vendors_affected,
                    dimension_or_field=shell.dimension_or_field,
                )
            )

        # f. Construct pre-clarification ComparisonResult
        pre_clamp_result = ComparisonResult(
            vendor_names=vendor_names,
            dimensions=dimensions,
            line_item_offers=line_item_offers,
            vendor_readiness=vendor_readiness,
            attention_points=attention_points,
            clarification_questions=[],  # filled in clarify node
            clamp_report=clamp_report,
        )

        # g. Store in state — DO NOT emit result here (Review Fix 9)
        # ponytail: one result event total — emitted by clarify node. The compare node
        # stores the pre-clarification result in state but does NOT emit it. (Review Fix 9)
        return {
            "result": pre_clamp_result,
            "raw_draft": parsed,  # kept for generate_comparison_with_trace
        }

    except Exception as exc:
        # Log full traceback so programming errors are distinguishable from model
        # errors (both reach this handler). (Review WR-04)
        logger.exception("compare node failed")
        emit(
            {
                "type": "error",
                "payload": ErrorPayload(
                    code="comparison_error",
                    message=str(exc),
                    recoverable=False,
                ).model_dump(),
            }
        )
        return {"error": "comparison_error"}


def _run_clarify_impl(state: dict[str, Any], emit: Callable[[dict], None]) -> dict[str, Any]:
    """Node 4: generate clarification questions, emit the SINGLE final result event. (Review Fix 9)

    This is the ONLY node that emits the result event.
    """
    if state.get("error") or "result" not in state:
        emit({"type": "done", "payload": {}})
        return {}

    result: ComparisonResult = state["result"]
    extractions: list[ExtractionResult] = state["extractions"]

    emit(
        {
            "type": "status",
            "payload": {"message": "generating clarification questions", "phase": "clarify"},
        }
    )

    flagged_fields = _collect_flagged_fields(extractions)
    final_result = result

    if flagged_fields:
        try:
            flagged_json = json.dumps(
                [f.model_dump(mode="json") for f in flagged_fields],
                default=str,
            )
            clar_raw = _clarification_chain.invoke({"flagged_fields": flagged_json})

            clar_parsed = clar_raw.get("parsed")
            if clar_parsed is not None and isinstance(clar_parsed, ClarificationSet):
                # Identity validation: match by (vendor_name, field_path, flag_status) (Review Fix 8)
                valid_questions: list[ClarificationQuestion] = []
                flagged_set = {
                    (f.vendor_name, f.field_path, f.flag_status) for f in flagged_fields
                }
                for q in clar_parsed.questions:
                    identity = (q.vendor_name, q.field_path, q.flag_status)
                    if identity in flagged_set:
                        valid_questions.append(q)
                    else:
                        logger.warning(
                            "Clarification question dropped — identity not in flagged fields: %r",
                            identity,
                        )
                final_result = result.model_copy(update={"clarification_questions": valid_questions})
            else:
                logger.warning("Clarification chain returned no parsed result")

        except Exception as exc:
            # Clarification failure → AttentionPoint, do NOT abort (Review Fix 8)
            logger.warning("Clarification call failed: %s", exc)
            failed_point = AttentionPoint(
                trigger_type="clarification_generation_failed",
                summary=f"Clarification question generation failed: {exc}",
                vendors_affected=[],
                dimension_or_field=None,
            )
            updated_attention = list(result.attention_points) + [failed_point]
            final_result = result.model_copy(update={"attention_points": updated_attention})

    # Emit the ONE AND ONLY result event (Review Fix 9)
    result_event = {
        "type": "result",
        "payload": final_result.model_dump(mode="json"),
    }
    emit(result_event)
    emit({"type": "done", "payload": {}})

    return {"result": final_result, "result_sse_event": result_event}


# ---------------------------------------------------------------------------
# LangGraph nodes (production SSE path)
# ---------------------------------------------------------------------------


def _align_node(state: dict[str, Any]) -> dict[str, Any]:
    return _run_align_impl(state, get_stream_writer())


def _comparability_node(state: dict[str, Any]) -> dict[str, Any]:
    return _run_comparability_impl(state, get_stream_writer())


def _compare_node(state: dict[str, Any]) -> dict[str, Any]:
    return _run_compare_impl(state, get_stream_writer())


def _clarify_node(state: dict[str, Any]) -> dict[str, Any]:
    return _run_clarify_impl(state, get_stream_writer())


# ---------------------------------------------------------------------------
# Build and compile the graph
# ---------------------------------------------------------------------------


class ComparisonState(TypedDict, total=False):
    """Graph state channels. A typed schema is REQUIRED — with a bare ``dict``
    schema LangGraph only persists keys a node writes, so the input
    ``extractions``/``rfq`` were dropped after the align node (which returns {}),
    KeyError-ing the comparability node on the real astream/route path. Declaring
    every channel here makes unwritten keys persist (last-value reducer)."""

    extractions: list[ExtractionResult]
    rfq: RFQ
    error: str
    ceilings: Any
    scope_alignment_issues: Any
    triggers: list[Any]
    raw_draft: ComparisonDraft
    result: ComparisonResult
    result_sse_event: dict[str, Any]
    last_sse_event: dict[str, Any]


def _build_comparison_graph():  # noqa: ANN201
    builder = StateGraph(ComparisonState)
    builder.add_node("align", _align_node)
    builder.add_node("comparability", _comparability_node)
    builder.add_node("compare", _compare_node)
    builder.add_node("clarify", _clarify_node)
    builder.add_edge(START, "align")
    builder.add_edge("align", "comparability")
    builder.add_edge("comparability", "compare")
    builder.add_edge("compare", "clarify")
    builder.add_edge("clarify", END)
    return builder.compile()


comparison_graph = _build_comparison_graph()


# ---------------------------------------------------------------------------
# Testable sync wrapper (test/script use only)
# ---------------------------------------------------------------------------


def run_comparison(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> dict[str, Any]:
    """Synchronous testable wrapper for the comparison nodes.

    Calls the 4 _run_*_impl functions directly (bypassing LangGraph runtime) so
    tests can patch _comparison_chain / _clarification_chain and inspect emitted
    events without a running event loop.

    Returns the merged state dict with:
      last_sse_event  — the last event emitted
      result_sse_event — the result event if one was emitted

    # ponytail: direct node invocation for testability — does NOT exercise
    # the LangGraph SSE streaming path. Production path uses
    # comparison_graph.astream(stream_mode="custom"). Use this only in tests
    # and scripts.
    """
    events: list[dict] = []

    def _collect(event: dict) -> None:
        events.append(event)

    state: dict[str, Any] = {"extractions": extractions, "rfq": rfq}

    for impl in (
        _run_align_impl,
        _run_comparability_impl,
        _run_compare_impl,
        _run_clarify_impl,
    ):
        updates = impl(state, _collect)
        state.update(updates)
        if state.get("error"):
            break

    if events:
        state["last_sse_event"] = events[-1]

    if "result_sse_event" not in state:
        result_events = [e for e in events if e.get("type") == "result"]
        if result_events:
            state["result_sse_event"] = result_events[-1]

    return state


# ---------------------------------------------------------------------------
# Trace capture surface (D-11)
# ---------------------------------------------------------------------------


def generate_comparison_with_trace(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> tuple[ComparisonDraft, ComparisonResult, ClampReport, list[ClarificationQuestion]]:
    """Capture raw ComparisonDraft + clamped ComparisonResult for the D-11 trace.

    Returns (raw_draft, clamped_result, clamp_report, clarification_questions).
    raw_draft is the ComparisonDraft before clamping (the model's proposed verdicts).

    Raises ValueError on any failure shape so capture_traces.py knows the trace is unusable.

    # ponytail: exposes raw draft vs clamped result for D-11 trace capture;
    # not used in the production SSE path.
    """
    state = run_comparison(extractions, rfq)
    if state.get("error"):
        raise ValueError(f"Comparison failed: {state['error']}")
    result: ComparisonResult = state["result"]
    raw_draft: ComparisonDraft = state.get("raw_draft")
    if raw_draft is None:
        raise ValueError("No raw_draft captured — model call may have been patched")
    return (
        raw_draft,
        result,
        result.clamp_report,
        result.clarification_questions,
    )
