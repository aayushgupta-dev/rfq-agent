---
phase: 03-extraction-agent
plan: "02"
subsystem: schemas
tags: [schema, extraction, grounding, codegen, typescript]
dependency_graph:
  requires: [03-01]
  provides: [ExtractionResult full schema, LineItemExtraction, TS contract]
  affects: [services/ai/agents/extraction.py, packages/shared-types/index.d.ts]
tech_stack:
  added: []
  patterns: [Field[T] per-claim grounding, list[Field[str]] multi-claim, pydantic2ts codegen]
key_files:
  created: []
  modified:
    - services/ai/schemas/domain.py
    - services/ai/tests/conftest_extraction.py
    - services/ai/tests/test_extraction_agent.py
    - packages/shared-types/index.d.ts
decisions:
  - vendor_name is plain str (D-05 fix) — provenance metadata, never grounded
  - Field[Decimal] for pricing fields (total_price, LineItemExtraction.pricing) with ponytail contingency note
  - fabricated_decimal_field() added to conftest_extraction for Decimal-typed walker tests
metrics:
  duration: "~12 min"
  completed: "2026-06-27T17:42:06Z"
  tasks: 2
  files: 4
---

# Phase 3 Plan 02: ExtractionResult Schema + Codegen Summary

**One-liner:** Full ExtractionResult with LineItemExtraction sub-model per D-01..D-05, codegen regenerated, 3 tests GREEN.

## What Was Built

### Task 1: Flesh out ExtractionResult + LineItemExtraction (D-01..D-05)

Replaced the 3-field `ExtractionResult` stub with the full production schema:

- **`LineItemExtraction`** (new): per-RFQ-line-item container with `pricing: Field[Decimal]` and `scope_coverage: Field[str]`. `line_item_id`/`line_item_name` are plain `str` provenance fields (not grounded).
- **`ExtractionResult`** (11 fields): `vendor_name: str` (D-05 fix), `scope_summary`, `line_items: list[LineItemExtraction]` (D-01), `pricing_structure` + `total_price` (D-02 bundle/grand total), `commercial_terms`, `timeline`, `compliance_points`, `assumptions`, `exclusions`, `risks` — last four as `list[Field[str]]` (D-03 per-claim grounding).
- No `dict[str, Field]` shapes anywhere (D-04 — closes IN-04 walker gap by design).

**Test markers removed:** `test_schema_shape`, `test_walker_covers_all_fields`, `test_evidence_required` — all 3 now pass GREEN (were `xfail(strict=True)`).

**conftest_extraction.py:** Added `fabricated_decimal_field()` convenience wrapper for `Field[Decimal]` typed fields in walker tests. Updated `fabricated_field` signature to accept `object` value (was `str`).

### Task 2: Codegen + drift-check

Ran `uv run python scripts/codegen.py`. Regenerated `packages/shared-types/index.d.ts` now contains:
- `LineItemExtraction` interface with `pricing: FieldDecimal` and `scope_coverage: FieldStr1`
- `ExtractionResult` with all 11 fields and correct types
- `FieldDecimal` / `ConflictingValueDecimal` monomorphized types

`test_codegen_drift` GREEN.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `4f228f4` | feat(03-02): flesh out ExtractionResult + LineItemExtraction (D-01..D-05) |
| Task 2 | `ce8cd1c` | chore(03-02): regenerate TS contract for updated ExtractionResult + LineItemExtraction |

## Test Results

```
tests/test_extraction_agent.py ...xxxxxx  — 3 passed, 6 xfailed
tests/test_codegen_drift.py .             — 1 passed
Full suite (108 tests):                   — 108 passed, 1 warning
```

The 6 remaining `xfailed` tests are correctly scoped to Plans 03-03 (agent graph) and 03-04 (traces).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] fabricated_decimal_field() added to conftest_extraction**
- **Found during:** Task 1 — running `test_walker_covers_all_fields`
- **Issue:** `fabricated_field("XYZNOTFOUND_VALUE")` sets `value=str` but `pricing: Field[Decimal]` validates value is a valid Decimal — pydantic raised `ValidationError: decimal_parsing`
- **Fix:** Added `fabricated_decimal_field()` to conftest_extraction, updated test to use it for `pricing` and `total_price` fields; updated `fabricated_field` signature from `value: str` to `value: object`
- **Files modified:** `services/ai/tests/conftest_extraction.py`, `services/ai/tests/test_extraction_agent.py`
- **Commit:** `4f228f4`

**2. [Rule 1 - Bug] test_evidence_required xfail marker removed**
- **Found during:** Task 1 — running the broader test suite
- **Issue:** `test_evidence_required` was marked `xfail(reason="Plan 03-02 not yet executed")` but the test constructs a full `ExtractionResult` — it XPASS(strict)-failed after the schema was complete
- **Fix:** Removed the xfail marker; test passes GREEN
- **Files modified:** `services/ai/tests/test_extraction_agent.py`
- **Commit:** `4f228f4`

## Known Stubs

None — plan objective fully achieved.

## Threat Flags

No new security-relevant surface introduced. Schema definition → codegen is build-time only; no user input at this stage (T-03-02-SC accepted). D-05 fix (vendor_name plain str) closes T-03-02-01 — grounding gate never attempts to ground provenance metadata. D-04 no-dict constraint closes T-03-02-02 — walker coverage confirmed by test_walker_covers_all_fields GREEN.

## Self-Check: PASSED

- [x] `services/ai/schemas/domain.py` — exists, contains LineItemExtraction + ExtractionResult
- [x] `packages/shared-types/index.d.ts` — exists, contains LineItemExtraction + ExtractionResult
- [x] `services/ai/tests/conftest_extraction.py` — exists, contains fabricated_decimal_field
- [x] Commit `4f228f4` — exists (`git log --oneline | grep 4f228f4`)
- [x] Commit `ce8cd1c` — exists (`git log --oneline | grep ce8cd1c`)
- [x] test_schema_shape GREEN
- [x] test_walker_covers_all_fields GREEN
- [x] test_codegen_drift GREEN
