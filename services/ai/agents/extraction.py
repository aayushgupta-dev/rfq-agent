"""
extraction.py — Extraction agent: LangGraph StateGraph that calls the model,
runs grounding, and emits SSE events (Phase 3, Plan 03-03).

The graph is the phase's central reliability artifact. Every structured-output
failure shape maps to a safe error event — truncation, refusal, parse errors,
unexpected types, and bare exceptions all produce SSE error events and return
early. No half-parsed object ever reaches the result path (B-R2).

Grounding (ground_model) runs BEFORE the result event is emitted (D-07), so
no ungrounded facts cross the SSE boundary.

Exported:
  extraction_graph                  — compiled LangGraph StateGraph
  run_extraction                    — sync testable wrapper (test/script use only)
  generate_extraction               — sync wrapper for script use (asyncio.run)
  generate_extraction_with_trace    — sync function for trace capture (D-14/D-15)

# ponytail: two-path failure detection because truncation raises but refusal
# silently populates additional_kwargs["refusal"]. include_raw=True used solely
# for refusal/parse-error inspection; truncation is caught as an exception before
# the raw output is inspected.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from openai import LengthFinishReasonError

from grounding.gate import ground_model
from grounding.report import DowngradeReport
from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import ExtractionResult, LineItemExtraction, RFQ, VendorResponse  # noqa: F401
from schemas.events import EVENT_TYPES, ErrorPayload

# ---------------------------------------------------------------------------
# Module-level chain (patched in tests)
# ---------------------------------------------------------------------------

_post = load("extraction")
# ponytail: SystemMessage object (not a ("system", content) tuple) prevents LangChain
# from parsing the prompt body as an f-string template — the extraction prompt
# contains JSON examples with {braces} that are NOT template variables.
_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=_post.content),
        (
            "human",
            "Vendor source ID (use this exact value for all evidence source_id fields): {source_id}\n\nVendor response:\n{vendor_text}\n\nRFQ line items (JSON):\n{rfq_line_items}",
        ),
    ]
)
# include_raw=True: inspect additional_kwargs["refusal"] and parsed/parsing_error
_llm_with_raw = get_llm("reasoning").with_structured_output(
    ExtractionResult, method="json_schema", include_raw=True
)
_chain = _prompt | _llm_with_raw


# ---------------------------------------------------------------------------
# Core node implementation (separated for testability)
# ---------------------------------------------------------------------------


def _run_extraction_impl(
    state: dict[str, Any],
    emit: Callable[[dict], None],
) -> dict[str, Any]:
    """Core extraction logic — separated so run_extraction can inject an emit collector.

    emit is called with every SSE event dict the node would normally write via
    get_stream_writer(). Production path uses get_stream_writer(); test path
    passes a list-appending lambda.

    # ponytail: split from _extraction_node so tests can patch _chain and
    # capture emitted events without needing a running LangGraph event loop.
    """
    # Taxonomy guard — a rename/removal in EVENT_TYPES fails here, not downstream.
    assert {"status", "result", "error"} <= set(EVENT_TYPES)

    vendor: VendorResponse = state["vendor"]
    rfq: RFQ = state["rfq"]

    rfq_json = json.dumps(
        [
            {"id": li.id, "name": li.name, "description": li.description}
            for li in rfq.line_items
        ]
    )

    emit(
        {
            "type": "status",
            "payload": {"message": "calling extraction model", "phase": "model"},
        }
    )

    # All structured-output failure shapes mapped to safe error events (B-R2).
    try:
        # --- TRUNCATION PATH ---
        # LengthFinishReasonError propagates uncaught through include_raw=True
        # wrapper (langchain-ai/langchain#29700). Catch it here before any
        # parse attempt.
        try:
            raw_output = _chain.invoke(
                {
                    "vendor_text": vendor.raw_text,
                    "rfq_line_items": rfq_json,
                    "source_id": vendor.source_id,
                }
            )
        except LengthFinishReasonError:
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="extraction_truncated",
                        message="Model output was truncated (finish_reason=length).",
                        recoverable=True,
                    ).model_dump(),
                }
            )
            return {"error": "truncated"}

        # --- REFUSAL PATH ---
        # Refusals surface in additional_kwargs["refusal"] on the raw AIMessage,
        # NOT as an exception. Do NOT key refusal off str(ValidationError) —
        # that conflates pydantic schema errors with model refusals (CLAUDE.md §2).
        raw_msg = raw_output["raw"]
        if raw_msg.additional_kwargs.get("refusal"):
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="extraction_refused",
                        message="Model refused to process the extraction request.",
                        recoverable=False,
                    ).model_dump(),
                }
            )
            return {"error": "refusal"}

        # --- PARSED=NONE / PARSING_ERROR PATH ---
        # ponytail: parsing_error fallback — guards against include_raw=True returning
        # {"parsed": None, "parsing_error": <exc>} when langchain-openai routes
        # truncation into parsing_error rather than raising LengthFinishReasonError in
        # some installed versions (open bug #29700/#25510 may be backported). Cover
        # both shapes: raise path AND parsing_error path.
        parsed = raw_output.get("parsed")
        parsing_error = raw_output.get("parsing_error")
        if parsed is None or parsing_error is not None:
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="extraction_parse_error",
                        message=f"Structured output parse failed: {parsing_error!r}",
                        recoverable=True,
                    ).model_dump(),
                }
            )
            return {"error": "parse_error"}

        # --- UNEXPECTED TYPE PATH ---
        if not isinstance(parsed, ExtractionResult):
            emit(
                {
                    "type": "error",
                    "payload": ErrorPayload(
                        code="extraction_unexpected_type",
                        message=f"Expected ExtractionResult, got {type(parsed).__name__}",
                        recoverable=False,
                    ).model_dump(),
                }
            )
            return {"error": "unexpected_type"}

    except Exception as exc:
        # Bare exception catch — any other failure maps to a safe error event.
        emit(
            {
                "type": "error",
                "payload": ErrorPayload(
                    code="extraction_error",
                    message=str(exc),
                    recoverable=False,
                ).model_dump(),
            }
        )
        return {"error": "extraction_error"}

    # --- SUCCESS PATH ---
    # Only reached after ALL failure shapes are ruled out.

    # W-R4: use model_copy(update=...) not attribute mutation — keeps immutability.
    raw: ExtractionResult = parsed.model_copy(update={"vendor_name": vendor.vendor_name})

    emit(
        {
            "type": "status",
            "payload": {"message": "running grounding gate", "phase": "grounding"},
        }
    )

    # D-07: ground_model runs BEFORE result event is emitted — no ungrounded facts
    # cross the SSE boundary.
    grounded, report = ground_model(raw, {vendor.source_id: vendor.raw_text})

    # ponytail: extraction fields inlined at payload top level so callers can access
    # payload["line_items"], payload["pricing_structure"], etc. directly.
    # downgrade_report is a sibling key — no key collision since ExtractionResult
    # has no field named "downgrade_report".
    result_event = {
        "type": "result",
        "payload": {
            **grounded.model_dump(mode="json"),
            "downgrade_report": report.model_dump(mode="json"),
        },
    }
    emit(result_event)

    return {"result": grounded, "report": report, "result_sse_event": result_event}


# ---------------------------------------------------------------------------
# LangGraph node (uses get_stream_writer for production SSE path)
# ---------------------------------------------------------------------------


def _extraction_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node: calls _run_extraction_impl with the production stream writer."""
    w = get_stream_writer()
    return _run_extraction_impl(state, w)


