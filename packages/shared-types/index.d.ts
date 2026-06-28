/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * Comparison-level verdict — NOT a field-level FlagStatus (D-02).
 *
 * Lives in domain.py, never in envelope.py. Three states cover the badge matrix:
 * comparable (all contributing fields present + grounded),
 * partially (unclear/conflicting on any contributing field),
 * not_comparable (missing/unsupported on any contributing field).
 *
 * Resolves WR-01 carry-forward: not_comparable is comparison-level, not a FlagStatus member.
 */
export type ComparabilityVerdict = "comparable" | "partially" | "not_comparable";
/**
 * Typed enum for the 6 comparison dimensions (Review Fix 1).
 *
 * # ponytail: typed enum prevents the free-str dimension key join that would let a
 * # mis-cased model-returned dimension name (e.g. 'Commercial') bypass the clamp.
 * # Wave 3 _apply_verdict_clamp coerces to this StrEnum, defaults unknown to
 * # not_comparable (fail-closed). (Review Fix 1, D-03)
 */
export type ComparisonDimension = "technical" | "commercial" | "scope" | "timeline" | "compliance" | "risk";
/**
 * 5-state absence/confidence flag for every extracted field (D-07).
 *
 * Never collapses to blank — absence is first-class.
 */
export type FlagStatus = "present" | "missing" | "unclear" | "conflicting" | "unsupported";

/**
 * One buyer attention point (D-08): code-triggered, model-phrased.
 *
 * Code detects the trigger condition; model only writes the buyer-facing summary.
 * trigger_type is one of: 'comparability_blocker' | 'missing_pricing' |
 * 'cross_vendor_conflict' | 'compliance_gap' | 'clarification_generation_failed'
 * (Review Fix 8 added clarification_generation_failed).
 */
export interface AttentionPoint {
  trigger_type: string;
  summary: string;
  vendors_affected?: string[];
  dimension_or_field?: string | null;
}
/**
 * One verdict downgrade record — mirrors DowngradeEntry from grounding/report.py.
 *
 * Captures the verdict before and after code clamping so the D-11 trace diff
 * shows exactly where the model was overruled.
 */
export interface ClampEntry {
  vendor_name: string;
  dimension: string;
  model_proposed: string;
  code_ceiling: string;
  clamped_to: string;
  ceiling_reason: string;
}
/**
 * Full collection of clamp entries for one comparison run.
 *
 * # ponytail: mirrors DowngradeReport from grounding/report.py — same
 * # code-authority-over-model pattern at the comparison level (D-03/D-11).
 * Rides the ComparisonResult payload; feeds the Phase 5 in-app trace viewer.
 */
export interface ClampReport {
  entries?: ClampEntry[];
}
/**
 * One clarification question per flagged field (D-09/D-10).
 *
 * model-phrased, code-seeded. Generic questions ("please clarify pricing") are
 * rejected by the clarification.v1.md prompt — each question must name vendor,
 * line item, and exact ambiguity.
 */
export interface ClarificationQuestion {
  vendor_name: string;
  field_path: string;
  flag_status: string;
  question: string;
  why_needed: string;
}
/**
 * Model-emitted clarification output wrapper (Review Fix 12).
 *
 * Moved to domain.py so it is in the contract/drift-check scope (pydantic2ts picks
 * it up). Code validates question count + identity against _collect_flagged_fields
 * before accepting. The model receives only the code-collected flagged field list —
 * it cannot add questions for fields not in that list.
 */
export interface ClarificationSet {
  questions?: ClarificationQuestion[];
}
/**
 * Model-emitted draft. THE MODEL'S STRUCTURED OUTPUT TARGET (Review Fix 1+2 BLOCKER).
 *
 * The model proposes per-dimension verdicts and phrasing ONLY. Code constructs
 * ComparisonResult from this draft — the offer table, vendor_readiness,
 * attention_points, clarification_questions, and clamp_report are ALL CODE-BUILT,
 * never model-authored. Wave 3 uses .with_structured_output(ComparisonDraft,
 * method='json_schema', include_raw=True). (CLAUDE.md §2 / D-03 / Review Fix 1+2)
 */
export interface ComparisonDraft {
  dimensions: DimensionComparisonDraft[];
  narrative_summary?: string | null;
}
/**
 * Model-emitted one-row draft for one dimension (Review Fix 1+2).
 *
 * dimension is str here — model emits a string value; Wave 3 _apply_verdict_clamp
 * coerces to ComparisonDimension(StrEnum) and fails closed on unrecognized values.
 */
