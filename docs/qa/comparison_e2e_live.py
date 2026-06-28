"""Gate 4 — functional E2E for the comparison agent with REAL GPT-5.4.

Drives the production route (POST /compare/vendors → graph astream → live model)
over the 3 real Phase-3 vendor extraction results, asserts the rubric-critical
behaviours against the REAL model output, and captures docs/traces/comparison_trace_2
(live mode) to satisfy assignment §16 ("Model output").

Repeatable UAT artifact (CLAUDE.md §11). Requires a live OPENAI_API_KEY + MODEL_*
in the repo-root .env (auto-loaded by llm.factory at import).

Run:  cd services/ai && uv run python ../../docs/qa/comparison_e2e_live.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# repo root = two levels up from docs/qa/
AER = Path(__file__).resolve().parents[2]
TRACES = AER / "docs" / "traces"

sys.path.insert(0, str(AER / "services" / "ai"))

from fastapi.testclient import TestClient  # noqa: E402

from agents.comparison import _VERDICT_ORDER, _compute_ceilings  # noqa: E402
from api.app import app  # noqa: E402
from schemas.domain import RFQ, ComparisonResult, ExtractionResult  # noqa: E402

VENDOR_ORDER = ["cheap", "fluff", "thorough"]
ABSENCE = {"", "none", "null", "n/a", "not provided", "missing", "—", "-"}

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  PASS" if cond else "  FAIL"), msg)
    if not cond:
        failures.append(msg)


def main() -> int:
    # ---- Load real inputs ----
    rfq = RFQ.model_validate_json((AER / "data" / "rfq.json").read_text())
    extractions: list[ExtractionResult] = []
    for v in VENDOR_ORDER:
        d = json.loads((TRACES / f"trace_vendor_{v}.json").read_text())
        extractions.append(ExtractionResult.model_validate(d["final_result"]))
    print(f"Loaded RFQ ({len(rfq.line_items)} line items) + {len(extractions)} real extractions:",
          [e.vendor_name for e in extractions])

    body = {
        "extractions": [e.model_dump(mode="json") for e in extractions],
        "rfq": rfq.model_dump(mode="json"),
    }

    # ---- Hit the REAL production route (no mocking → live GPT-5.4) ----
    print("\nPOST /compare/vendors  (live GPT-5.4 — reasoning + cheap)...")
    client = TestClient(app, raise_server_exceptions=True)
    resp = client.post("/compare/vendors", json=body)
    check(resp.status_code == 200, f"HTTP 200 (got {resp.status_code})")

    events = []
    for line in resp.text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    types = [e["type"] for e in events]
    print("  SSE event types:", types)

    # ---- A. Transport contract (validates the graph-state fix end-to-end) ----
    check(types.count("result") == 1, f"exactly one 'result' event (got {types.count('result')})")
    check(types.count("done") == 1, f"exactly one 'done' event (got {types.count('done')})")
    check(types and types[-1] == "done", "last event is 'done'")
    check("error" not in types, "no 'error' event")

    result_payload = next(e["payload"] for e in events if e["type"] == "result")
    result = ComparisonResult.model_validate(result_payload)

    # ---- B. Vendor order preserved (COMPARE-05) ----
    check(result.vendor_names == [e.vendor_name for e in extractions],
          f"vendor order preserved: {result.vendor_names}")

    # ---- C. Qualitative only — no numeric score/rank anywhere (COMPARE-05 / §24) ----
    check(not any(k in result_payload for k in ("score", "rank", "weight")),
          "no score/rank/weight top-level field")
    valid_verdicts = {"comparable", "partially", "not_comparable"}
    all_verdicts = [
        dv.verdict for dim in result.dimensions for dv in dim.verdicts
    ]
    check(all(v in valid_verdicts for v in all_verdicts),
          f"every verdict is a qualitative enum ({len(all_verdicts)} verdicts)")

    # ---- D. Comparability BEFORE scoring + NO aggregation over missing (COMPARE-02) ----
    # Recompute code ceilings independently from the real extractions and assert the
    # final (real-model→clamped) verdict NEVER exceeds the code ceiling. This is the
    # core "code, not the model, decides comparability" guarantee on LIVE output.
    nested = _compute_ceilings(extractions)  # {ComparisonDimension: {vendor: ceiling_str}}
    ceilings = {}  # flat {(vendor, dim_str): ceiling_str}
    for dim_key, per_vendor in nested.items():
        for vendor, ceil in per_vendor.items():
            ceilings[(vendor, str(dim_key))] = ceil
    violations = []
    for dim in result.dimensions:
        for dv in dim.verdicts:
            ceiling = ceilings.get((dv.vendor_name, str(dim.dimension)))
            if ceiling is None:
                continue
            if _VERDICT_ORDER[str(dv.verdict)] > _VERDICT_ORDER[str(ceiling)]:
                violations.append(f"{dv.vendor_name}/{dim.dimension}: {dv.verdict} > ceiling {ceiling}")
    check(not violations, f"no final verdict exceeds its code ceiling ({len(violations)} violations)")
    if violations:
        for v in violations:
            print("      !", v)

    # ---- E. Clamp report integrity: clamped_to == min(model_proposed, code_ceiling) ----
    clamp_entries = result.clamp_report.entries
    bad_clamp = [
        f"{c.vendor_name}/{c.dimension}: proposed={c.model_proposed} ceiling={c.code_ceiling} clamped={c.clamped_to}"
        for c in clamp_entries
        if c.clamped_to != (c.model_proposed if _VERDICT_ORDER[c.model_proposed] <= _VERDICT_ORDER[c.code_ceiling] else c.code_ceiling)
    ]
    check(not bad_clamp, f"every clamp entry == min(model, ceiling) ({len(clamp_entries)} entries, {len(bad_clamp)} bad)")
    downgrades = [c for c in clamp_entries if c.model_proposed != c.clamped_to]
    print(f"      live downgrades (model overruled by code): {len(downgrades)}")

    # ---- F. No fabricated pricing — offer prices trace back to extraction (grounding) ----
    # Each LineItemOffer is flat per (line_item, vendor) with pricing_verbatim copied
    # from the extraction. Assert no offer carries a pricing string absent from that
    # vendor's source extraction (would indicate fabrication). Absence markers allowed.
    src_prices_by_vendor: dict[str, set[str]] = {}
    for e in extractions:
        s = src_prices_by_vendor.setdefault(e.vendor_name, set())
        for li in e.line_items:
            pricing = getattr(li, "pricing", None)
            val = getattr(pricing, "value", None) if pricing is not None else None
            if val is not None:
                s.add(str(val).strip())
    fabricated = []
    for offer in result.line_item_offers:
        pv = getattr(offer, "pricing_verbatim", None)
        if pv is None:
            continue
        pv_s = str(pv).strip()
        if pv_s.lower() in ABSENCE:
            continue
        vendor_src = src_prices_by_vendor.get(offer.vendor_name, set())
        # verbatim => exact match, or a substring of a source value (offer may quote a slice)
        ok = pv_s in vendor_src or any(pv_s in src or src in pv_s for src in vendor_src)
        if not ok:
            fabricated.append(f"{offer.vendor_name}/{getattr(offer,'line_item_id','?')}: {pv_s!r}")
    check(not fabricated, f"no fabricated offer prices (checked {len(result.line_item_offers)} offers, {len(fabricated)} suspect)")
    if fabricated:
        for f in fabricated[:8]:
            print("      ?", f)

    # ---- G. Gaps → clarification questions (COMPARE-03) ----
    qs = result.clarification_questions
    check(len(qs) >= 1, f"clarification questions generated for flagged fields (got {len(qs)})")
    check(len(result.attention_points) >= 1, f"attention points raised (got {len(result.attention_points)})")

    # ---- Capture comparison_trace_2 (LIVE) ----
    trace = {
        "_live_mode": True,
        "_model_reasoning": "gpt-5.4 (MODEL_REASONING)",
        "_model_clarification": "gpt-5.4-mini (MODEL_CHEAP)",
        "input": {
            "rfq_title": getattr(rfq, "title", ""),
            "vendors": [e.vendor_name for e in extractions],
        },
        "clamp_step": {
            "entries": [c.model_dump(mode="json") for c in clamp_entries],
            "live_downgrade_count": len(downgrades),
        },
        "clarification_questions": [q.model_dump(mode="json") for q in qs],
        "vendor_readiness": [r.model_dump(mode="json") for r in result.vendor_readiness],
        "result": result_payload,
    }
    (TRACES / "comparison_trace_2.json").write_text(json.dumps(trace, indent=2, default=str))

    md = []
    md.append("# Comparison Trace 2 — Live Mode (real GPT-5.4)")
    md.append("")
    md.append("> **Live Mode:** real GPT-5.4 call via `POST /compare/vendors` (the production route).")
    md.append("> Reasoning model: `gpt-5.4` · Clarification model: `gpt-5.4-mini`.")
    md.append("> Companion to the deterministic fixture trace (`comparison_trace_1`).")
    md.append("")
    md.append("## 1. Input")
    md.append(f"- **RFQ:** {trace['input']['rfq_title']}")
    md.append(f"- **Vendors:** {', '.join(trace['input']['vendors'])}")
    md.append("")
    md.append("## 2. Resolved Prompt")
    md.append("- comparison.v1 (reasoning) + clarification.v1 (cheap)")
    md.append("")
    md.append("## 3. Verdict-Clamp Diff (real model proposed → code clamped)")
    md.append("")
    if clamp_entries:
        md.append("| Vendor | Dimension | Model Proposed | Code Ceiling | Clamped To |")
        md.append("|--------|-----------|----------------|--------------|------------|")
        for c in clamp_entries:
            mark = " **(downgraded)**" if c.model_proposed != c.clamped_to else ""
            md.append(f"| {c.vendor_name} | {c.dimension} | {c.model_proposed} | {c.code_ceiling} | {c.clamped_to}{mark} |")
        md.append("")
        md.append(f"_Live downgrades (code overruled the real model): {len(downgrades)}._")
        md.append("")
        md.append("> Note: with an honest model, downgrades may be 0 — the guarantee is that no "
                  "final verdict EVER exceeds the code ceiling (asserted in the E2E), so code remains "
                  "the authority whether or not the model happened to over-claim.")
    else:
        md.append("_No clamp entries recorded._")
    md.append("")
    md.append("## 4. Clarification Questions (live)")
    if qs:
        for q in qs:
            qd = q.model_dump()
            qtext = qd.get("question") or qd.get("question_text") or qd.get("text") or ""
            md.append(f"- **{qd.get('vendor_name','')}** / `{qd.get('field_path','')}` "
                      f"({qd.get('flag_status','')}): {qtext}")
    else:
        md.append("_None generated._")
    md.append("")
    md.append("## 5. Vendor Readiness")
    md.append("| Vendor | Readiness |")
    md.append("|--------|-----------|")
    for r in result.vendor_readiness:
        rd = r.model_dump()
        vendor = rd.get("vendor_name", "")
        desc = (rd.get("readiness_descriptor") or rd.get("descriptor")
                or rd.get("summary") or json.dumps({k: v for k, v in rd.items() if k != "vendor_name"}, default=str))
        md.append(f"| {vendor} | {desc} |")
    md.append("")
    (TRACES / "comparison_trace_2.md").write_text("\n".join(md))
    print(f"\nWrote {TRACES / 'comparison_trace_2.json'} and .md")

    print("\n" + ("=" * 60))
    if failures:
        print(f"E2E FAILED — {len(failures)} assertion(s) failed:")
        for f in failures:
            print("  -", f)
        return 1
    print("E2E PASSED — all rubric assertions hold on live GPT-5.4 output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
