---
phase: 03-extraction-agent
plan: "01"
subsystem: services/ai/tests
tags: [testing, tdd, extraction, wave-0]
dependency_graph:
  requires: []
  provides:
    - RED test stubs for EXTRACT-01/02/03/05 and PROMPT-03
    - Shared fixture builders (conftest_extraction.py)
    - docs/traces/ directory tracking for D-13 trace artifacts
  affects:
    - services/ai/tests/test_extraction_agent.py
    - services/ai/tests/conftest_extraction.py
    - services/ai/pyproject.toml
    - docs/traces/
tech_stack:
  added: []
  patterns:
    - xfail stubs with strict=True (RED gate enforcement)
    - plain function fixture builders (no pytest fixture injection needed inside test bodies)
    - fabricated_field() sentinel approach for walker coverage testing (B-R1 redesign)
key_files:
  created:
    - services/ai/tests/test_extraction_agent.py
    - services/ai/tests/conftest_extraction.py
    - docs/traces/.gitkeep
  modified:
    - services/ai/pyproject.toml
decisions:
  - "fabricated_field() approach for walker coverage — all-missing would produce 0 entries regardless of walker behavior; fabricated present fields guarantee a DowngradeEntry per visited field"
  - "9 tests all xfail strict=True — they must FAIL until implementation lands; live guard additionally marked @pytest.mark.live"
  - "plain functions not pytest fixtures in conftest_extraction.py — usable inside test bodies without injection machinery"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-27"
  tasks_completed: 1
  files_created: 4
---

# Phase 3 Plan 1: Wave 0 RED Test Stubs Summary

**One-liner:** RED test stubs for all Phase 3 verification gates — 9 xfail functions covering schema shape, walker coverage (IN-04 B-R1), evidence grounding, truncation/refusal error events, SSE taxonomy, and trace file existence.

## What Was Built

### `services/ai/tests/conftest_extraction.py`
Three plain-function fixture builders:
- `missing_field()` — `Field(status=missing)`, no value or evidence
- `present_field(value, snippet, source_id)` — `Field(status=present)` with one Evidence item
- `fabricated_field(value)` — `Field(status=present)` with sentinel snippet `XYZNOTFOUND_FABRICATED_SNIPPET_123` (24+ chars, guaranteed unlocatable); used in walker coverage test

### `services/ai/tests/test_extraction_agent.py`
9 test stubs, all `@pytest.mark.xfail(strict=True)`:

| Test | Maps to | What it verifies when GREEN |
|------|---------|----------------------------|
| `test_schema_shape` | EXTRACT-01 | `ExtractionResult` has all 10 fields; `vendor_name` is `str` not `Field[str]` (D-05) |
| `test_walker_covers_all_fields` | walker/IN-04 | `_walk_and_ground` visits every `Field[T]`; B-R1 fabricated_field approach, not all-missing |
| `test_evidence_required` | EXTRACT-02 | Verbatim snippet survives grounding with `status=present` |
| `test_truncation_raises_error_event` | EXTRACT-05 | `LengthFinishReasonError` → `error` SSE event with `recoverable=True`, no parsed result |
| `test_refusal_raises_error_event` | EXTRACT-05 | Refusal path → `error` SSE event with `recoverable=False`, no parsed result |
| `test_missing_line_items_surface_as_missing` | EXTRACT-01/03 | Missing `pricing`/`scope_coverage` propagate through SSE result unchanged |
| `test_sse_event_taxonomy` | SSE | All `/extract/vendor` event types in `EVENT_TYPES`; patches `agents.extraction._chain` (B-R4) |
| `test_traces_committed` | PROMPT-03/D-15 | ≥3 trace JSON files with required keys; ≥1 has non-empty `downgrade_report.entries` |
| `test_truncation_live_guard` | EXTRACT-05 live | `LengthFinishReasonError` raised by installed langchain-openai on `max_tokens=1`; `@pytest.mark.live` |

### `docs/traces/.gitkeep`
Empty tracked file that establishes the `docs/traces/` directory for D-13 trace artifacts.

### `services/ai/pyproject.toml`
Added `markers = ["live: ..."]` to `[tool.pytest.ini_options]` so CI can run `pytest -m "not live"` to skip the live guard.

## Verification Result

```
108 passed, 9 xfailed in 0.97s
```
All 9 stubs collected with no import errors. Full suite (108 tests) still green.

## Deviations from Plan

None — plan executed exactly as written.

The only implementation note: `test_truncation_live_guard` shows as XFAIL (not SKIP) because the `@pytest.mark.live` custom marker doesn't auto-skip without a `pytest --addopts="-m not live"` CI flag. The `live` marker is registered and documented; CI exclusion is configured at the CI level (not in pyproject.toml `addopts`) per the plan's intent.

## Known Stubs

All 9 test functions are intentional stubs — this is Wave 0 (RED gate). They are designed to fail and will go GREEN as implementation plans land:
- Plans 03-02/03-03 → tests 1–7 go GREEN (schema + agent implementation)
- Plan 03-04 → test 8 goes GREEN (trace capture)
- Plan 03-03/03-04 + live run → test 9 goes GREEN (live validation)

## Threat Flags

None — Wave 0 is test-only; no trust boundary crossed; no user input processed.

## Self-Check: PASSED

- FOUND: services/ai/tests/test_extraction_agent.py
- FOUND: services/ai/tests/conftest_extraction.py
- FOUND: docs/traces/.gitkeep
- FOUND: .planning/phases/03-extraction-agent/03-01-SUMMARY.md
- FOUND: commit 84680c6
