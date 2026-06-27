"""
domain.py — Minimal compiling domain schema stubs (D-08).

RFQ, VendorResponse, ExtractionResult, and ComparisonResult are defined here
as the smallest stubs that:
  1. Compile cleanly with pydantic.
  2. Reference Field[T] across at least Field[str], Field[Decimal], and Field[int]
     so codegen monomorphizes FieldStr / FieldDecimal / FieldInt — proving D-05.
  3. Serve as the Phase 1 contract placeholder that P2/P3/P4 extend with real fields.

# ponytail: stub fields carry a comment marking them as the P2/P3/P4 contract
# placeholder. Kept-complexity is intentional — the contract precedes the agents
# that fill it (D-08).
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from schemas.envelope import Field


class RFQ(BaseModel):
    """Marketing-services Request for Quotation (stub — full fields in Phase 2).

    # ponytail: P2 placeholder — real fields (8 line items, scope, timelines,
    # commercials, questionnaire, compliance) land in Phase 2 (RFQ/vendor generation).
    """

    model_config = ConfigDict(extra="forbid")

    title: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
    budget_total: Field[Decimal] = Field[Decimal](status="missing")  # type: ignore[call-arg]


class VendorResponse(BaseModel):
    """A single vendor's response to the RFQ (stub — full fields in Phase 2).

    # ponytail: P2 placeholder — real fields (pricing structure, completeness,
    # scope, assumptions, timelines) land in Phase 2.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
    proposed_total: Field[Decimal] = Field[Decimal](status="missing")  # type: ignore[call-arg]
    response_completeness_score: Field[int] = Field[int](status="missing")  # type: ignore[call-arg]


class ExtractionResult(BaseModel):
    """Structured extraction for one vendor response (stub — full fields in Phase 3).

    # ponytail: P3 placeholder — real fields (scope, pricing breakdown, commercial
    # terms, timeline, compliance, assumptions, exclusions, risks + evidence spans
    # for each) land in Phase 3 (extraction agent).
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
    scope_summary: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
    total_price: Field[Decimal] = Field[Decimal](status="missing")  # type: ignore[call-arg]


class ComparisonResult(BaseModel):
    """Side-by-side vendor comparison output (stub — full fields in Phase 4).

    # ponytail: P4 placeholder — real fields (technical / commercial / scope /
    # timeline / compliance / risk dimensions, comparability signal, buyer
    # attention points, clarification questions) land in Phase 4 (comparison agent).
    """

    model_config = ConfigDict(extra="forbid")

    vendor_count: Field[int] = Field[int](status="missing")  # type: ignore[call-arg]
    comparable: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
