"""
domain.py — Domain schemas: RFQ, VendorResponse, and supporting models (Phase 2).

RFQ is the structured procurement event — our own clean artifact, never grounded
against (D-11). Plain Python types only; no Field[T] wrappers.

VendorResponse carries raw messy text + provenance metadata (D-12). The extraction
agent reads raw_text and produces ExtractionResult; this schema does not pre-extract
any facts.

MessSpecItem is the typed mess-spec entry (D-08/D-09) — a hand-authored instruction
for the vendor-gen prompt describing one deliberate flaw to inject. list[dict] avoided
to keep the TS contract typed via pydantic2ts.

ExtractionResult and ComparisonResult remain Phase 3/4 stubs (unchanged from Phase 1).

# ponytail: ExtractionResult/ComparisonResult stay as P3/P4 contract placeholders —
# the Field[T] stubs prove codegen monomorphizes FieldStr/FieldDecimal/FieldInt and
# establish the absence-envelope contract before the agents that fill them exist (D-08).
# The `# type: ignore[call-arg]` on stub fields is scoped to placeholder construction
# only — real P3/P4 fields are populated by validated agent output, not inline stubs.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as pydantic_Field

from schemas.envelope import Field


class MessSpecItem(BaseModel):
    """Typed mess-spec entry (D-08/D-09).

    list[dict] avoided — keeps the TS contract typed and the generated
    shared-types accurate. Each entry instructs the vendor-gen prompt to inject
    one deliberate flaw into a specific line item.
    """

    model_config = ConfigDict(extra="forbid")

    line_item: str
    issue_type: str
    instruction: str


class LineItem(BaseModel):
    """One line item in the RFQ — a discrete service or deliverable category.

    budget_range_usd uses list[int] with a 2-element convention (min, max) instead
    of tuple[int, int] — OpenAI structured output does not support Python tuples
    in JSON schema (Pitfall 6 from RESEARCH.md).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    deliverables: list[str]
    timeline_weeks: int | None = None
    budget_range_usd: list[int] | None = None

    @model_validator(mode="after")
    def _validate_budget_range(self) -> "LineItem":
        if self.budget_range_usd is not None:
            if len(self.budget_range_usd) != 2:
                raise ValueError(
                    f"budget_range_usd must be a 2-element [min, max] list, "
                    f"got {len(self.budget_range_usd)} elements"
                )
            if self.budget_range_usd[0] > self.budget_range_usd[1]:
                raise ValueError(
                    f"budget_range_usd[0] must be <= budget_range_usd[1], "
                    f"got {self.budget_range_usd}"
                )
        return self


class RFQ(BaseModel):
    """Marketing-services Request for Quotation.

    Our own clean procurement artifact — plain Python types, no Field[T] wrappers
    (D-11). The rfq-gen prompt targets structured output against this schema.
    The 8-line-item requirement is enforced by test_rfq_fixture_valid(), not by a
    model_validator here — see plan 02-03 decision note.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    client_name: str
    issue_date: str
    response_deadline: str
    scope_summary: str
    line_items: list[LineItem]
    commercial_expectations: str
    questionnaire: list[str] = pydantic_Field(default_factory=list)
    compliance_requirements: list[str] = pydantic_Field(default_factory=list)
    budget_total_usd: int | None = None


class VendorResponse(BaseModel):
    """A single vendor's response to the RFQ — raw text + provenance (D-12).

    raw_text is the vendor's messy prose document exactly as generated (or
    uploaded). mess_spec is the typed list[MessSpecItem] so the TS contract
    stays accurate. The extraction agent reads raw_text and produces
    ExtractionResult — no pre-extracted fields live here.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    persona: str
    mess_spec: list[MessSpecItem] = pydantic_Field(default_factory=list)
    source_id: str
    format_label: str
    raw_text: str


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
