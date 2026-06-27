"""
schemas — foundational contract primitives for the Bid Desk AI service.

Re-exports all public types so `pydantic2ts --module schemas` discovers them
and the rest of the service can import from one place.
"""
from schemas.domain import RFQ, ComparisonResult, ExtractionResult, VendorResponse
from schemas.envelope import (
    ConflictingValue,
    Evidence,
    Field,
    FlagStatus,
)
from schemas.events import EVENT_TYPES, ErrorPayload, EventEnvelope

__all__ = [
    # Envelope primitives
    "FlagStatus",
    "Evidence",
    "ConflictingValue",
    "Field",
    # SSE events
    "EVENT_TYPES",
    "ErrorPayload",
    "EventEnvelope",
    # Domain stubs
    "RFQ",
    "VendorResponse",
    "ExtractionResult",
    "ComparisonResult",
]
