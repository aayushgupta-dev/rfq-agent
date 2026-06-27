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
from pydantic import BaseModel, Field as pydantic_Field
from sse_starlette import EventSourceResponse

from agents._demo import demo_graph
from agents.rfq_gen import generate_rfq, render_rfq_md
from agents.vendor_gen import MESS_SPECS, generate_vendor_response
from llm.factory import verify_access
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
