---
status: complete
phase: 02-grounding-gate-messy-data
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
  - 02-FIXES-SUMMARY.md
started: 2026-06-27T15:54:08Z
updated: 2026-06-27T15:58:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Fresh boot of the AI service runs the D-16 boot gate (verify_access) without aborting; FastAPI app comes up clean.
result: pass
evidence: TestClient lifespan (api smoke + live-LLM run) ran the boot gate against the real org/key — gpt-5.4 access confirmed, no boot abort, routes registered.

### 2. Code-Level Test Suite
expected: `uv run pytest -q` passes the full suite (108 tests).
result: pass
evidence: "108 passed, 1 warning in 0.63s" (warning is a pre-existing starlette/httpx deprecation, not a failure).

### 3. Grounding Gate Downgrades Fabricated Spans (EXTRACT-04)
expected: A model-asserted snippet not present in source → status=unsupported, value cleared, evidence dropped, downgrade entry recorded.
result: pass
evidence: phase2_e2e.py — "status=unsupported, value=None, evidence_len=0, downgrade_entries=1". Pure-Python gate, no LLM involved.

### 4. Grounding Gate Recomputes Genuine Offsets (EXTRACT-04 / D-01)
expected: Genuine snippet with WRONG model offsets stays present; gate recomputes true offsets from source so source[span]==snippet.
result: pass
evidence: phase2_e2e.py — "model gave (0,1); gate recomputed (400,460); source[span]==snippet: True". Model-supplied offsets ignored.

### 5. RFQ Is a Realistic Procurement Event (DATA-01)
expected: data/rfq.json is a valid RFQ with all 8 named line items + compliance requirements.
result: pass
evidence: Committed fixture: line_items=8, compliance=10. Live regen via GET /data/rfq: 8 line items, 11 compliance requirements, title "GlowBite 18-Month Go-to-Market Marketing Services Program".

### 6. Three Messy Vendor Fixtures With Distinct Real-World Mess (DATA-02/03)
expected: cheap → missing-price "TBD"; fluff → conflicting timeline figures; thorough → bundled/over-scope.
result: pass
evidence: phase2_e2e.py — cheap has "TBD"; fluff has distinct week counts {5,6,8,12,14,18}. Live regen of cheap persona also produced a missing/TBD marker.

### 7. Live-Regen API Endpoints + Validation Guards (DATA-04 / security)
expected: GET /data/rfq + POST /data/vendor-gen registered; unknown persona → 400; over-length rfq_text → 422.
result: pass
evidence: phase2_api_smoke.py — both routes registered, unknown persona → 400, over-length → 422. Live-LLM run confirmed the happy path of BOTH endpoints actually calls gpt-5.4 and returns valid RFQ + VendorResponse objects.

### 8. Prompt Pack Authored + Documented (PROMPT-04)
expected: rfq-gen / vendor-gen / messy-data-gen prompts exist with full bodies; docs/prompts/data-generation.md documents each.
result: pass
evidence: All three prompt files present with full bodies; docs/prompts/data-generation.md present (PROMPT-04).

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Observations (minor, non-blocking)

Surfaced while exercising the live LLM path — both pre-existing in the committed
fixtures and consistent live↔committed. Neither affects the grounding gate or any
Phase 2 success criterion. Recorded for transparency, not auto-routed to fix:

- **`vendor_name` is set to the persona label**, not an agency name (vendor_gen.py:237 `vendor_name=persona`). A buyer UI would show "cheap-but-incomplete" as the vendor's name. The real fictional agency identity lives in `raw_text`. Minor data-realism gap (rubric §realistic-data) — most relevant once Phase 5 renders vendor names.
- **`source_id` has a doubled `vendor_` prefix** → `vendor_vendor_cheap` (vendor_gen.py:240 prepends `vendor_` to a filename that already starts with `vendor_`). Cosmetic; `source_id` is an internal evidence-mapping key and works correctly as-is.

## Gaps

[none — all checkpoints passed]