# ---------------------------------------------------------------------------
# Build and compile the graph
# ---------------------------------------------------------------------------


def _build_extraction_graph():  # noqa: ANN201
    builder = StateGraph(dict)
    builder.add_node("extract", _extraction_node)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", END)
    return builder.compile()


extraction_graph = _build_extraction_graph()


# ---------------------------------------------------------------------------
# Testable sync wrapper (test/script use only — not the production SSE path)
# ---------------------------------------------------------------------------


def run_extraction(
    vendor_response: VendorResponse,
    rfq: RFQ,
) -> dict[str, Any]:
    """Synchronous testable wrapper for the extraction node.

    Calls _run_extraction_impl directly (bypassing the LangGraph runtime) so
    tests can patch _chain and inspect emitted events without a running event loop.

    Returns the state dict from _run_extraction_impl, augmented with:
      last_sse_event  — the last event emitted (error or result)
      result_sse_event — the result event if one was emitted

    # ponytail: direct node invocation for testability — does NOT exercise
    # the LangGraph SSE streaming path. Production path uses
    # extraction_graph.astream(stream_mode="custom"). Use this only in tests
    # and scripts.
    """
    events: list[dict] = []

    def _collect(event: dict) -> None:
        events.append(event)

    state = _run_extraction_impl(
        {"vendor": vendor_response, "rfq": rfq},
        _collect,
    )

    # Attach event inspection helpers to the returned state dict.
    if events:
        state["last_sse_event"] = events[-1]
    # result_sse_event is set by _run_extraction_impl on the success path;
    # also check emitted events in case error path was taken.
    if "result_sse_event" not in state:
        result_events = [e for e in events if e.get("type") == "result"]
        if result_events:
            state["result_sse_event"] = result_events[-1]

    return state


