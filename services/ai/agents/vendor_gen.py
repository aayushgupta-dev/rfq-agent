"""
vendor_gen.py — Vendor response generation agent for the Bid Desk AI service.

One-pass generation — see D-08. The LLM is instructed to produce a messy,
realistic vendor proposal in a single call, not a clean response that is then
"vandalized". This preserves coherent prose and prevents post-hoc vandalism from
creating obviously artificial artifacts.

Three vendor personas (D-10): thorough-but-pricey, cheap-but-incomplete,
polished-fluff. Each persona has a hand-authored MESS_SPECS entry (D-09) that
defines exactly what deliberate flaws to inject — making the messiness
deterministic and assertable in tests (D-13).

FIXTURE_FILENAMES is the authoritative source for output filenames. Short names
(vendor_thorough.json, not vendor_thorough_but_pricey.json) match what
test_sample_fixtures.py expects. generate_samples.py imports this dict — never
derives filenames via persona.replace("-", "_").
"""

from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate

from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import MessSpecItem, VendorResponse

# Authoritative persona -> output filename map (D-09/D-13).
# Imported by generate_samples.py and mirrored (as a local constant) in
# test_sample_fixtures.py for test path resolution.
FIXTURE_FILENAMES: dict[str, str] = {
    "thorough-but-pricey": "vendor_thorough.json",
    "cheap-but-incomplete": "vendor_cheap.json",
    "polished-fluff": "vendor_fluff.json",
}

# Hand-authored mess specs (D-09) — typed MessSpecItem instances so the TS
# contract stays accurate and test assertions can target specific issue types.
MESS_SPECS: dict[str, list[MessSpecItem]] = {
    "thorough-but-pricey": [
        MessSpecItem(
            line_item="strategy-creative + tvc-development",
            issue_type="bundled_scope",
            instruction=(
                "Bundle 'Strategy & Creative Development' and 'TVC Development' into a single "
                "'Integrated Creative Programme' fee. Mention both line items by name, but "
                "refuse to split the fee. Use language like: 'We offer this as a comprehensive "
                "package — we do not provide separate line-item pricing for creative and "
                "development as they are deeply integrated.'"
            ),
        ),
        MessSpecItem(
            line_item="paid-media-planning + paid-media-buying",
            issue_type="bundled_scope",
            instruction=(
                "Bundle 'Paid Media Planning' and 'Paid Media Buying' into a single 'Integrated "
                "Media Management' fee described as an all-inclusive package. Quote a single "
                "monthly retainer that covers both. Do not break out the planning vs buying cost."
            ),
        ),
        MessSpecItem(
            line_item="launch-management",
            issue_type="unclear_tax_and_currency",
            instruction=(
                "Quote the Launch Program Management fee without clarifying whether it is "
                "inclusive or exclusive of taxes. Use: 'plus applicable statutory taxes and "
                "levies'. Do not specify whether the base is USD or 'local currency equivalent'."
            ),
        ),
        MessSpecItem(
            line_item="tvc-production",
            issue_type="marketing_fluff",
            instruction=(
                "Describe TVC Production capability using award-winning and world-class language "
                "without citing specific awards, metrics, or named client references. E.g.: "
                "'Our award-winning production team has delivered world-class TVC content for "
                "leading FMCG brands, consistently exceeding client expectations with "
                "best-in-class production quality.'"
            ),
        ),
    ],
    "cheap-but-incomplete": [
        MessSpecItem(
            line_item="tvc-production",
            issue_type="missing_line_item",
            instruction=(
                "Do NOT price or address TVC Production. Do not acknowledge the omission. "
                "Write as if the proposal is complete and the service is simply not offered."
            ),
        ),
        MessSpecItem(
            line_item="kids-compliance",
            issue_type="missing_line_item",
            instruction=(
                "Do NOT price or address Kids Advertising & Claims Compliance. "
                "Do not acknowledge the omission. Omit this line item entirely from the proposal."
            ),
        ),
        MessSpecItem(
            line_item="paid-media-buying",
            issue_type="missing_line_item",
            instruction=(
                "Leave the fee for Paid Media Buying as TBD. Write explicitly: "
                "'Paid Media Buying: TBD — we would need to understand your media budget "
                "before quoting. Happy to discuss in a follow-up call.' Do not provide a price."
            ),
        ),
        MessSpecItem(
            line_item="social-organic",
            issue_type="vague_timeline",
            instruction=(
                "Give the Social Organic Content timeline as 'Q1 2027, subject to your "
                "go-ahead and sign-off on the content calendar' — not a specific week count."
            ),
        ),
        MessSpecItem(
            line_item="kids-compliance",
            issue_type="weak_compliance_claim",
            instruction=(
                "If mentioning compliance at all, use only: 'We are well-versed in all "
                "relevant industry regulations and have extensive experience working in "
                "compliance-sensitive categories.' No named regulation, no process detail, "
                "no certification."
            ),
        ),
    ],
    "polished-fluff": [
        MessSpecItem(
            line_item="launch-management",
            issue_type="internal_conflict",
            instruction=(
                "State the project end date / duration for Launch Program Management as "
                "'6 weeks post-launch' in the Executive Summary or Overview section, then "
                "state '18 weeks from kick-off' in the detailed Timeline section. "
                "Do not reconcile the two figures."
            ),
        ),
        MessSpecItem(
            line_item="tvc-production",
            issue_type="internal_conflict",
            instruction=(
                "State the TVC Production timeline as '8 weeks' in the Approach section, "
                "then reference '14 weeks' in the Delivery Timeline section for the same "
                "scope. Present both figures without flagging the discrepancy."
            ),
        ),
        MessSpecItem(
            line_item="strategy-creative",
            issue_type="marketing_fluff",
            instruction=(
                "Describe the strategy offering using: 'Our proprietary SPARK™ framework "
                "has delivered award-winning campaigns for world-class brands. We bring "
                "proven methodologies and best-in-class strategic thinking.' "
                "No specific awards, no named clients, no metrics."
            ),
        ),
        MessSpecItem(
            line_item="kids-compliance",
            issue_type="weak_compliance_claim",
            instruction=(
                "Address compliance with: 'We are fully aligned with all relevant regulations "
                "governing children's advertising and follow industry best practices across all "
                "jurisdictions.' No named regulation (not COPPA, not CARU, not CAP/BCAP). "
                "No certification. No process."
            ),
        ),
        MessSpecItem(
            line_item="paid-media-planning",
            issue_type="partial_scope",
            instruction=(
                "Address Paid Media Planning but only describe TV and digital channels. "
                "Do not mention OOH (Out-of-Home) media planning — omit it without flagging "
                "the gap. Write as if the plan is complete."
            ),
        ),
    ],
}

