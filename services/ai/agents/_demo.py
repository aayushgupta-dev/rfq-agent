"""
_demo.py — Trivial LangGraph graph that proves the SSE streaming spine (D-09, PLAT-04).

Emits the full EVENT_TYPES taxonomy in order:
  status -> partial -> result
followed by a final "done" appended by the FastAPI route.

This graph makes NO model calls — it exists only to prove the streaming
infrastructure. A real agent (extraction, comparison) reuses this pattern.

The emitted type values are asserted against schemas.events.EVENT_TYPES at node
runtime so the demo cannot drift from the closed taxonomy defined in Plan 02.

# ponytail: kept as a single node emitting three events — splitting into
# multiple nodes adds latency and complexity with no observability benefit
# for a streaming-spine proof.
"""

from __future__ import annotations

from typing import Any

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

# Import the canonical taxonomy so this module cannot drift from it.
from schemas.events import EVENT_TYPES


def _demo_node(state: dict[str, Any]) -> dict[str, Any]:
    """Single node that emits status -> partial -> result events via the stream writer."""
    w = get_stream_writer()

    # Couple emitted events to the canonical taxonomy: a rename/removal in
    # EVENT_TYPES fails here, not silently downstream.
    assert {"status", "partial", "result"} <= set(EVENT_TYPES)

    # Emit status first (the phase/progress signal)
    w({"type": "status", "payload": {"message": "Demo graph running", "phase": "demo"}})

    # Emit partial (an incremental structured chunk — simulated)
    w({"type": "partial", "payload": {"field": "demo_field", "value": "partial content"}})

    # Emit result (the final validated object from this graph)
    w({"type": "result", "payload": {"demo": True, "summary": "SSE spine proof complete"}})

    return {}


# Build the graph: START -> _demo_node -> END
_builder = StateGraph(dict)
_builder.add_node("demo", _demo_node)
_builder.add_edge(START, "demo")
_builder.add_edge("demo", END)

# Compiled graph — imported and used by api/app.py
demo_graph = _builder.compile()
