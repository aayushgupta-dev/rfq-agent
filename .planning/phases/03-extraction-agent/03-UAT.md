---
status: complete
phase: 03-extraction-agent
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md]
started: 2026-06-27T18:58:20Z
updated: 2026-06-27T19:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running service, start `uvicorn api.app:app` from scratch. Server boots with no errors/warnings, lifespan completes, and `/extract/vendor` appears in the OpenAPI schema (route live).
result: pass
verified: Booted uvicorn on a clean port from scratch — empty startup log (no errors/warnings). OpenAPI served 4 routes; /extract/vendor present.

### 2. Extract a Messy Vendor → Grounded Structured Output
expected: Running extraction on a real messy vendor returns a structured ExtractionResult (vendor_name, scope_summary, line_items, pricing, commercial_terms, timeline, compliance, assumptions, exclusions, risks). Every fact marked `present` carries an evidence snippet traceable to the vendor's source text — nothing asserted without a span.
result: pass
verified: trace_vendor_cheap final_result — 31/31 present facts carry a non-empty evidence snippet (100%). Sample value matched its source span verbatim.

### 3. Absence Is First-Class (missing / unclear / conflicting surfaced)
expected: Gaps and contradictions are explicit, not silently filled. Across the 3 vendors: cheap-but-incomplete shows `missing` (TVC Production + Kids Compliance unbid) and `unclear`; polished-fluff shows `conflicting` (pricing/timeline); thorough-but-pricey shows `unclear` (bundled pricing). All three absence states appear.
result: pass
verified: trace flag counts — cheap {present 31, missing 4, unclear 3}; fluff {present 27, conflicting 3}; thorough {present 41, unclear 4, conflicting 1, missing 1}. All three absence states exhibited.

### 4. No Fabricated Evidence (grounding gate enforced in code)
expected: Evidence is validated in code, not on the model's word. A fabricated/unlocatable snippet is downgraded by the grounding gate (exact + fuzzy match against source); every `present` fact's snippet is genuinely locatable in the vendor source. Verbatim-evidence integrity holds across captured traces.
result: pass
verified: gate downgrade + integrity tests pass (fabricated span, fuzzy-below-threshold, missing source_id, short-snippet, traces_committed verbatim integrity) — 9 passed.

### 5. Failure Shapes → Safe Error Events (no partial result leaks)
expected: Structured-output failure shapes (truncation / refusal / parse error / unexpected type) each map to a safe SSE `error` event with the correct `recoverable` flag, and NO partial/parsed result crosses the boundary. Truncation=recoverable, refusal=non-recoverable.
result: pass
verified: test_truncation_raises_error_event + test_refusal_raises_error_event pass; covered by full suite (116 passed, live guard deselected).

### 6. Prompt Pack — extraction.v1.md Quality
expected: The extraction prompt loads from the registry, enforces exactly 4 model-facing flag states (present/missing/unclear/conflicting), a ≥20-char verbatim evidence floor, and RFQ-aware line-item extraction. The gate-only word `unsupported` does not appear in the prompt body. Prompt Pack doc explains intent + failure handling.
result: pass
verified: prompt loads (9459 chars); all 4 flag states present, 'unsupported' absent, verbatim + 20-char floor present in body.

### 7. Pipeline Traces Captured (input → prompt → output → grounded)
expected: ≥3 full pipeline traces committed under docs/traces/ (JSON + Markdown), each with the D-14 keys: input, resolved_prompt, raw_model_output, grounding_step, final_result. Traces demonstrate the end-to-end extraction on real vendors.
result: pass
verified: 4 JSON + 4 MD traces under docs/traces/ (cheap, fluff, thorough, adversarial). Keys confirmed: input, resolved_prompt, raw_model_output, grounding_step, final_result.

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