export interface DimensionComparisonDraft {
  dimension: string;
  verdicts: DimensionVerdictDraft[];
  narrative: string;
}
/**
 * Model-emitted draft verdict for one vendor on one dimension.
 *
 * Carries model_proposed (required — D-11 trace diff) and buyer-facing reason text.
 * Code constructs DimensionVerdict from this after clamping.
 * Per Review Fix 1+2: model proposes; code guards.
 */
export interface DimensionVerdictDraft {
  vendor_name: string;
  model_proposed: ComparabilityVerdict;
  reason: string;
}
/**
 * Full comparison output — code-constructed from ComparisonDraft + code-built surfaces.
 *
 * This is NEVER the model's structured output target — use ComparisonDraft for that.
 * Replaces the Phase 4 stub (D-01..D-07 / Review Fix 1+2).
 *
 * vendor_names: input order preserved, never sorted (D-07).
 * dimensions: 6 entries, one per dimension; code-clamped (Review Fix 1).
 * line_item_offers: code-built from ExtractionResult (Review Fix 6).
 * vendor_readiness: N entries, input order preserved, never sorted (D-07).
 * attention_points: code-triggered shells, model-phrased text (Review Fix 7).
 * clarification_questions: validated against _collect_flagged_fields (Review Fix 8).
 * clamp_report: rides the result payload for D-11 trace + Phase 5 trace viewer.
 */
export interface ComparisonResult {
  vendor_names: string[];
  dimensions: DimensionComparison[];
  line_item_offers?: LineItemOffer[];
  vendor_readiness?: VendorReadiness[];
  attention_points?: AttentionPoint[];
  clarification_questions?: ClarificationQuestion[];
  clamp_report: ClampReport;
}
/**
 * CODE-CONSTRUCTED one row of the badge matrix (D-01/D-06).
 *
 * dimension is ComparisonDimension (typed StrEnum), enforced at construction time
 * by Wave 3 code that coerces from the model-emitted string.
 */
export interface DimensionComparison {
  dimension: ComparisonDimension;
  verdicts: DimensionVerdict[];
  narrative: string;
}
/**
 * CODE-CONSTRUCTED per-vendor verdict cell in the badge matrix (D-01).
 *
 * model_proposed is kept alongside the clamped verdict for the D-11 trace diff —
 * the "code disproves the model" proof at the comparison level.
 */
export interface DimensionVerdict {
  vendor_name: string;
  verdict: ComparabilityVerdict;
  reason: string;
  model_proposed: ComparabilityVerdict;
}
/**
 * One cell of the 8×vendor offer table (D-06).
 *
 * Code-built from ExtractionResult.line_items[*] verbatim values.
 * Never model-authored. (Review Fix 6 / D-05)
 */
export interface LineItemOffer {
  line_item_id: string;
  line_item_name: string;
  vendor_name: string;
  pricing_verbatim?: string | null;
  pricing_status: string;
  scope_verbatim?: string | null;
  scope_status: string;
  non_equivalence_flag?: string | null;
}
/**
 * Code-built per-vendor qualitative readiness summary (D-07).
 *
 * Never model-authored. comparable_count and total_dimensions are framed as a
 * data-readiness indicator — equal weights, never sorted (§24 leaderboard guardrail).
 *
 * # ponytail: no sort key, no rank field — D-07 guardrail. Vendors are never ordered
 * # by this count. The list[VendorReadiness] on ComparisonResult preserves input order.
 */
export interface VendorReadiness {
  vendor_name: string;
  comparable_count: number;
  total_dimensions: number;
  descriptor: string;
}
/**
 * Payload for the 'error' SSE event (D-10).
 *
 * Truncation (finish_reason: length), refusals, and agent failures all map
 * to this in Phase 3. Defined here so the error contract is stable before
 * any agent emits it.
 */
export interface ErrorPayload {
  code: string;
  message: string;
  recoverable: boolean;
}
/**
 * SSE event envelope — the typed wrapper for every streamed agent event (D-09).
 *
 * type is a closed Literal so the set of event names is enforced at schema
 * validation time, not by convention. payload is typed as Any because
 * per-agent payload shapes land in P3/P4 and this envelope is the structural
 * wrapper only.
 */
