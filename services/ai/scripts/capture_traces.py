"""
capture_traces.py — One-shot trace capture for extraction agent (D-12..D-15).

Reads committed vendor fixtures from data/, calls generate_extraction_with_trace
(the ONLY authorized trace-capture surface — D-14/D-15), writes JSON + Markdown
traces to docs/traces/.

D-15 FALLBACK LADDER (B-R3):
  Step 1 — Strengthen verbatim-quoting instruction in extraction.v1.md and re-run.
  Step 2 — Inject an adversarial fixture (vague vendor text to induce paraphrase-catch).
  Step 3 — DO NOT lower FUZZY_THRESHOLD. Lowering it to manufacture a downgrade is
           forbidden (B-R3 / CLAUDE.md §2/§8). A manufactured downgrade via threshold-
           lowering is not the same as a genuine fabrication caught.

# ponytail: FUZZY_THRESHOLD is intentionally NOT a dial to turn for trace production.
# Any threshold change must pass a regression assert that genuine spans still survive.
"""
from __future__ import annotations

import json
import pathlib
import sys

# Repo root is 3 levels up from services/ai/scripts/
REPO_ROOT = pathlib.Path(__file__).parents[3]
DATA_DIR = REPO_ROOT / "data"
TRACES_DIR = REPO_ROOT / "docs" / "traces"

# Import after path is established (agents.extraction uses relative imports via uv run)
from agents.extraction import generate_extraction_with_trace  # noqa: E402
from prompts.registry import load  # noqa: E402
from schemas.domain import RFQ, VendorResponse  # noqa: E402


def _load_rfq() -> RFQ:
    return RFQ.model_validate_json((DATA_DIR / "rfq.json").read_text())


def _load_vendor(filename: str) -> VendorResponse:
    return VendorResponse.model_validate_json((DATA_DIR / filename).read_text())


def _build_trace(
    vendor: VendorResponse,
    rfq: RFQ,
    fixture_type: str | None = None,
) -> dict | None:
    """Run extraction, return trace dict or None on failure."""
    vendor_slug = vendor.vendor_name.replace("-", "_")
    try:
        raw_ungrounded, grounded, report = generate_extraction_with_trace(vendor, rfq)
    except ValueError as exc:
        print(f"  ERROR for {vendor.vendor_name}: {exc}", file=sys.stderr)
        return None

    prompt_post = load("extraction")
    # Human turn template — matches extraction.py _prompt definition
    human_template = (
        "Vendor source ID (use this exact value for all evidence source_id fields): {source_id}\n\n"
        "Vendor response:\n{vendor_text}\n\n"
        "RFQ line items (JSON):\n{rfq_line_items}"
    )
    # ponytail: Post is a frontmatter.Post (dict-style access); metadata holds frontmatter fields.
    prompt_id = prompt_post.metadata.get("id", "extraction")
    prompt_version = prompt_post.metadata.get("version", 1)

    trace: dict = {
        "input": {
            "vendor_name": vendor.vendor_name,
            "source_id": vendor.source_id,
            "rfq_line_items": [
                {"id": li.id, "name": li.name, "description": li.description}
                for li in rfq.line_items
            ],
            "raw_text_preview": vendor.raw_text[:500],
        },
        "resolved_prompt": {
            "id": prompt_id,
            "version": prompt_version,
            "system_message": prompt_post.content,
            "human_message_template": human_template,
        },
        "raw_model_output": raw_ungrounded.model_dump(mode="json"),
        "grounding_step": {
            "downgrade_report": report.model_dump(mode="json"),
            "fields_downgraded": len(report.entries),
            # ponytail: fields_checked omitted — DowngradeReport only carries entries;
            # deriving a checked-count requires schema introspection the script should not duplicate.
        },
        "final_result": grounded.model_dump(mode="json"),
    }

    if fixture_type is not None:
        trace["input"]["fixture_type"] = fixture_type
        # Synthetic fixtures are not committed to data/, so store the full source so
        # test_traces_committed can verify evidence integrity against the whole text
        # (the 500-char preview can truncate a quoted span).
        trace["input"]["raw_text_full"] = vendor.raw_text

    return trace


