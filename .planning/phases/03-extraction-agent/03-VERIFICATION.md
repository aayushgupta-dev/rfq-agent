---
phase: 03-extraction-agent
verified: 2026-06-27T18:24:08Z
status: passed
score: 5/5
overrides_applied: 0
---

# Phase 3: Extraction Agent — Verification Report

**Phase Goal:** Per-vendor extraction produces grounded, evidence-backed structured output that
streams to the client and never fabricates.
**Verified:** 2026-06-27T18:24:08Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | Extraction returns a structured per-vendor object covering scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, and risks | VERIFIED | `ExtractionResult` has all 10 required fields (vendor_name + 10 categories); `LineItemExtraction` per line item. `test_schema_shape` GREEN. `domain.py:116–161`. |
| SC-2 | Every extracted fact carries an evidence snippet drawn from the vendor response, and that snippet passes the Phase 2 grounding gate before being shown | VERIFIED | `ground_model()` called at `extraction.py:215` before the result event is emitted (D-07 ordering confirmed by line 228 `emit(result_event)`). `test_evidence_required` GREEN. `test_traces_committed` asserts snippet locatability via gate's own matcher. 4 traces confirm grounding ran (grounding_step present in all). |
| SC-3 | Missing / unclear / conflicting / unsupported information is flagged explicitly; the agent never fills a missing field | VERIFIED | 4 flag states enforced by `Field[T]` envelope (`envelope.py:27–37`). Prompt uses exactly 4 states; "unsupported" absent from `extraction.v1.md` body (grep returns empty). Model-facing schema only ever emits present/missing/unclear/conflicting; code gate assigns unsupported. `test_missing_line_items_surface_as_missing` GREEN. Flag distribution across 3 vendor traces: cheap→missing(4), fluff→conflicting(3), thorough→unclear(4). |
| SC-4 | Structured output under strict mode treats `finish_reason: length` (truncation) and the `refusal` field as hard errors — never parsed as valid output | VERIFIED | All 5 failure shapes mapped to safe error events in `extraction.py:107–198` (B-R2). `test_truncation_raises_error_event` GREEN (recoverable=True). `test_refusal_raises_error_event` GREEN (recoverable=False). parse-None, parsing_error, unexpected-type paths also covered. |
| SC-5 | The extraction agent streams progress over SSE as `{type, payload}` (never buffer-and-return), and ≥1 complete prompt trace is captured | VERIFIED | `POST /extract/vendor` returns `EventSourceResponse` (`app.py:153–170`), streaming via `extraction_graph.astream(stream_mode="custom")`. Every chunk validated through `EventEnvelope` before serialization. `test_sse_event_taxonomy` GREEN. 4 traces (JSON + MD) under `docs/traces/` — each with D-14 keys: input, resolved_prompt, raw_model_output, grounding_step, final_result. |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `services/ai/schemas/domain.py` | Full `ExtractionResult` + `LineItemExtraction` (D-01..D-05) | VERIFIED | 11-field `ExtractionResult`, `LineItemExtraction` with `pricing: Field[str]` + `scope_coverage: Field[str]`. `vendor_name: str` (D-05 fix). No `dict[str, Field]` (D-04). |
| `services/ai/agents/extraction.py` | LangGraph `StateGraph` with all-failure-shapes hardening, grounding before result emit | VERIFIED | `extraction_graph` compiled. `_run_extraction_impl` handles 5 failure shapes. `ground_model` at line 215, `emit(result_event)` at line 228. Exports `run_extraction`, `generate_extraction`, `generate_extraction_with_trace`. |
| `services/ai/api/app.py` | `POST /extract/vendor` SSE route | VERIFIED | Route at line 153. `ExtractionRequest` model with 200k-char guard. SSE via `EventSourceResponse`, done event appended. |
| `services/ai/prompts/extraction.v1.md` | Full production prompt with exactly 4 flag states, "unsupported" absent from body | VERIFIED | Prompt authored with role, 4 flag states with decision rules, evidence floor (≥20 chars / ≥3 words), humility instruction, 4 few-shot examples, RFQ line-item extraction rules. "unsupported" does not appear in the body (grep empty). |
| `docs/traces/*.json` (≥3) | D-14 keys: input, resolved_prompt, raw_model_output, grounding_step, final_result | VERIFIED | 4 JSON + 4 Markdown traces. All 4 have all 5 required keys. |
| `packages/shared-types/index.d.ts` | TS contract includes `LineItemExtraction` + `ExtractionResult` | VERIFIED | Codegen regenerated at commit `ce8cd1c` (Plan 03-02) and again `1d29886` (Plan 03-04, Field[str] fix). `test_codegen_drift` GREEN. |
| `services/ai/tests/test_extraction_agent.py` | 9 tests covering all verification gates | VERIFIED | 554 lines, 9 tests. 8 GREEN, 1 XFAIL (live truncation guard — deliberate, requires real key + `-m live` flag). |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `extraction.py` | `grounding/gate.py:ground_model` | Called at line 215 before `emit(result_event)` at line 228 | WIRED | D-07 ordering confirmed in source |
| `extraction.py` | `prompts/registry.py:load("extraction")` | `_post = load("extraction")` at line 48 | WIRED | Prompt loaded at module init |
| `api/app.py:/extract/vendor` | `agents/extraction.py:extraction_graph` | `from agents.extraction import extraction_graph` + `extraction_graph.astream(...)` | WIRED | Import at line 36, used at line 163 |
| Result event | `EventEnvelope` validation | `EventEnvelope(**chunk).model_dump_json()` before serialization | WIRED | Malformed emit fails validation, never streams to client |
| Traces | `generate_extraction_with_trace` | Only authorized trace-capture surface; no local chain rebuilds | WIRED | `capture_traces.py` imports and calls this function per D-14/D-15 |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `extraction.py:_run_extraction_impl` | `grounded` (ExtractionResult) | `_chain.invoke(...)` → `ground_model(raw, ...)` | Yes — real gpt-5.4 call + gate grounding | FLOWING |
| `api/app.py:/extract/vendor` | SSE chunks | `extraction_graph.astream(stream_mode="custom")` | Yes — production graph | FLOWING |
| `docs/traces/*.json` | final_result | Real gpt-5.4 runs on committed messy vendor fixtures | Yes — 4 live-run traces committed | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `uv run pytest tests/ -q` | 116 passed, 1 xfailed, 0 failures in 2.16s | PASS |
| ExtractionResult has all 10 categories | `test_schema_shape` | PASSED | PASS |
| Walker visits every Field[T] (IN-04) | `test_walker_covers_all_fields` | PASSED | PASS |
| Truncation → error event recoverable=True | `test_truncation_raises_error_event` | PASSED | PASS |
| Refusal → error event recoverable=False | `test_refusal_raises_error_event` | PASSED | PASS |
| Missing fields propagate through SSE result | `test_missing_line_items_surface_as_missing` | PASSED | PASS |
| All SSE types in EVENT_TYPES | `test_sse_event_taxonomy` | PASSED | PASS |
| ≥3 traces with D-14 keys + evidence integrity | `test_traces_committed` | PASSED | PASS |
| Grounding gate downgrade path | `test_fabricated_span_is_downgraded`, `test_fuzzy_match_below_threshold_downgrades`, `test_missing_source_id_downgrades`, `test_short_snippet_guard` | ALL PASSED | PASS |
| "unsupported" absent from extraction.v1.md body | `grep -n "unsupported" services/ai/prompts/extraction.v1.md` | No output | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| EXTRACT-01 | 03-02, 03-03 | ExtractionResult covers all 8 RFQ categories; per-line-item pricing + scope | SATISFIED | `domain.py:116–161`; `test_schema_shape` GREEN |
| EXTRACT-02 | 03-02, 03-04 | Every extracted fact carries an evidence snippet that passes grounding | SATISFIED | `extraction.py:215`; `test_evidence_required` GREEN; `test_traces_committed` evidence-integrity assertion |
| EXTRACT-03 | 03-03 | Missing/unclear/conflicting flagged explicitly; never filled | SATISFIED | `FlagStatus` enum enforces this at schema level; `test_missing_line_items_surface_as_missing` GREEN |
| EXTRACT-05 | 03-03 | Truncation + refusal = hard errors, never parsed | SATISFIED | 5 failure shapes in `extraction.py:107–198`; `test_truncation_raises_error_event` + `test_refusal_raises_error_event` GREEN |
| PROMPT-03 | 03-04 | Full extraction prompt authored; ≥3 pipeline traces captured | SATISFIED | `extraction.v1.md` complete; 4 traces with D-14 keys; `test_traces_committed` GREEN |

