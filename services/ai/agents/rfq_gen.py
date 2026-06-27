"""
rfq_gen.py — RFQ generation agent for the Bid Desk AI service.

Single structured LangChain call — no LangGraph (D-11: RFQ is our own clean
artifact; one-pass structured output is sufficient, no state machine needed).

generate_rfq() calls the rfq-gen prompt with the "reasoning" tier model and
returns a validated RFQ instance using with_structured_output(RFQ).

render_rfq_md() formats a validated RFQ as readable Markdown for use as
input context to vendor_gen. Pure string formatting — no LLM call.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import RFQ


def generate_rfq() -> RFQ:
    """Generate a marketing-services RFQ via the rfq-gen prompt.

    Uses the "reasoning" tier model (gpt-5.4) with structured output targeting
    the RFQ pydantic schema. Single LangChain chain — no LangGraph.

    Returns:
        A validated RFQ instance with 8 line items.
    """
    post = load("rfq-gen")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", post.content),
            ("human", "Generate the RFQ now."),
        ]
    )
    llm = get_llm("reasoning").with_structured_output(RFQ, method="json_schema")
    chain = prompt | llm
    result = chain.invoke({})
    # with_structured_output returns a validated pydantic instance directly
    assert isinstance(result, RFQ), f"Expected RFQ, got {type(result)}"
    return result


def render_rfq_md(rfq: RFQ) -> str:
    """Render a validated RFQ as a readable Markdown document.

    Pure string formatting — no LLM call. The output is used as rfq_text
    input to vendor_gen so all vendors respond to the same procurement event.

    Args:
        rfq: A validated RFQ instance.

    Returns:
        A Markdown string representing the RFQ.
    """
    lines: list[str] = []
    lines.append(f"# {rfq.title}")
    lines.append("")
    lines.append(f"**Client:** {rfq.client_name}")
    lines.append(f"**Issue Date:** {rfq.issue_date}")
    lines.append(f"**Response Deadline:** {rfq.response_deadline}")
    if rfq.budget_total_usd is not None:
        lines.append(f"**Total Budget (USD):** ${rfq.budget_total_usd:,}")
    lines.append("")
    lines.append("## Scope Summary")
    lines.append("")
    lines.append(rfq.scope_summary)
    lines.append("")
    lines.append("## Line Items")
    lines.append("")
    for item in rfq.line_items:
        lines.append(f"### {item.id}: {item.name}")
        lines.append("")
        lines.append(item.description)
        lines.append("")
        if item.deliverables:
            lines.append("**Deliverables:**")
            for d in item.deliverables:
                lines.append(f"- {d}")
            lines.append("")
        if item.timeline_weeks is not None:
            lines.append(f"**Timeline:** {item.timeline_weeks} weeks")
        if item.budget_range_usd is not None and len(item.budget_range_usd) == 2:
            lo, hi = item.budget_range_usd
            lines.append(f"**Budget Range (USD):** ${lo:,} – ${hi:,}")
        lines.append("")
    lines.append("## Commercial Expectations")
    lines.append("")
    lines.append(rfq.commercial_expectations)
    lines.append("")
    if rfq.questionnaire:
        lines.append("## Vendor Questionnaire")
        lines.append("")
        for i, q in enumerate(rfq.questionnaire, 1):
            lines.append(f"{i}. {q}")
        lines.append("")
    if rfq.compliance_requirements:
        lines.append("## Compliance Requirements")
        lines.append("")
        for req in rfq.compliance_requirements:
            lines.append(f"- {req}")
        lines.append("")
    return "\n".join(lines)