def _write_json(trace: dict, path: pathlib.Path) -> None:
    path.write_text(json.dumps(trace, indent=2, ensure_ascii=False))
    print(f"  Wrote {path.name}")


def _write_markdown(trace: dict, path: pathlib.Path) -> None:
    inp = trace["input"]
    rp = trace["resolved_prompt"]
    gs = trace["grounding_step"]
    fr = trace["final_result"]
    dr = gs["downgrade_report"]

    lines: list[str] = []
    lines.append(f"# Extraction Trace — {inp['vendor_name']}\n")
    if inp.get("fixture_type"):
        lines.append(f"> **fixture_type:** {inp['fixture_type']}\n")
    lines.append("## Input\n")
    lines.append(f"- **Vendor:** {inp['vendor_name']}")
    lines.append(f"- **Source ID:** {inp['source_id']}")
    lines.append(f"- **RFQ line items:** {len(inp['rfq_line_items'])}")
    lines.append(f"\n**Raw text preview (first 500 chars):**\n```\n{inp['raw_text_preview']}\n```\n")

    lines.append("## Resolved Prompt\n")
    lines.append(f"- **id:** {rp['id']}")
    lines.append(f"- **version:** {rp['version']}\n")

    lines.append("## Grounding Step\n")
    lines.append(f"- **Fields downgraded:** {gs['fields_downgraded']}\n")
    entries = dr.get("entries", [])
    if entries:
        lines.append("### Downgraded Fields\n")
        lines.append("| field_path | original_status | reason |")
        lines.append("|---|---|---|")
        for e in entries:
            lines.append(f"| `{e['field_path']}` | {e['original_status']} | {e['reason']} |")
        lines.append("")
    else:
        lines.append("_No fields downgraded — all evidence snippets located verbatim._\n")

    lines.append("## Final Result (top-level status summary)\n")
    # Summarize top-level Field statuses
    field_keys = [
        "scope_summary", "pricing_structure", "total_price",
        "commercial_terms", "timeline",
    ]
    for key in field_keys:
        field = fr.get(key, {})
        status = field.get("status", "—") if isinstance(field, dict) else "—"
        lines.append(f"- **{key}:** {status}")

    # Line items summary
    line_items = fr.get("line_items", [])
    if line_items:
        lines.append(f"\n### Line Items ({len(line_items)} extracted)\n")
        lines.append("| line_item_name | pricing status | scope_coverage status |")
        lines.append("|---|---|---|")
        for li in line_items:
            pricing_status = li.get("pricing", {}).get("status", "—") if isinstance(li.get("pricing"), dict) else "—"
            scope_status = li.get("scope_coverage", {}).get("status", "—") if isinstance(li.get("scope_coverage"), dict) else "—"
            lines.append(f"| {li.get('line_item_name', '?')} | {pricing_status} | {scope_status} |")

    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path.name}")


