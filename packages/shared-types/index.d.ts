/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * 5-state absence/confidence flag for every extracted field (D-07).
 *
 * Never collapses to blank — absence is first-class.
 */
export type FlagStatus = "present" | "missing" | "unclear" | "conflicting" | "unsupported";

/**
 * Side-by-side vendor comparison output (stub — full fields in Phase 4).
 *
 * # ponytail: P4 placeholder — real fields (technical / commercial / scope /
 * # timeline / compliance / risk dimensions, comparability signal, buyer
 * # attention points, clarification questions) land in Phase 4 (comparison agent).
 */
export interface ComparisonResult {
  vendor_count?: FieldInt;
  comparable?: FieldStr;
}
export interface FieldInt {
  status: FlagStatus;
  value?: number | null;
  evidence?: Evidence[];
  values?: ConflictingValueInt[] | null;
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
export interface ConflictingValueInt {
  value?: number | null;
  evidence?: Evidence[];
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
  scope_summary: FieldStr1;
  line_items?: LineItemExtraction[];
  pricing_structure: FieldStr1;
  total_price: FieldDecimal;
  commercial_terms: FieldStr1;
  timeline: FieldStr1;
  compliance_points?: FieldStr1[];
  assumptions?: FieldStr1[];
  exclusions?: FieldStr1[];
  risks?: FieldStr1[];
}
export interface FieldStr1 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
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
  pricing: FieldDecimal;
  scope_coverage: FieldStr1;
}
export interface FieldDecimal {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueDecimal[] | null;
}
export interface ConflictingValueDecimal {
  value?: string | null;
  evidence?: Evidence[];
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