# ---------------------------------------------------------------------------
# Script-level sync wrapper (asyncio.run — do not call from async context)
# ---------------------------------------------------------------------------


def generate_extraction(vendor_response: VendorResponse, rfq: RFQ) -> ExtractionResult:
    """Synchronous wrapper for script/CLI use only.

    # ponytail: sync wrapper for script/test use only — do NOT call from an
    # async context (asyncio.run raises RuntimeError if an event loop is already
    # running). Production SSE path uses extraction_graph.astream directly.
    # An async variant is available via extraction_graph.ainvoke for async callers.
    """
    result = asyncio.run(
        extraction_graph.ainvoke({"vendor": vendor_response, "rfq": rfq})
    )
    return result["result"]


# ---------------------------------------------------------------------------
# Trace capture surface (D-14/D-15) — the ONLY authorized trace capture path
# ---------------------------------------------------------------------------


def generate_extraction_with_trace(
    vendor_response: VendorResponse,
    rfq: RFQ,
) -> tuple[ExtractionResult, ExtractionResult, DowngradeReport]:
    """Capture raw (ungrounded) + grounded pair from the production chain.

    Returns (raw_ungrounded, grounded, report).

    Raises ValueError on any failure shape (refusal, parse error, unexpected type)
    so capture_traces.py knows the trace is unusable.

    This is the ONLY authorized trace-capture surface — Plan 04's capture_traces.py
    imports and calls this function. No local chain rebuilds elsewhere (D-14/D-15).

    # ponytail: exposes raw vs grounded pair from production chain for D-14 trace
    # capture; not used in the production SSE path.
    """
    rfq_json = json.dumps(
        [
            {"id": li.id, "name": li.name, "description": li.description}
            for li in rfq.line_items
        ]
    )

    try:
        raw_output = _chain.invoke(
            {
                "vendor_text": vendor_response.raw_text,
                "rfq_line_items": rfq_json,
                "source_id": vendor_response.source_id,
            }
        )
    except LengthFinishReasonError as exc:
        raise ValueError("Model output truncated — cannot capture trace") from exc

    # Apply same failure-shape checks as the node.
    raw_msg = raw_output["raw"]
    if raw_msg.additional_kwargs.get("refusal"):
        raise ValueError("Model refused extraction — cannot capture trace")

    parsed = raw_output.get("parsed")
    parsing_error = raw_output.get("parsing_error")
    if parsed is None or parsing_error is not None:
        raise ValueError(f"Structured output parse failed: {parsing_error!r}")

    if not isinstance(parsed, ExtractionResult):
        raise ValueError(f"Unexpected type: {type(parsed).__name__}")

    # W-R4: model_copy for immutability
    raw = parsed.model_copy(update={"vendor_name": vendor_response.vendor_name})
    grounded, report = ground_model(raw, {vendor_response.source_id: vendor_response.raw_text})
    return (raw, grounded, report)
