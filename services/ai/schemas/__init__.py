"""
schemas — foundational contract primitives for the Bid Desk AI service.

Re-exports all public types so `pydantic2ts --module schemas` discovers them
and the rest of the service can import from one place.
"""
from schemas.domain import (
    RFQ,
    AttentionPoint,
    ClampEntry,
    ClampReport,
    ClarificationQuestion,
    ClarificationSet,
    ComparabilityVerdict,
    ComparisonDimension,
    ComparisonDraft,
    ComparisonResult,
    DimensionComparison,
    DimensionComparisonDraft,
    DimensionVerdict,
    DimensionVerdictDraft,
    ExtractionResult,
    FlaggedField,
    LineItem,
    LineItemOffer,
    MessSpecItem,
    VendorReadiness,
    VendorResponse,
)
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
    # Domain — core
    "RFQ",
    "MessSpecItem",
    "LineItem",
    "VendorResponse",
    "ExtractionResult",
    # Domain — Phase 4 comparison family
    "ComparabilityVerdict",
    "ComparisonDimension",
    "ClampEntry",
    "ClampReport",
    "DimensionVerdictDraft",
    "DimensionComparisonDraft",
    "ComparisonDraft",
    "DimensionVerdict",
    "DimensionComparison",
    "LineItemOffer",
    "VendorReadiness",
    "AttentionPoint",
    "ClarificationQuestion",
    "ClarificationSet",
    "FlaggedField",
    "ComparisonResult",
]
