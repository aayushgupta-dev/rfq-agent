"""
test_sse_demo.py — Unit tests for the FastAPI SSE demo route and LangGraph demo graph.

# TestClient instantiated without context manager to skip lifespan (startup access
# check) — no live key required for unit tests. Run uvicorn directly to exercise
# the startup gate (D-16 second half).

Tests cover:
  - GET /stream/demo emits a valid sequence of SSE events
  - Events arrive in the correct taxonomy order: status -> partial -> result -> done
  - Every event has exactly the keys "type" and "payload"
  - Every emitted "type" value is a member of EVENT_TYPES (closed taxonomy)
  - No "No access" false-negatives are possible (unit tests never touch OpenAI)

SSE taxonomy validation against EVENT_TYPES:
  Imported from schemas.events (Plan 02 is confirmed landed in this wave).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

# --- Import the FastAPI app --- #
# This import must NOT trigger the lifespan (startup access check).
# We use TestClient(app) without a context manager for all tests so the
# lifespan is not entered. The startup gate only fires on actual uvicorn boot.
from api.app import app

# EVENT_TYPES is the canonical closed SSE taxonomy from Plan 02.
# Imported directly so this test cannot drift from the schema definition.
from schemas.events import EVENT_TYPES


class TestSseDemoRoute:
    """GET /stream/demo — SSE event sequence, shape, and taxonomy tests."""

    def test_demo_route_returns_200(self) -> None:
        """GET /stream/demo must return HTTP 200."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        assert response.status_code == 200

    def test_demo_route_streams_events(self) -> None:
        """GET /stream/demo response body must contain SSE data lines."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        # SSE data lines start with "data: "
        assert "data: " in response.text

    def test_event_sequence_order(self) -> None:
        """Events must arrive in taxonomy order: status -> partial -> result -> done."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)

        assert len(events) >= 4, f"Expected at least 4 events, got {len(events)}: {events}"
        types = [e["type"] for e in events]
        assert types[0] == "status", f"First event must be 'status', got {types[0]!r}"
        assert types[-1] == "done", f"Last event must be 'done', got {types[-1]!r}"

    def test_all_events_have_type_and_payload(self) -> None:
        """Every SSE event must have exactly 'type' and 'payload' keys."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)

        for i, event in enumerate(events):
            assert "type" in event, f"Event {i} missing 'type' key: {event}"
            assert "payload" in event, f"Event {i} missing 'payload' key: {event}"

    def test_all_event_types_in_closed_taxonomy(self) -> None:
        """Every emitted 'type' value must be a member of EVENT_TYPES (schemas.events).

        This test is the SSE taxonomy drift-prevention check (MEDIUM review fix).
        If the demo graph emits a type not in the closed taxonomy, this test fails —
        the emitter cannot drift from EVENT_TYPES.
        """
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)

        for i, event in enumerate(events):
            assert event["type"] in EVENT_TYPES, (
                f"Event {i} type {event['type']!r} is not in EVENT_TYPES {EVENT_TYPES}. "
                "The SSE emitter has drifted from the closed taxonomy in schemas.events."
            )

    def test_status_event_precedes_partial(self) -> None:
        """A 'status' event must appear before any 'partial' event."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)
        types = [e["type"] for e in events]

        if "partial" in types:
            status_idx = types.index("status")
            partial_idx = types.index("partial")
            assert status_idx < partial_idx, (
                f"'status' (idx={status_idx}) must precede 'partial' (idx={partial_idx})"
            )

    def test_result_event_before_done(self) -> None:
        """A 'result' event must appear before the final 'done' event."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)
        types = [e["type"] for e in events]

        if "result" in types:
            result_idx = types.index("result")
            done_idx = types.index("done")
            assert result_idx < done_idx, (
                f"'result' (idx={result_idx}) must precede 'done' (idx={done_idx})"
            )

    def test_no_extra_keys_in_events(self) -> None:
        """Events must have exactly {type, payload} — no extra keys."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/stream/demo")
        events = _parse_sse_events(response.text)

        for i, event in enumerate(events):
            extra = set(event.keys()) - {"type", "payload"}
            assert not extra, f"Event {i} has extra keys {extra}: {event}"


def test_wire_rejects_event_outside_taxonomy() -> None:
    """The SSE emit path validates each chunk through EventEnvelope (WR-02).

    A node emitting a type outside the closed taxonomy must raise rather than
    stream the malformed event to the client.
    """
    from schemas.events import EventEnvelope

    with pytest.raises(ValidationError):
        EventEnvelope(type="frobnicate", payload={})


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE response body into a list of event dicts.

    SSE format: lines starting with "data: " followed by JSON.
    Blank lines separate events; non-data lines are ignored.
    """
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            payload_str = line[len("data: ") :]
            if payload_str:
                try:
                    event = json.loads(payload_str)
                    events.append(event)
                except json.JSONDecodeError as exc:
                    pytest.fail(f"SSE event is not valid JSON: {payload_str!r} — {exc}")
    return events
