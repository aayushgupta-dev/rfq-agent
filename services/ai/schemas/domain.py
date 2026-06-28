"""
domain.py — Domain schemas: RFQ, VendorResponse, and supporting models (Phase 2).
Phase 3 (P3): ExtractionResult fleshed out with LineItemExtraction sub-model (D-01..D-05).
Phase 4 (P4): ComparisonResult family fleshed out — 15 models + 2 StrEnums.

RFQ is the structured procurement event — our own clean artifact, never grounded
against (D-11). Plain Python types only; no Field[T] wrappers.

VendorResponse carries raw messy text + provenance metadata (D-12). The extraction
agent reads raw_text and produces ExtractionResult; this schema does not pre-extract
any facts.

MessSpecItem is the typed mess-spec entry (D-08/D-09) — a hand-authored instruction
for the vendor-gen prompt describing one deliberate flaw to inject. list[dict] avoided
to keep the TS contract typed via pydantic2ts.

ComparisonResult is code-constructed from ComparisonDraft (the model's structured output
target). The draft/result split closes the "model authors reliability-critical surfaces"
BLOCKER (Review Fix 1+2, CLAUDE.md §2). ComparisonDimension(StrEnum) closes the
fail-open dimension key join (Review Fix 1). ClarificationSet lives here so it is in
the contract/drift-check scope (Review Fix 12).
"""
from __future__ import annotations

from enum import StrEnum

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
    # ponytail: Field[str] not Field[Decimal] — real vendor pricing uses ranges, currency
    # prefixes, and conditional text ("TBD", "USD 110,000 – 135,000") that Decimal rejects.
    # Plan 03-04 confirmed this in live runs. The gate is value-type-agnostic; str works.
    pricing: Field[str]  # vendor's stated price for this item; missing if not bid
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
    # ponytail: Field[str] not Field[Decimal] for total_price — live runs (Plan 03-04) showed models
    # return values like "USD 1.46M – 1.60M" (conflicting range) and "approximately USD 600,000"
    # which Decimal rejects. The gate is value-type-agnostic; str preserves the verbatim value.
    total_price: Field[str]  # D-02: stated grand total if separable; missing if bundled-only
    commercial_terms: Field[str]  # payment terms, milestones, discounts, conditions
    timeline: Field[str]  # delivery timeline / project schedule narrative
    compliance_points: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each compliance statement
    assumptions: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each vendor assumption
    exclusions: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each explicit exclusion
    risks: list[Field[str]] = pydantic_Field(default_factory=list)  # D-03: each identified risk


# ---------------------------------------------------------------------------
# Phase 4: Comparison-level types (D-01..D-11)
# ---------------------------------------------------------------------------


class ComparabilityVerdict(StrEnum):
    """Comparison-level verdict — NOT a field-level FlagStatus (D-02).

    Lives in domain.py, never in envelope.py. Three states cover the badge matrix:
    comparable (all contributing fields present + grounded),
    partially (unclear/conflicting on any contributing field),
    not_comparable (missing/unsupported on any contributing field).

    Resolves WR-01 carry-forward: not_comparable is comparison-level, not a FlagStatus member.
    """

    comparable = "comparable"
    partially = "partially"
    not_comparable = "not_comparable"


class ComparisonDimension(StrEnum):
    """Typed enum for the 6 comparison dimensions (Review Fix 1).

    # ponytail: typed enum prevents the free-str dimension key join that would let a
    # mis-cased model-returned dimension name (e.g. 'Commercial') bypass the clamp.
    # Wave 3 _apply_verdict_clamp coerces to this StrEnum, defaults unknown to
    # not_comparable (fail-closed). (Review Fix 1, D-03)
    """

    technical = "technical"
    commercial = "commercial"
    scope = "scope"
    timeline = "timeline"
    compliance = "compliance"
    risk = "risk"


