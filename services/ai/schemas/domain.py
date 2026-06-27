"""
domain.py — Domain schemas: RFQ, VendorResponse, and supporting models (Phase 2).
Phase 3 (P3): ExtractionResult fleshed out with LineItemExtraction sub-model (D-01..D-05).

RFQ is the structured procurement event — our own clean artifact, never grounded
against (D-11). Plain Python types only; no Field[T] wrappers.

VendorResponse carries raw messy text + provenance metadata (D-12). The extraction
agent reads raw_text and produces ExtractionResult; this schema does not pre-extract
any facts.

MessSpecItem is the typed mess-spec entry (D-08/D-09) — a hand-authored instruction
for the vendor-gen prompt describing one deliberate flaw to inject. list[dict] avoided
to keep the TS contract typed via pydantic2ts.

ComparisonResult remains a Phase 4 stub.
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


class LineItemExtraction(BaseModel):
    """Per-RFQ-line-item extraction — pricing and scope coverage for one service item (D-01).

    line_item_id and line_item_name are copied from RFQ context at extraction time.
    # ponytail: line_item_id and line_item_name are copied from RFQ context at extraction time,
    # not extracted from vendor text — they are scaffold/provenance, not grounded facts.
    """

    model_config = ConfigDict(extra="forbid")

    line_item_id: str  # matches RFQ.line_items[*].id — provenance, not grounded
    line_item_name: str  # matches RFQ.line_items[*].name — provenance, not grounded
    pricing: Field[Decimal]  # vendor's stated price for this item; missing if not bid
    scope_coverage: Field[str]  # what the vendor covers for this item; missing if not bid


class ExtractionResult(BaseModel):
    """Structured extraction for one vendor response (Phase 3 — D-01..D-05).

    vendor_name is plain str (D-05): provenance metadata from VendorResponse, not an
    extracted claim — grounding a known name against raw_text could spuriously fail.

    All multi-claim categories use list[Field[T]] for per-claim grounding (D-03).
    No dict[str, Field] shapes — only list[BaseModel] and list[Field[T]] (D-04).
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str  # D-05: provenance metadata — NOT a grounded Field
    scope_summary: Field[str]  # doc-level narrative summary of what vendor is offering
    line_items: list[LineItemExtraction] = pydantic_Field(default_factory=list)  # D-01: one entry per RFQ line item
    pricing_structure: Field[str]  # D-02: verbatim bundle/grand total statement; unclear if not stated
    total_price: Field[Decimal]  # D-02: stated grand total if separable; missing if bundled-only
    # ponytail: Field[Decimal] for total_price — if with_structured_output(method="json_schema")
    # produces schema friction during Plan 03 (model fills it inconsistently or parse errors occur),
    # downgrade to Field[str] here; the gate is value-type-agnostic. Check by running:
    # python -c "from schemas.domain import ExtractionResult; print('ok')" after Plan 03 wires the chain.
    commercial_terms: Field[str]  # payment terms, milestones, discounts, conditions
    timeline: Field[str]  # delivery timeline / project schedule narrative
    compliance_points: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each compliance statement
    assumptions: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each vendor assumption
    exclusions: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each explicit exclusion
    risks: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each identified risk


class ComparisonResult(BaseModel):
    """Side-by-side vendor comparison output (stub — full fields in Phase 4).

    # ponytail: P4 placeholder — real fields (technical / commercial / scope /
    # timeline / compliance / risk dimensions, comparability signal, buyer
    # attention points, clarification questions) land in Phase 4 (comparison agent).
    """

    model_config = ConfigDict(extra="forbid")

    vendor_count: Field[int] = Field[int](status="missing")  # type: ignore[call-arg]
    comparable: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]