def main() -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    rfq = _load_rfq()

    vendors = [
        ("vendor_cheap.json", "vendor_cheap"),
        ("vendor_fluff.json", "vendor_fluff"),
        ("vendor_thorough.json", "vendor_thorough"),
    ]

    downgrades_per_vendor: dict[str, int] = {}

    for filename, slug in vendors:
        vendor = _load_vendor(filename)
        print(f"\nProcessing {vendor.vendor_name} ({filename})...")
        trace = _build_trace(vendor, rfq)
        if trace is None:
            downgrades_per_vendor[vendor.vendor_name] = -1  # error
            continue
        n = trace["grounding_step"]["fields_downgraded"]
        downgrades_per_vendor[vendor.vendor_name] = n
        _write_json(trace, TRACES_DIR / f"trace_{slug}.json")
        _write_markdown(trace, TRACES_DIR / f"trace_{slug}.md")

    print("\n--- Downgrade summary ---")
    total_downgrades = 0
    for name, count in downgrades_per_vendor.items():
        status = f"{count} downgrade(s)" if count >= 0 else "ERROR"
        print(f"  {name}: {status}")
        if count > 0:
            total_downgrades += count

    # D-15 FALLBACK LADDER CHECK
    if total_downgrades == 0:
        print(
            "\nWARNING: 0 downgrades across all vendors. "
            "D-15 requires >=1 genuine downgrade.\n"
            "Fallback ladder:\n"
            "  Step 1 — Strengthen verbatim-quoting instruction in extraction.v1.md and re-run.\n"
            "  Step 2 — Add adversarial fixture (see script comments).\n"
            "  Step 3 — DO NOT lower FUZZY_THRESHOLD (B-R3).",
            file=sys.stderr,
        )
        # Step 2: adversarial fixture — vague text designed to induce paraphrase-catch
        print("\nRunning adversarial fixture (D-15 Step 2)...")
        # Adversarial fixture: scattered, paraphrase-prone text.
        # Key facts are implied but never stated as a single quotable sentence.
        # The model must either quote a near-miss (triggering a downgrade) or
        # correctly return missing/unclear. If it fabricates a composite snippet
        # that isn't verbatim, the gate catches it.
        adversarial_vendor = VendorResponse(
            vendor_name="adversarial-fixture",
            persona="adversarial-fixture",
            mess_spec=[],
            source_id="vendor_adversarial_fixture",
            format_label="text",
            raw_text=(
                "Agency Proposal — GlowBite RFQ Response\n\n"
                "Section A: Introduction\n"
                "We are a full-service creative and media agency. Our work spans strategy, "
                "brand development, and integrated campaign delivery across consumer categories.\n\n"
                "Section B: Commercial Approach\n"
                "Fees for strategic engagements of this nature are scoped individually. "
                "We do not publish rate cards. Investment levels are discussed after a "
                "discovery session. Our commercial model is designed to align with client "
                "outcomes and program complexity.\n\n"
                "Section C: Timeline\n"
                "Program timelines reflect the scope complexity and client readiness factors. "
                "We plan work collaboratively with clients. Duration is typically confirmed "
                "during onboarding. We have delivered comparable programs in periods ranging "
                "from six to eighteen months depending on approval cycles.\n\n"
                "Section D: Compliance\n"
                "We work within all applicable regulatory and industry guidelines. Our "
                "internal compliance review covers all relevant advertising standards.\n\n"
                "Section E: Summary\n"
                "We believe this engagement presents an excellent fit for our capabilities. "
                "We welcome a conversation to discuss fit and next steps."
            ),
        )
        adv_trace = _build_trace(adversarial_vendor, rfq, fixture_type="adversarial")
        if adv_trace is not None:
            adv_n = adv_trace["grounding_step"]["fields_downgraded"]
            print(f"  Adversarial fixture: {adv_n} downgrade(s)")
            _write_json(adv_trace, TRACES_DIR / "trace_adversarial_fixture.json")
            _write_markdown(adv_trace, TRACES_DIR / "trace_adversarial_fixture.md")
            if adv_n > 0:
                print("  D-15 satisfied via adversarial fixture.")
            else:
                print(
                    "  Step 2 produced 0 downgrades. "
                    "Step 3 (FUZZY_THRESHOLD lowering) is FORBIDDEN.\n"
                    "Escalate: /gsd:plan-phase --gaps — the model quotes perfectly on "
                    "all fixtures including the adversarial one.",
                    file=sys.stderr,
                )
    else:
        print(f"\nD-15: {total_downgrades} genuine downgrade(s) found across real vendor fixtures.")


if __name__ == "__main__":
    main()
