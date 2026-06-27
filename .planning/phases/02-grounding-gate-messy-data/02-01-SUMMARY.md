---
phase: 02-grounding-gate-messy-data
plan: "01"
subsystem: services/ai
tags:
  - grounding
  - test-harness
  - RED-state
  - wave-0
  - EXTRACT-04
  - DATA-01
  - DATA-02
  - DATA-03
dependency_graph:
  requires: []
  provides:
    - grounding package stubs (gate.py, report.py, __init__.py)
    - test_grounding_gate.py — 9 EXTRACT-04 unit tests in RED state
    - test_sample_fixtures.py — 5 DATA-01/02/03 fixture tests in RED state
  affects:
    - plan 02-02 (implements ground_field, ground_model to turn RED tests GREEN)
    - plan 02-03 (generates data/rfq.json + data/vendor_*.json to turn RED fixture tests GREEN)
tech_stack:
  added: []
  patterns:
    - grounding package with public API re-exports via __init__.py
    - pydantic BaseModel with ConfigDict(extra="forbid") for report models
    - NotImplementedError stubs: imports resolve, tests can be written pre-implementation
    - File-existence-first assertion ordering: AssertionError before AttributeError
    - FIXTURE_FILENAMES explicit map: persona -> authoritative filename (D-09/D-13)
key_files:
  created:
    - services/ai/grounding/__init__.py
    - services/ai/grounding/gate.py
    - services/ai/grounding/report.py
    - services/ai/tests/test_grounding_gate.py
    - services/ai/tests/test_sample_fixtures.py
  modified: []
decisions:
  - RED-before-GREEN enforced: test functions call gate functions normally; stubs raise NotImplementedError so tests FAIL (not pytest.raises which would invert RED/GREEN)
  - File-existence checked first in every fixture test: fails with AssertionError on missing file, not AttributeError on missing schema field
  - FIXTURE_FILENAMES uses explicit persona->filename map: derivation from persona name is forbidden (D-09/D-13 compliance)
metrics:
  duration_minutes: 25
  completed: "2026-06-27"
  tasks_completed: 3
  files_created: 5
  files_modified: 0
---

# Phase 02 Plan 01: Wave 0 Test Harness and Module Stubs Summary

Grounding package stubs + complete RED-state test suite — imports resolve, falsifiability tests A/B exist before any implementation.

## What Was Built

**grounding/ package stubs** — Three files creating the `grounding` Python package with the full public API surface plan 02-02 will implement:

- `grounding/__init__.py`: Re-exports `ground_field`, `ground_model`, `DowngradeEntry`, `DowngradeReport` as the package's public API.
- `grounding/gate.py`: Stubs for all gate functions (`_normalize_with_map`, `_match_exact`, `_match_fuzzy`, `ground_field`, `ground_model`), each raising `NotImplementedError("function_name not implemented")`. Module-level constants `FUZZY_THRESHOLD = 90.0` and `MIN_SNIPPET_LEN = 15` included with `# ponytail:` comments. Does NOT import rapidfuzz (added in 02-02).
- `grounding/report.py`: `DowngradeEntry` and `DowngradeReport` pydantic `BaseModel` subclasses with `ConfigDict(extra="forbid")`, proper `pydantic_Field(default_factory=list)` for lists, and a `has_downgrades` property.

**test_grounding_gate.py** — 9 unit tests in RED state (EXTRACT-04):

| Test | Class | Behavior Tested |
|------|-------|-----------------|
| `test_fabricated_span_is_downgraded` | `TestFabricatedSpanDowngrade` | Falsifiability Test A: fabricated snippet → unsupported |
| `test_genuine_span_passes_grounding` | `TestGenuineSpanPasses` | Falsifiability Test B: genuine snippet → present + recomputed offsets |
| `test_offsets_are_recomputed_not_trusted` | `TestGenuineSpanPasses` | Wrong model offsets overwritten by gate |
| `test_conflicting_field_grounded_per_value` | `TestConflictingField` | Any failed ConflictingValue.evidence → whole field unsupported (D-05) |
| `test_fuzzy_match_above_threshold_grounds` | `TestFuzzyMatching` | Minor whitespace/case diff → grounds successfully |
| `test_fuzzy_match_below_threshold_downgrades` | `TestFuzzyMatching` | Unrelated snippet → unsupported |
| `test_nfkc_ligature_offset_mapping` | `TestNFKCLigature` | fi ligature ↔ "fi" match with correct offsets |
| `test_short_snippet_guard` | `TestShortSnippetGuard` | Sub-MIN_SNIPPET_LEN snippet → unsupported even if in source |
| `test_walker_grounds_nested_fields` | `TestWalker` | Recursive walker grounds both Field[str] attributes in inline model |

**test_sample_fixtures.py** — 5 fixture tests in RED state (DATA-01/02/03):

| Test | Requirement | What It Asserts |
|------|-------------|-----------------|
| `test_rfq_fixture_valid` | DATA-01 | rfq.json exists + RFQ with 8 line_items |
| `test_vendor_fixtures_exist_and_valid` | DATA-02 | 3 vendor fixtures exist + VendorResponse + raw_text > 200 chars |
| `test_vendor_fixture_messiness` | DATA-03 | Per-persona messiness markers (bundled, TBD, week conflicts) |
| `test_cheap_incomplete_has_missing_price` | DATA-03 | cheap vendor has missing-price marker or < 8 dollar amounts |
| `test_polished_fluff_has_conflict` | DATA-03 | fluff vendor has ≥2 different week counts or contradictory scope |

## Verification Results

```
uv run pytest tests/test_grounding_gate.py -q
→ 9 failed — all NotImplementedError (correct RED state; no ImportError)

uv run pytest tests/test_sample_fixtures.py -q
→ 5 failed — all AssertionError on file-existence check (correct RED state; no AttributeError)

from grounding import ground_field, ground_model, DowngradeEntry, DowngradeReport; print('OK')
→ imports OK

grep -n "pytest.raises" tests/test_grounding_gate.py
→ only in docstring comment, no code usage
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

All stubs are intentional Wave 0 artifacts:
- `grounding/gate.py`: All functions raise `NotImplementedError` — implementation lands in plan 02-02.
- `services/ai/tests/test_grounding_gate.py`: Tests in RED state — turn GREEN when 02-02 implements gate.
- `services/ai/tests/test_sample_fixtures.py`: Tests in RED state — turn GREEN when 02-03 generates sample data.

These stubs are the goal of this plan (not defects); they prove the RED→GREEN progression is verifiable before implementation.

## Pre-existing Deferred Issue (Out of Scope)

`test_codegen_drift.py` fails with `Exception: json2ts must be installed` — pre-existing issue requiring the `json-schema-to-typescript` npm package. Unrelated to this plan's changes; 80 other existing tests pass.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. This plan creates test harness and stub code only.

## Self-Check: PASSED

All created files exist:
- FOUND: services/ai/grounding/__init__.py
- FOUND: services/ai/grounding/gate.py
- FOUND: services/ai/grounding/report.py
- FOUND: services/ai/tests/test_grounding_gate.py
- FOUND: services/ai/tests/test_sample_fixtures.py

All commits exist:
- FOUND: ad9110d (Task 1 — grounding package stubs)
- FOUND: f8c722d (Task 2 — test_grounding_gate.py in RED)
- FOUND: 8140d4a (Task 3 — test_sample_fixtures.py in RED)
