---
phase: 03-extraction-agent
plan: "03"
subsystem: services/ai
tags: [extraction, langgraph, sse, grounding, reliability]
dependency_graph:
  requires: [03-02]
  provides: [extraction_graph, run_extraction, generate_extraction_with_trace, /extract/vendor]
  affects: [services/ai/agents/extraction.py, services/ai/api/app.py]
tech_stack:
  added: []
  patterns: [LangGraph StateGraph, include_raw=True refusal detection, all-failure-shapes B-R2 guard]
key_files:
  created:
    - services/ai/agents/extraction.py
  modified:
    - services/ai/api/app.py
    - services/ai/tests/test_extraction_agent.py
decisions:
  - Extraction payload inlines ExtractionResult fields at top level of payload dict (not nested under "extraction" key) so callers access payload["line_items"] directly; downgrade_report is a sibling key
  - run_extraction() sync testable wrapper bypasses LangGraph runtime to enable patching _chain in tests without a running event loop
  - xfail markers removed from test_truncation, test_refusal, test_missing_line_items, test_sse_event_taxonomy — implementation now satisfies all four
metrics:
  duration: "~15 min"
  completed_date: "2026-06-27"
  tasks_completed: 2
  files_changed: 3
---

# Phase 3 Plan 03: Extraction Agent StateGraph + SSE Route Summary

LangGraph extraction agent with B-R2 all-failure-shapes hardening and grounded SSE streaming. The extraction graph is the phase's central reliability artifact: every structured-output failure shape maps to a safe SSE error event before any result data crosses the boundary. Grounding runs inside the node before the result event emits (D-07).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement agents/extraction.py — StateGraph + all-failure-shapes + trace surface | c2ff8c8 | services/ai/agents/extraction.py, tests/test_extraction_agent.py |
| 2 | Add POST /extract/vendor SSE route to app.py + ExtractionRequest body | ed78bea | services/ai/api/app.py, tests/test_extraction_agent.py |

## What Was Built

**services/ai/agents/extraction.py** — LangGraph StateGraph with one `extract` node backed by `_run_extraction_impl`. The implementation separates core logic from the LangGraph node wrapper to allow test-time injection of an event collector instead of `get_stream_writer()`.

Failure shapes handled (B-R2 — none reach the result path):
- `LengthFinishReasonError` (truncation) → error event `{code: extraction_truncated, recoverable: True}`
- `additional_kwargs["refusal"]` non-None → error event `{code: extraction_refused, recoverable: False}`
- `parsed is None` OR `parsing_error` present → error event `{code: extraction_parse_error, recoverable: True}`
- `not isinstance(parsed, ExtractionResult)` → error event `{code: extraction_unexpected_type, recoverable: False}`
- Bare `Exception` → error event `{code: extraction_error, recoverable: False}`

Exports: `extraction_graph` (compiled StateGraph), `run_extraction` (sync testable wrapper), `generate_extraction` (asyncio.run wrapper for scripts), `generate_extraction_with_trace` (D-14/D-15 trace capture surface).

**services/ai/api/app.py** — Added `ExtractionRequest` Pydantic model with `vendor_response: VendorResponse` + `rfq: RFQ` fields and a `model_validator` that enforces the 200k-char limit on `vendor_response.raw_text`. Added `POST /extract/vendor` route that streams `extraction_graph.astream(stream_mode="custom")` events through `EventEnvelope`.

## Tests

5 tests turned GREEN in this plan (xfail markers removed):
- `test_truncation_raises_error_event` — LengthFinishReasonError → error event recoverable=True
- `test_refusal_raises_error_event` — additional_kwargs refusal → error event recoverable=False
- `test_evidence_required` — verbatim snippet survives grounding with status=present
- `test_missing_line_items_surface_as_missing` — missing Field status propagates through SSE result
- `test_sse_event_taxonomy` — all emitted event types are in EVENT_TYPES

Full suite: 115 passed, 2 xfailed (test_traces_committed and test_truncation_live_guard remain correctly deferred to Plan 04).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed LengthFinishReasonError constructor in test**
- **Found during:** Task 1 test run
- **Issue:** Test stub used `LengthFinishReasonError(message=..., response=...)` but the actual constructor signature is `LengthFinishReasonError(*, completion: ChatCompletion)`
- **Fix:** Changed to `LengthFinishReasonError(completion=MagicMock())`
- **Files modified:** services/ai/tests/test_extraction_agent.py
- **Commit:** c2ff8c8

**2. [Rule 1 - Bug] Payload structure — extraction fields inlined at top level**
- **Found during:** Task 1 test run for test_missing_line_items_surface_as_missing
- **Issue:** Plan spec had `{"type": "result", "payload": {"extraction": {...}, "downgrade_report": {...}}}` but the test accesses `payload["line_items"]` directly (not `payload["extraction"]["line_items"]`)
- **Fix:** Inlined extraction fields at payload top level using `{**grounded.model_dump(mode="json"), "downgrade_report": report.model_dump(mode="json")}` — test is the behavioral spec
- **Files modified:** services/ai/agents/extraction.py
- **Commit:** c2ff8c8

**3. [Rule 1 - Bug] run_extraction() testable wrapper vs graph-level invoke**
- **Found during:** Task 1 test analysis
- **Issue:** Tests call `run_extraction(vendor_response=..., rfq=...)` and patch `agents.extraction._chain` — this requires direct node invocation, not `extraction_graph.ainvoke` (which runs inside the LangGraph runtime and doesn't expose the stream writer for event collection)
- **Fix:** Added `_run_extraction_impl(state, emit_fn)` separating core logic from the LangGraph node; `run_extraction` calls it directly with a list-collecting emit function; production `_extraction_node` passes `get_stream_writer()`
- **Files modified:** services/ai/agents/extraction.py
- **Commit:** c2ff8c8

## Known Stubs

None — all exported functions are implemented and tested.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns beyond what is in the plan's threat model. The `POST /extract/vendor` route is in the plan's trust boundary table (T-03-03-01 through T-03-03-07). No unregistered threat surface introduced.

## Self-Check: PASSED

- [x] services/ai/agents/extraction.py exists
- [x] services/ai/api/app.py has /extract/vendor route
- [x] Commit c2ff8c8 exists (Task 1)
- [x] Commit ed78bea exists (Task 2)
- [x] 115 passed, 2 xfailed — full suite green