---

## D-15 Reframe Assessment

The D-15 requirement ("≥1 trace must show a genuine downgrade") was reframed to "verbatim-evidence integrity" by a product-owner decision during execution. This was implemented honestly:

- **Not taken:** FUZZY_THRESHOLD lowering (B-R3 — forbidden); weaker model swap; staged/fabricated downgrade.
- **What happened:** gpt-5.4 quoted character-for-character verbatim on all 3 vendor fixtures and the adversarial fixture. The gate confirmed all snippets. 0 trace-level downgrades fired.
- **Downgrade path proven separately:** `test_grounding_gate.py` — 13 tests ALL GREEN — includes `test_fabricated_span_is_downgraded`, `test_fuzzy_match_below_threshold_downgrades`, `test_missing_source_id_downgrades`, `test_short_snippet_guard`. Code disproves the model when the model produces unlocatable snippets.
- **`test_traces_committed` now asserts:** Every shown fact's evidence snippet is locatable in the vendor source via the gate's own matcher (complementary half of "code enforces grounding").

Verdict: the reframe is implemented honestly and the combined evidence (4 traces + 13 gate unit tests) satisfies "code disproves the model" more rigorously than a single forced downgrade would.

---

## Anti-Patterns Found

No blockers. No TBD/FIXME/XXX markers in phase files. One deliberate XFAIL:

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `test_extraction_agent.py:536` | `@pytest.mark.xfail(strict=True)` on `test_truncation_live_guard` | INFO | Intentional — requires real OpenAI key; CI skips with `-m not live`. Documented in SUMMARY and plan. |

