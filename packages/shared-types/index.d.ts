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
 * Structured extraction for one vendor response (stub — full fields in Phase 3).
 *
 * # ponytail: P3 placeholder — real fields (scope, pricing breakdown, commercial
 * # terms, timeline, compliance, assumptions, exclusions, risks + evidence spans
 * # for each) land in Phase 3 (extraction agent).
 */
export interface ExtractionResult {
  vendor_name?: FieldStr1;
  scope_summary?: FieldStr2;
  total_price?: FieldDecimal;
}
export interface FieldStr1 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
}
export interface FieldStr2 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
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
 * Marketing-services Request for Quotation (stub — full fields in Phase 2).
 *
 * # ponytail: P2 placeholder — real fields (8 line items, scope, timelines,
 * # commercials, questionnaire, compliance) land in Phase 2 (RFQ/vendor generation).
 */
export interface RFQ {
  title?: FieldStr3;
  budget_total?: FieldDecimal1;
}
export interface FieldStr3 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
}
export interface FieldDecimal1 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueDecimal[] | null;
}
/**
 * A single vendor's response to the RFQ (stub — full fields in Phase 2).
 *
 * # ponytail: P2 placeholder — real fields (pricing structure, completeness,
 * # scope, assumptions, timelines) land in Phase 2.
 */
export interface VendorResponse {
  vendor_name?: FieldStr4;
  proposed_total?: FieldDecimal2;
  response_completeness_score?: FieldInt1;
}
export interface FieldStr4 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueStr[] | null;
}
export interface FieldDecimal2 {
  status: FlagStatus;
  value?: string | null;
  evidence?: Evidence[];
  values?: ConflictingValueDecimal[] | null;
}
export interface FieldInt1 {
  status: FlagStatus;
  value?: number | null;
  evidence?: Evidence[];
  values?: ConflictingValueInt[] | null;
}