# Format label per persona (D-12: format diversity stresses the extraction agent).
FORMAT_LABELS: dict[str, str] = {
    "thorough-but-pricey": "tabular_proposal",
    "cheap-but-incomplete": "letter_email",
    "polished-fluff": "deck_bullets",
}

assert FIXTURE_FILENAMES.keys() == MESS_SPECS.keys() == FORMAT_LABELS.keys(), (
    "persona dicts (FIXTURE_FILENAMES, MESS_SPECS, FORMAT_LABELS) must share identical keys"
)


def generate_vendor_response(
    rfq_text: str,
    persona: str,
    mess_spec: list[MessSpecItem],
) -> VendorResponse:
    """Generate a messy vendor response for the given persona.

    Single LangChain call (D-08: one-pass generation, not clean-then-vandalize).
    The vendor-gen prompt instructs the model to inject all mess_spec flaws
    during generation — not as a post-processing step.

    Args:
        rfq_text: The RFQ as a Markdown string (rfq_gen.render_rfq_md() output).
        persona: One of "thorough-but-pricey", "cheap-but-incomplete", "polished-fluff".
        mess_spec: List of MessSpecItem instances specifying deliberate flaws.

    Returns:
        A VendorResponse with raw_text containing the messy proposal prose.
    """
    post = load("vendor-gen")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", post.content),
            ("human", "Generate the vendor response now."),
        ]
    )
    llm = get_llm("reasoning")

    # Serialize to JSON so the LLM prompt receives valid JSON syntax (WR-04).
    # str() on a list[dict] produces Python repr (single-quoted keys, True/False) —
    # json.dumps guarantees double-quoted keys and json-native booleans.
    mess_spec_json = json.dumps([m.model_dump() for m in mess_spec], indent=2, ensure_ascii=False)

    chain = prompt | llm
    result = chain.invoke(
        {
            "rfq_text": rfq_text,
            "persona": persona,
            "mess_spec": mess_spec_json,
        }
    )
    raw_text: str = result.content

    return VendorResponse(
        vendor_name=persona,
        persona=persona,
        mess_spec=mess_spec,
        source_id=f"vendor_{FIXTURE_FILENAMES[persona].removesuffix('.json')}",
        format_label=FORMAT_LABELS[persona],
        raw_text=raw_text,
    )
