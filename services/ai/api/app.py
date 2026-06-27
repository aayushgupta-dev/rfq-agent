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

Security: verify_access() never logs the API key (T-03-01 mitigation).
No CORS or proxy-buffering config — deferred to Phase 5 (SHIP-01).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sse_starlette import EventSourceResponse

from agents._demo import demo_graph
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