`ponytail:` comments in `domain.py`, `extraction.py`, and `app.py` mark deliberate simplifications with named upgrade paths — not debt.

---

## Human Verification Required

### 1. Live SSE end-to-end stream

**Test:** `curl -N http://localhost:8000/extract/vendor` with a real vendor JSON body (one of the committed `data/vendor_*.json` fixtures) and the committed RFQ.
**Expected:** Events arrive as `data: {"type":"status",...}` → `data: {"type":"result",...}` → `data: {"type":"done",...}`. The result payload contains grounded line items with correct flag statuses.
**Why human:** Requires running FastAPI + a live gpt-5.4 call. Unit tests mock `_chain`; this validates the full production path including the LangGraph SSE spine.

### 2. Prompt trace visual review

**Test:** Open `docs/traces/trace_vendor_cheap.md`, `trace_vendor_fluff.md`, `trace_vendor_thorough.md` in a browser or markdown viewer.
**Expected:** Each trace shows: (1) input vendor text, (2) the resolved system prompt, (3) raw model output, (4) grounding step diff, (5) final grounded result. The "cheap" trace shows `missing` line items for TVC Production and Kids Compliance. The "fluff" trace shows `conflicting` on pricing_structure, total_price, timeline. The "thorough" trace shows `unclear` on bundled line-item pricing.
**Why human:** Visual review of rendered Markdown; automated tests assert structure and evidence integrity but not narrative correctness of the trace annotations.

---

## Gaps Summary

No gaps. All 5 ROADMAP success criteria are verified. All 5 phase requirements (EXTRACT-01/02/03/05, PROMPT-03) are satisfied. Test suite: **116 passed, 1 xfailed (deliberate live guard), 0 failures**.

---

*Verified: 2026-06-27T18:24:08Z*
*Verifier: Claude (gsd-verifier)*