export interface EventEnvelope {
  type: "status" | "partial" | "result" | "error" | "done";
  payload: unknown;
}
/**
 * Source grounding for a single extracted fact (D-04).
 *
 * Offsets are validated in code, never trusted from the model (CLAUDE.md §8).
 * Enforced: char_start >= 0 and char_end > char_start. Snippet-vs-source-text
 * matching (that the span actually exists in the vendor document) is a Phase 3
 * agent-level concern requiring the source text — not enforced here.
 */
export interface Evidence {
  snippet: string;
  char_start: number;
  char_end: number;
  source_id: string;
}
/**
 * Structured extraction for one vendor response (Phase 3 — D-01..D-05).
 *
 * vendor_name is plain str (D-05): provenance metadata from VendorResponse, not an
 * extracted claim — grounding a known name against raw_text could spuriously fail.
 *
 * All multi-claim categories use list[Field[T]] for per-claim grounding (D-03).
 * No dict[str, Field] shapes — only list[BaseModel] and list[Field[T]] (D-04).
 */
export interface ExtractionResult {
  vendor_name: string;
  scope_summary: FieldStr;
  line_items?: LineItemExtraction[];
  pricing_structure: FieldStr;
  total_price: FieldStr;
  commercial_terms: FieldStr;
  timeline: FieldStr;
  compliance_points?: FieldStr[];
  assumptions?: FieldStr[];
  exclusions?: FieldStr[];
  risks?: FieldStr[];
}
export interface FieldStr {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
}
export interface ConflictingValueStr {
  value?: string | null;
  evidence?: Evidence[];
}
/**
 * Per-RFQ-line-item extraction — pricing and scope coverage for one service item (D-01).
 *
 * line_item_id and line_item_name are copied from RFQ context at extraction time.
 * # ponytail: line_item_id and line_item_name are copied from RFQ context at extraction time,
 * # not extracted from vendor text — they are scaffold/provenance, not grounded facts.
 */
export interface LineItemExtraction {
  line_item_id: string;
  line_item_name: string;
  pricing: FieldStr;
  scope_coverage: FieldStr;
}
/**
 * Code-collected flagged field entry passed to the clarification prompt (D-09).
 *
 * Never model-generated — always produced by _collect_flagged_fields(). The model
 * receives this list as structured input and phrases one question per item.
 */
export interface FlaggedField {
  vendor_name: string;
  field_path: string;
  flag_status: string;
  field_context?: string | null;
}
/**
 * One line item in the RFQ — a discrete service or deliverable category.
 *
 * budget_range_usd uses list[int] with a 2-element convention (min, max) instead
 * of tuple[int, int] — OpenAI structured output does not support Python tuples
 * in JSON schema (Pitfall 6 from RESEARCH.md).
 */
export interface LineItem {
  id: string;
  name: string;
  description: string;
  deliverables: string[];
  timeline_weeks?: number | null;
  budget_range_usd?: number[] | null;
}
/**
 * Typed mess-spec entry (D-08/D-09).
 *
 * list[dict] avoided — keeps the TS contract typed and the generated
 * shared-types accurate. Each entry instructs the vendor-gen prompt to inject
 * one deliberate flaw into a specific line item.
 */
export interface MessSpecItem {
  line_item: string;
  issue_type: string;
  instruction: string;
}
/**
 * Marketing-services Request for Quotation.
 *
 * Our own clean procurement artifact — plain Python types, no Field[T] wrappers
 * (D-11). The rfq-gen prompt targets structured output against this schema.
 * The 8-line-item requirement is enforced by test_rfq_fixture_valid(), not by a
 * model_validator here — see plan 02-03 decision note.
 */
export interface RFQ {
  title: string;
  client_name: string;
  issue_date: string;
  response_deadline: string;
  scope_summary: string;
  line_items: LineItem[];
  commercial_expectations: string;
  questionnaire?: string[];
  compliance_requirements?: string[];
  budget_total_usd?: number | null;
}
/**
 * A single vendor's response to the RFQ — raw text + provenance (D-12).
 *
 * raw_text is the vendor's messy prose document exactly as generated (or
 * uploaded). mess_spec is the typed list[MessSpecItem] so the TS contract
 * stays accurate. The extraction agent reads raw_text and produces
 * ExtractionResult — no pre-extracted fields live here.
 */
export interface VendorResponse {
  vendor_name: string;
  persona: string;
  mess_spec?: MessSpecItem[];
  source_id: string;
  format_label: string;
  raw_text: string;
}
