---
phase: 04-comparison-agent
plan: "01"
subsystem: services/ai/tests
tags: [tdd, red-stubs, comparison-agent, testing]
dependency_graph:
  requires: [03-extraction-agent]
  provides: [04-02, 04-03, 04-04]
  affects: [services/ai/tests/test_comparison_agent.py, services/ai/tests/conftest_comparison.py]
tech_stack:
  added: []
  patterns: [builder-functions-not-fixtures, red-green-refactor, wave-gated-tdd]
key_files:
  created:
    - services/ai/tests/conftest_comparison.py
    - services/ai/tests/test_comparison_agent.py
  modified: []
decisions:
  - "Builder functions (not pytest fixtures) in conftest_comparison.py — same rationale as conftest_extraction.py; works in test bodies without injection machinery"
  - "20 stubs raise NotImplementedError (not xfail) — genuinely RED by design; Wave 3 makes them GREEN"
  - "WAVE_0_COMPLETE = True sentinel enables grep-gating from orchestrator"
metrics:
  duration: "4 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_created: 2
---

# Phase 04 Plan 01: RED Stubs — Comparison Agent Test Gates Summary

Wave 1: established all 20 RED stubs and ExtractionResult fixture builders for the comparison agent before any implementation exists (Nyquist gate).

## What Was Built

**conftest_comparison.py** — ExtractionResult fixture builders following the conftest_extraction.py pattern exactly:
- `missing_line_item()` / `present_line_item()` — LineItemExtraction builders
- `missing_extraction()` — all Field[T] attributes set to missing
- `present_extraction()` — all fields present with sentinel snippets; one present line item
- `partial_extraction()` — scope_summary + timeline present; pricing/commercial missing; one missing line item (primary clamp test fixture)
- Imports `missing_field` / `present_field` from conftest_extraction (no duplication)

**test_comparison_agent.py** — 20 named RED stubs:
- 13 original stubs (COMPARE-01..05, SSE taxonomy, truncation/refusal error events, trace)
- 7 new stubs from consensus review fixes (Fix 1 e2e clamp blocker, Fix 4 empty-list ceilings, Fix 7 attention triggers, Fix 8 clarification failure, Fix 9 SSE sequence, Fix 10 cross-vendor conflicts, Fix 11 RFQ alignment)
- `WAVE_0_COMPLETE = True` constant for grep-gating
- Module docstring maps every test to its requirement ID and review fix

## Verification

- `pytest --collect-only` shows exactly 20 test IDs
- All 20 fail with `NotImplementedError` (0 import errors, 0 AttributeErrors)
- Full existing suite: 116 passed, 1 xfailed (no regression)
- Pydantic validation confirmed for all three extraction builders

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

All 20 stubs in test_comparison_agent.py are intentional RED stubs. Wave 3 (plan 04-03) will make them GREEN once the comparison agent implementation lands in Wave 2 (plan 04-02).

## Threat Surface Scan

No new network endpoints, auth paths, file access, or schema changes introduced — test-only files.

## Self-Check

- [x] services/ai/tests/conftest_comparison.py exists
- [x] services/ai/tests/test_comparison_agent.py exists
- [x] Commit 7220a4e: conftest_comparison.py builders
- [x] Commit deffe23: test_comparison_agent.py 20 RED stubs

## Self-Check: PASSED