class ClampEntry(BaseModel):
    """One verdict downgrade record — mirrors DowngradeEntry from grounding/report.py.

    Captures the verdict before and after code clamping so the D-11 trace diff
    shows exactly where the model was overruled.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    dimension: str
    model_proposed: str
    code_ceiling: str
    clamped_to: str
    ceiling_reason: str  # e.g. "line_items[2].pricing.status = missing"


class ClampReport(BaseModel):
    """Full collection of clamp entries for one comparison run.

    # ponytail: mirrors DowngradeReport from grounding/report.py — same
    # code-authority-over-model pattern at the comparison level (D-03/D-11).
    Rides the ComparisonResult payload; feeds the Phase 5 in-app trace viewer.
    """

    model_config = ConfigDict(extra="forbid")

    entries: list[ClampEntry] = pydantic_Field(default_factory=list)

    @property
    def has_downgrades(self) -> bool:
        return len(self.entries) > 0


class DimensionVerdictDraft(BaseModel):
    """Model-emitted draft verdict for one vendor on one dimension.

    Carries model_proposed (required — D-11 trace diff) and buyer-facing reason text.
    Code constructs DimensionVerdict from this after clamping.
    Per Review Fix 1+2: model proposes; code guards.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    model_proposed: ComparabilityVerdict
    reason: str


class DimensionComparisonDraft(BaseModel):
    """Model-emitted one-row draft for one dimension (Review Fix 1+2).

    dimension is str here — model emits a string value; Wave 3 _apply_verdict_clamp
    coerces to ComparisonDimension(StrEnum) and fails closed on unrecognized values.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: str  # model emits str; Wave 3 _apply_verdict_clamp coerces to ComparisonDimension — fails closed (Review Fix 1)
    verdicts: list[DimensionVerdictDraft]
    narrative: str


class ComparisonDraft(BaseModel):
    """Model-emitted draft. THE MODEL'S STRUCTURED OUTPUT TARGET (Review Fix 1+2 BLOCKER).

    The model proposes per-dimension verdicts and phrasing ONLY. Code constructs
    ComparisonResult from this draft — the offer table, vendor_readiness,
    attention_points, clarification_questions, and clamp_report are ALL CODE-BUILT,
    never model-authored. Wave 3 uses .with_structured_output(ComparisonDraft,
    method='json_schema', include_raw=True). (CLAUDE.md §2 / D-03 / Review Fix 1+2)
    """

    model_config = ConfigDict(extra="forbid")

    dimensions: list[DimensionComparisonDraft]
    narrative_summary: str | None = None


class DimensionVerdict(BaseModel):
    """CODE-CONSTRUCTED per-vendor verdict cell in the badge matrix (D-01).

    model_proposed is kept alongside the clamped verdict for the D-11 trace diff —
    the "code disproves the model" proof at the comparison level.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    verdict: ComparabilityVerdict
    reason: str
    model_proposed: ComparabilityVerdict  # pre-clamp verdict — kept for the D-11 trace diff (D-11)


class DimensionComparison(BaseModel):
    """CODE-CONSTRUCTED one row of the badge matrix (D-01/D-06).

    dimension is ComparisonDimension (typed StrEnum), enforced at construction time
    by Wave 3 code that coerces from the model-emitted string.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: ComparisonDimension
    verdicts: list[DimensionVerdict]
    narrative: str


class LineItemOffer(BaseModel):
    """One cell of the 8×vendor offer table (D-06).

    Code-built from ExtractionResult.line_items[*] verbatim values.
    Never model-authored. (Review Fix 6 / D-05)
    """

    model_config = ConfigDict(extra="forbid")

    line_item_id: str
    line_item_name: str
    vendor_name: str
    pricing_verbatim: str | None = None
    pricing_status: str
    scope_verbatim: str | None = None
    scope_status: str
    non_equivalence_flag: str | None = None  # e.g. 'bundled — not separable', 'quoted EUR vs USD'


class VendorReadiness(BaseModel):
    """Code-built per-vendor qualitative readiness summary (D-07).

    Never model-authored. comparable_count and total_dimensions are framed as a
    data-readiness indicator — equal weights, never sorted (§24 leaderboard guardrail).

    # ponytail: no sort key, no rank field — D-07 guardrail. Vendors are never ordered
    # by this count. The list[VendorReadiness] on ComparisonResult preserves input order.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    comparable_count: int  # X of N dimensions currently comparable
    total_dimensions: int  # always 6
    descriptor: str  # e.g. "4 of 6 dimensions comparable; blocked on commercial, compliance"


