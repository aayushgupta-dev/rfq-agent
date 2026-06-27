"""
events.py — SSE event envelope with a closed event taxonomy (D-09, D-10).

Defines the complete canonical set of SSE event types for the Bid Desk streaming
pipeline. The EventEnvelope type is closed (Literal) — no downstream agent can
invent new event names without updating this module.

# ponytail: EVENT_TYPES constant exists so Plan 03 SSE emitter can validate its
# emitted events against this canonical source rather than duplicating the tuple.
# One source cannot drift from itself.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# Canonical closed taxonomy for SSE event types (D-09).
# The Literal values in EventEnvelope.type MUST match this tuple exactly.
EVENT_TYPES: tuple[str, ...] = ("status", "partial", "result", "error", "done")


class ErrorPayload(BaseModel):
    """Payload for the 'error' SSE event (D-10).

    Truncation (finish_reason: length), refusals, and agent failures all map
    to this in Phase 3. Defined here so the error contract is stable before
    any agent emits it.
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    recoverable: bool


class EventEnvelope(BaseModel):
    """SSE event envelope — the typed wrapper for every streamed agent event (D-09).

    type is a closed Literal so the set of event names is enforced at schema
    validation time, not by convention. payload is typed as Any because
    per-agent payload shapes land in P3/P4 and this envelope is the structural
    wrapper only.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["status", "partial", "result", "error", "done"]
    payload: Any
