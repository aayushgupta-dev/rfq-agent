"""
capture_comparison_trace.py — Fixture-mode comparison trace capture (D-11 / Review Fix 5).

Builds a deterministic over-optimistic ComparisonDraft (all verdicts = "comparable"),
runs the real _apply_verdict_clamp against real ExtractionResult data, and writes the
resulting trace to docs/traces/comparison_trace_1.{json,md}.

Fixture mode guarantees has_downgrades == True for any vendor with missing fields —
no live model call is needed or made. (Review Fix 5)

# ponytail: fixture draft bypasses the model call; the real clamp runs on real ExtractionResult data.
# This guarantees has_downgrades == True for any vendor with missing fields. (Review Fix 5)
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).parents[3]
DATA_DIR = REPO_ROOT / "data"
TRACES_DIR = REPO_ROOT / "docs" / "traces"

from agents.comparison import _apply_verdict_clamp, _compute_ceilings  # noqa: E402
from prompts.registry import load  # noqa: E402
from schemas.domain import (  # noqa: E402
    ComparisonDimension,
    ComparisonDraft,
    ComparisonResult,
    DimensionComparison,
    DimensionComparisonDraft,
    DimensionVerdict,
    DimensionVerdictDraft,
    ComparabilityVerdict,
    ExtractionResult,
    RFQ,
    VendorReadiness,
)
from schemas.envelope import FlagStatus  # noqa: E402


def _load_rfq() -> RFQ:
    return RFQ.model_validate_json((DATA_DIR / "rfq.json").read_text())


def _load_extractions_from_traces() -> list[ExtractionResult]:
    """Load ExtractionResult objects from committed extraction traces.

    Loads from docs/traces/trace_vendor_*.json using the final_result key.
    """
    exts: list[ExtractionResult] = []
    for f in sorted(TRACES_DIR.glob("trace_vendor_*.json")):
        t = json.loads(f.read_text())
        final = t.get("final_result")
        if not final:
            print(f"  WARN: {f.name} has no final_result — skipping", file=sys.stderr)
            continue
        ext = ExtractionResult.model_validate(final)
        exts.append(ext)
        print(f"  Loaded extraction: {ext.vendor_name} from {f.name}")
    return exts


def _build_fixture_draft(
    extractions: list[ExtractionResult],
) -> tuple[ComparisonDraft, dict]:
    """Build a deterministic over-optimistic ComparisonDraft.

    Proposes 'comparable' for EVERY vendor on EVERY dimension, regardless of actual
    flag states. The clamp will downgrade wherever flags dictate.
    Also computes and returns real ceilings via _compute_ceilings(extractions).

    # ponytail: fixture draft bypasses the model call; the real clamp runs on real ExtractionResult data.
    # This guarantees has_downgrades == True for any vendor with missing fields. (Review Fix 5)
    """
    vendor_names = [e.vendor_name for e in extractions]
    ceilings = _compute_ceilings(extractions)

    dims: list[DimensionComparisonDraft] = []
    for dim in ComparisonDimension:
        verdicts = [
            DimensionVerdictDraft(
                vendor_name=vn,
                model_proposed=ComparabilityVerdict.comparable,
                reason="fixture: proposed comparable for all vendors on all dimensions",
            )
            for vn in vendor_names
        ]
        dims.append(
            DimensionComparisonDraft(
                dimension=dim.value,
                verdicts=verdicts,
                narrative=(
                    f"Fixture narrative for {dim.value} dimension — "
                    "all vendors proposed comparable before code clamp."
                ),
            )
        )

    draft = ComparisonDraft(
        dimensions=dims,
        narrative_summary=(
            "Fixture draft: model proposed 'comparable' for all vendors on all dimensions. "
            "Code clamped this where flag statuses dictate not_comparable or partially."
        ),
    )
    return draft, ceilings


def _build_comparison_trace(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> dict:
    """Build the comparison trace dict using fixture-mode draft + real clamp.

    Steps:
    1. Compute real ceilings from real ExtractionResult data.
    2. Build fixture draft (all comparable).
    3. Run real _apply_verdict_clamp.
    4. Assert has_downgrades — fail hard if False (Review Fix 5).
    5. Build trace dict with required keys.
    """
    vendor_names = [e.vendor_name for e in extractions]
    draft, ceilings = _build_fixture_draft(extractions)

    # Run real clamp against real ExtractionResult ceilings
    dim_comparisons, clamp_report = _apply_verdict_clamp(draft, ceilings, vendor_names)

    has_downgrades = len(clamp_report.entries) >= 1
    if not has_downgrades:
        print(
            "ERROR: trace has 0 clamp entries. "
            "Fix fixture draft or check extraction data. (Review Fix 5)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build final ComparisonResult from clamped dimensions
    readiness: list[VendorReadiness] = []
    for vname in vendor_names:
        comparable_count = sum(
            1
            for dc in dim_comparisons
            for dv in dc.verdicts
            if dv.vendor_name == vname and dv.verdict == ComparabilityVerdict.comparable
        )
        blocked_dims = [
            dc.dimension.value
            for dc in dim_comparisons
            for dv in dc.verdicts
            if dv.vendor_name == vname and dv.verdict != ComparabilityVerdict.comparable
        ]
        descriptor = (
            f"{comparable_count} of 6 dimensions comparable; blocked on {', '.join(blocked_dims)}"
            if blocked_dims
            else f"{comparable_count} of 6 dimensions comparable"
        )
        readiness.append(
            VendorReadiness(
                vendor_name=vname,
                comparable_count=comparable_count,
                total_dimensions=6,
                descriptor=descriptor,
            )
        )

    from schemas.domain import ClampReport
    clamped_result = ComparisonResult(
        vendor_names=vendor_names,
        dimensions=dim_comparisons,
        line_item_offers=[],  # not needed for trace demonstration
        vendor_readiness=readiness,
        attention_points=[],
        clarification_questions=[],
        clamp_report=clamp_report,
    )

    # Build flag counts per vendor for input summary
    extraction_summaries = []
    for ext in extractions:
        from agents.comparison import _collect_flagged_fields
        flagged = _collect_flagged_fields([ext])
        flag_counts: dict[str, int] = {}
        for f in flagged:
            flag_counts[f.flag_status] = flag_counts.get(f.flag_status, 0) + 1
        extraction_summaries.append({
            "vendor_name": ext.vendor_name,
            "flag_counts": flag_counts,
        })

    # Load prompt for trace
    comp_post = load("comparison")
    system_excerpt = comp_post.content[:500] + "..." if len(comp_post.content) > 500 else comp_post.content

    trace: dict = {
        "_fixture_mode": True,
        "input": {
            "vendor_names": vendor_names,
            "rfq_title": getattr(rfq, "title", "GlowBite 18-Month Go-to-Market Program RFQ"),
            "extraction_summaries": extraction_summaries,
        },
        "resolved_prompt": {
            "id": comp_post.metadata.get("id", "comparison"),
            "version": comp_post.metadata.get("version", 1),
            "system_message_excerpt": system_excerpt,
        },
        "raw_model_output": draft.model_dump(mode="json"),
        "clamp_step": clamp_report.model_dump(mode="json"),
        "clarification_step": {
            "flagged_fields_input": [],
            "note": "fixture mode — no live model call; clarification not executed",
        },
        "final_result": clamped_result.model_dump(mode="json"),
    }
    return trace


def _write_comparison_markdown(trace: dict, path: pathlib.Path) -> None:
    """Write a human-readable Markdown trace for the Aerchain reviewer."""
    inp = trace["input"]
    rp = trace["resolved_prompt"]
    clamp = trace["clamp_step"]
    fr = trace["final_result"]

    lines: list[str] = []

    lines.append("# Comparison Trace — Fixture Mode\n")
    lines.append("> **Fixture Mode:** This trace uses a deterministic over-optimistic fixture draft.")
    lines.append("> No live OpenAI call was made. See the Fixture Mode Note section for details.\n")

    lines.append("## 1. Input\n")
    lines.append(f"- **RFQ:** {inp['rfq_title']}")
    lines.append(f"- **Vendors:** {', '.join(inp['vendor_names'])}")
    lines.append("")
    lines.append("### Flag counts per vendor\n")
    lines.append("| Vendor | missing | unclear | conflicting | unsupported |")
    lines.append("|--------|---------|---------|-------------|-------------|")
    for s in inp.get("extraction_summaries", []):
        fc = s.get("flag_counts", {})
        lines.append(
            f"| {s['vendor_name']} "
            f"| {fc.get('missing', 0)} "
            f"| {fc.get('unclear', 0)} "
            f"| {fc.get('conflicting', 0)} "
            f"| {fc.get('unsupported', 0)} |"
        )
    lines.append("")

    lines.append("## 2. Resolved Prompt\n")
    lines.append(f"- **id:** {rp['id']}")
    lines.append(f"- **version:** {rp['version']}")
    lines.append(f"\n**System message excerpt:**\n```\n{rp['system_message_excerpt']}\n```\n")

    lines.append("## 3. THE VERDICT-CLAMP DIFF\n")
    lines.append(
        "> This is the rubric story: model proposed 'comparable' for all; "
        "code clamped where flags dictate.\n"
    )
    entries = clamp.get("entries", [])
    if entries:
        lines.append(
            "| Vendor | Dimension | Model Proposed | Code Ceiling | Clamped To | Ceiling Reason |"
        )
        lines.append("|--------|-----------|----------------|--------------|------------|----------------|")
        for e in entries:
            lines.append(
                f"| {e['vendor_name']} "
                f"| {e['dimension']} "
                f"| {e['model_proposed']} "
                f"| {e['code_ceiling']} "
                f"| **{e['clamped_to']}** "
                f"| {e['ceiling_reason']} |"
            )
    else:
        lines.append("_No clamp entries — ERROR: fixture mode should always produce downgrades._")
    lines.append("")

    lines.append("## 4. Clarification Questions\n")
    lines.append(
        "_fixture mode — no live clarification call made. "
        "In production, the clarify node generates one question per flagged field._\n"
    )

    lines.append("## 5. Final Result — Vendor Readiness\n")
    readiness_list = fr.get("vendor_readiness", [])
    if readiness_list:
        lines.append("| Vendor | Comparable Dimensions | Descriptor |")
        lines.append("|--------|-----------------------|------------|")
        for vr in readiness_list:
            lines.append(
                f"| {vr['vendor_name']} "
                f"| {vr['comparable_count']}/6 "
                f"| {vr['descriptor']} |"
            )
    lines.append("")

    lines.append("## 6. Fixture Mode Note\n")
    lines.append(
        "This trace uses a deterministic over-optimistic fixture draft. "
        "The model was NOT called. Instead, a synthetic ComparisonDraft was constructed "
        "with `model_proposed='comparable'` for every vendor on every dimension. "
        "The real `_apply_verdict_clamp` function then ran against real ExtractionResult "
        "data (loaded from committed extraction traces), producing the downgrade diff above.\n"
    )
    lines.append(
        "**Why fixture mode?** The clamp diff must be reproducible and deterministic. "
        "A live model call may or may not produce over-optimistic verdicts — depending on "
        "the model's judgment. Fixture mode guarantees `has_downgrades == True` for any "
        "vendor with missing fields, making the code-authority guarantee demonstrable "
        "without relying on model misbehavior. (Review Fix 5)\n"
    )
    lines.append(
        "**What this proves:** Code, not the model, decides the final comparability verdict. "
        "The clamp diff table shows exactly where model-proposed 'comparable' was downgraded "
        "to 'not_comparable' or 'partially' because the code ceiling rule detected missing "
        "or ambiguous fields in the extraction data.\n"
    )

    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path.name}")


def main() -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading extractions from committed traces...")
    extractions = _load_extractions_from_traces()
    if len(extractions) < 2:
        print("ERROR: need at least 2 vendor extractions to produce a meaningful trace.", file=sys.stderr)
        sys.exit(1)

    print("Loading RFQ...")
    rfq = _load_rfq()

    print("Building fixture-mode comparison trace...")
    trace = _build_comparison_trace(extractions, rfq)

    n_entries = len(trace["clamp_step"]["entries"])
    print(f"  Clamp entries: {n_entries}")

    json_path = TRACES_DIR / "comparison_trace_1.json"
    md_path = TRACES_DIR / "comparison_trace_1.md"

    json_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False))
    print(f"  Wrote {json_path.name}")

    _write_comparison_markdown(trace, md_path)

    print(f"\nDone. Trace written with {n_entries} clamp entries.")


if __name__ == "__main__":
    main()