class AttentionPoint(BaseModel):
    """One buyer attention point (D-08): code-triggered, model-phrased.

    Code detects the trigger condition; model only writes the buyer-facing summary.
    trigger_type is one of: 'comparability_blocker' | 'missing_pricing' |
    'cross_vendor_conflict' | 'compliance_gap' | 'clarification_generation_failed'
    (Review Fix 8 added clarification_generation_failed).
    """

    model_config = ConfigDict(extra="forbid")

    trigger_type: str  # 'comparability_blocker'|'missing_pricing'|'cross_vendor_conflict'|'compliance_gap'|'clarification_generation_failed'
    summary: str  # buyer-facing phrasing (model-authored for detected triggers)
    vendors_affected: list[str] = pydantic_Field(default_factory=list)
    dimension_or_field: str | None = None


class ClarificationQuestion(BaseModel):
    """One clarification question per flagged field (D-09/D-10).

    model-phrased, code-seeded. Generic questions ("please clarify pricing") are
    rejected by the clarification.v1.md prompt — each question must name vendor,
    line item, and exact ambiguity.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    field_path: str  # e.g. "line_items[2].pricing"
    flag_status: str  # the triggering FlagStatus value
    question: str
    why_needed: str


class ClarificationSet(BaseModel):
    """Model-emitted clarification output wrapper (Review Fix 12).

    Moved to domain.py so it is in the contract/drift-check scope (pydantic2ts picks
    it up). Code validates question count + identity against _collect_flagged_fields
    before accepting. The model receives only the code-collected flagged field list —
    it cannot add questions for fields not in that list.
    """

    model_config = ConfigDict(extra="forbid")

    questions: list[ClarificationQuestion] = pydantic_Field(default_factory=list)


class FlaggedField(BaseModel):
    """Code-collected flagged field entry passed to the clarification prompt (D-09).

    Never model-generated — always produced by _collect_flagged_fields(). The model
    receives this list as structured input and phrases one question per item.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_name: str
    field_path: str
    flag_status: str
    field_context: str | None = None


class ComparisonResult(BaseModel):
    """Full comparison output — code-constructed from ComparisonDraft + code-built surfaces.

    This is NEVER the model's structured output target — use ComparisonDraft for that.
    Replaces the Phase 4 stub (D-01..D-07 / Review Fix 1+2).

    vendor_names: input order preserved, never sorted (D-07).
    dimensions: 6 entries, one per dimension; code-clamped (Review Fix 1).
    line_item_offers: code-built from ExtractionResult (Review Fix 6).
    vendor_readiness: N entries, input order preserved, never sorted (D-07).
    attention_points: code-triggered shells, model-phrased text (Review Fix 7).
    clarification_questions: validated against _collect_flagged_fields (Review Fix 8).
    clamp_report: rides the result payload for D-11 trace + Phase 5 trace viewer.
    """

    model_config = ConfigDict(extra="forbid")

    vendor_names: list[str]  # input order preserved, never sorted (D-07)
    dimensions: list[DimensionComparison]  # 6 entries, one per dimension; code-clamped
    line_item_offers: list[LineItemOffer] = pydantic_Field(default_factory=list)  # code-built from ExtractionResult (Review Fix 6)
    vendor_readiness: list[VendorReadiness] = pydantic_Field(default_factory=list)  # code-built; N entries, input order
    attention_points: list[AttentionPoint] = pydantic_Field(default_factory=list)  # code-triggered shells (Review Fix 7)
    clarification_questions: list[ClarificationQuestion] = pydantic_Field(default_factory=list)  # validated against _collect_flagged_fields (Review Fix 8)
    clamp_report: ClampReport  # rides the result payload; D-11 trace + Phase 5 trace viewer
