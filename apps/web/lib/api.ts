import type { ExtractionResult, RFQ, VendorResponse } from "@aerchain/shared-types";
import { streamSSE, type EventEnvelope } from "./sse";

const BASE = process.env.NEXT_PUBLIC_AI_BASE_URL ?? "http://localhost:8000";

// CRITICAL: request body key is "vendor_response" (FastAPI ExtractionRequest.vendor_response)
// Sending "vendor" → 422 Unprocessable Entity
export function streamExtract(
  vendor: VendorResponse,
  rfq: RFQ,
  signal?: AbortSignal,
): AsyncGenerator<EventEnvelope> {
  return streamSSE(`${BASE}/extract/vendor`, { vendor_response: vendor, rfq }, signal);
}

// Requires ≥2 items in extractions — caller (comparison/page.tsx) must guard this
export function streamCompare(
  extractions: ExtractionResult[],
  rfq: RFQ,
  signal?: AbortSignal,
): AsyncGenerator<EventEnvelope> {
  return streamSSE(`${BASE}/compare/vendors`, { extractions, rfq }, signal);
}

/**
 * Normalize the extraction "result" SSE payload.
 *
 * The extraction result payload spreads ExtractionResult fields at the top level
 * alongside a sibling "downgrade_report" key — NOT a bare ExtractionResult.
 * This helper separates them so callers can:
 *   - cache `result` (clean ExtractionResult) for re-POSTing to /compare/vendors
 *   - display `downgrade_report` on the Trace screen
 */
export function normalizeExtractionPayload(payload: Record<string, unknown>): {
  result: ExtractionResult;
  downgrade_report: unknown;
} {
  const { downgrade_report, ...result } = payload;
  return { result: result as unknown as ExtractionResult, downgrade_report };
}
