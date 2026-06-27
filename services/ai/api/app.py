"""
app.py — FastAPI application for the Bid Desk AI service.

Provides:
  - Lifespan startup gate: calls verify_access() on boot; aborts loudly with a
    clear error if the org/key lacks gpt-5.4 / gpt-5.4-mini access (D-16, LOCKED).
    Trade-off: a transient OpenAI outage prevents server start — correct behaviour
    for a graded prototype where access proof matters more than resilience. No bypass
    toggle (CLAUDE.md §2: no unrequested escape hatches).

  - GET /stream/demo: streams the trivial LangGraph demo graph as SSE events
    in {type, payload} format, observable via `curl -N` (PLAT-04).

  - GET /data/rfq: live-regenerate the marketing-services RFQ (DATA-04).

  - POST /data/vendor-gen: live-regenerate a vendor response for a given persona (DATA-04).
    Accepts optional rfq_text body parameter so callers can pass the same RFQ context
    to all vendors (ensuring a valid comparison). If rfq_text is omitted, a fresh RFQ
    is generated inline.

Security: verify_access() never logs the API key (T-03-01 mitigation).
POST /data/vendor-gen validates persona against MESS_SPECS keys before use (T-02-11).
No CORS or proxy-buffering config — deferred to Phase 5 (SHIP-01).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field as pydantic_Field, model_validator
from sse_starlette import EventSourceResponse

from agents._demo import demo_graph
from agents.extraction import extraction_graph
from agents.rfq_gen import generate_rfq, render_rfq_md
from agents.vendor_gen import MESS_SPECS, generate_vendor_response
from llm.factory import verify_access
from schemas.domain import RFQ, VendorResponse
from schemas.events import EventEnvelope


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan handler — calls verify_access() on boot (D-16).

    If verify_access() raises (access denied or param error), the exception
    propagates and uvicorn aborts startup with the clear failure message.
    This is the second half of D-16; the first half is scripts/verify_access.py.
    """
    verify_access()  # raises RuntimeError on missing access; aborts startup
    yield


app = FastAPI(title="Bid Desk AI", lifespan=lifespan)


class VendorGenRequest(BaseModel):
    """Request body for POST /data/vendor-gen (DATA-04)."""

    persona: str = pydantic_Field(max_length=64)
    rfq_text: str | None = pydantic_Field(default=None, max_length=200_000)


@app.get("/data/rfq")
async def get_rfq() -> dict:
    """Live-regenerate the marketing-services RFQ via rfq-gen prompt (DATA-04).

    Makes a live OpenAI call — not served from the committed fixture.
    Returns: JSON-serializable RFQ dict.
    """
    rfq = generate_rfq()
    return rfq.model_dump(mode="json")


@app.post("/data/vendor-gen")
async def post_vendor_gen(req: VendorGenRequest) -> dict:
    """Live-regenerate a vendor response for the given persona (DATA-04).

    req.persona: one of "thorough-but-pricey", "cheap-but-incomplete", "polished-fluff".
    req.rfq_text: optional RFQ Markdown text. If provided, all vendors see the same RFQ
                  (required for a valid comparison). If omitted, a fresh RFQ is generated.
    Returns: JSON-serializable VendorResponse dict.

    Security: persona is validated against MESS_SPECS keys before use (T-02-11).
    """
    if req.persona not in MESS_SPECS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona: {req.persona!r}. Must be one of {list(MESS_SPECS)}",
        )
    rfq_text = req.rfq_text
    if rfq_text is None:
        rfq = generate_rfq()
        rfq_text = render_rfq_md(rfq)
    vendor = generate_vendor_response(rfq_text, req.persona, MESS_SPECS[req.persona])
    return vendor.model_dump(mode="json")


class ExtractionRequest(BaseModel):
    """Request body for POST /extract/vendor (EXTRACT-03).

    vendor_response carries the full VendorResponse; rfq carries the full RFQ.

    # ponytail: max_length on nested str fields can't be enforced via
    # pydantic_Field (it only applies to direct str fields, not nested model
    # attributes), so a model_validator caps both the vendor raw_text and the
    # aggregate request size. The aggregate cap covers the RFQ free-text fields
    # (questionnaire, compliance_requirements, line-item descriptions/deliverables)
    # that an attacker could otherwise inflate independently of raw_text (W-R2).
    # This is an app-layer best-effort cap — the body is already deserialized by
    # the time it runs. The authoritative request-body size limit is server-level
    # (uvicorn --limit-* / reverse proxy) and is deferred to SHIP-01.
    """

    vendor_response: VendorResponse
    rfq: RFQ

    _MAX_RAW_TEXT = 200_000
    _MAX_TOTAL = 500_000

    @model_validator(mode="after")
    def _check_payload_size(self) -> "ExtractionRequest":
        if len(self.vendor_response.raw_text) > self._MAX_RAW_TEXT:
            raise ValueError(
                f"vendor_response.raw_text exceeds {self._MAX_RAW_TEXT:,} chars "
                f"(got {len(self.vendor_response.raw_text)})"
            )
        total = len(self.model_dump_json())
        if total > self._MAX_TOTAL:
            raise ValueError(
                f"extraction request exceeds {self._MAX_TOTAL:,} chars total "
                f"(got {total}) — RFQ free-text included"
            )
        return self


@app.get("/stream/demo")
async def stream_demo() -> EventSourceResponse:
    """Stream the trivial LangGraph demo graph as SSE events (PLAT-04).

    Emits the full EVENT_TYPES taxonomy in order:
      data: {"type":"status","payload":{...}}
      data: {"type":"partial","payload":{...}}
      data: {"type":"result","payload":{...}}
      data: {"type":"done","payload":{}}

    Observable via: curl -N http://localhost:8000/stream/demo
    No model calls on this path — the demo graph emits hardcoded taxonomy events.
    """

    async def _generate() -> AsyncGenerator[dict, None]:
        # Validate every chunk through the closed envelope before serializing —
        # a malformed emit (unknown type, missing payload, extra keys) fails
        # loudly here rather than streaming unchecked to the client.
        async for chunk in demo_graph.astream({}, stream_mode="custom"):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        # Final "done" event appended by the route after the graph completes.
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}

    return EventSourceResponse(_generate())


@app.post("/extract/vendor")
async def extract_vendor(req: ExtractionRequest) -> EventSourceResponse:
    """Stream vendor extraction as SSE events (EXTRACT-03).

    Accepts a VendorResponse + RFQ, runs the extraction graph, and streams
    status -> result -> done events. All structured-output failure shapes emit
    a safe error event (B-R2). Grounding runs before the result event (D-07).
    """

    async def _generate() -> AsyncGenerator[dict, None]:
        async for chunk in extraction_graph.astream(
            {"vendor": req.vendor_response, "rfq": req.rfq},
            stream_mode="custom",
        ):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}

    return EventSourceResponse(_generate())
