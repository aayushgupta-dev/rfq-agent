---
phase: 02-grounding-gate-messy-data
plan: "02"
subsystem: services/ai
tags:
  - grounding
  - gate
  - GREEN-state
  - EXTRACT-04
  - wave-2
dependency_graph:
  requires:
    - plan 02-01 (grounding package stubs + RED-state test harness)
  provides:
    - grounding/gate.py — full implementation: _normalize_with_map, _match_exact, _match_fuzzy, _ground_evidence_item, ground_field, ground_model
    - rapidfuzz added to pyproject.toml [project.dependencies]
    - 13 EXTRACT-04 tests GREEN (9 original + 4 new)
  affects:
    - plan 02-03 (extraction agent can now call ground_field/ground_model on Field[T] results)
    - plan 03 (extraction pipeline uses grounding gate; sources keyed by source_id)
tech_stack:
  added:
    - rapidfuzz>=3.14.5 (PyPI VERIFIED — MIT, 6-year history, 25M/wk downloads)
  patterns:
    - Two-stage normalization with dual offset map (stage1_to_orig + surviving_positions composition)
    - Trim-together leading/trailing whitespace to maintain map-length invariant
    - partial_ratio_alignment with dest_end-1 exclusive-end fix (Pitfall 2)
    - Schema-agnostic recursive Field[T] walker via type(obj).model_fields
    - Pure functions returning new objects via model_copy — never mutate (D-06)
    - Conservative conflicting-field downgrade: any failed ConflictingValue.evidence → whole field unsupported
key_files:
  created: []
  modified:
    - services/ai/grounding/gate.py
    - services/ai/pyproject.toml
    - services/ai/uv.lock
    - services/ai/tests/test_grounding_gate.py
decisions:
  - "D-01 enforced: gate ignores model-supplied char_start/char_end entirely — all offsets recomputed"
  - "D-02 moderate normalization: NFKC+casefold, smart-quotes, dashes; currency symbols preserved"
  - "D-03 fuzzy threshold 90.0 calibrated: minor-whitespace diffs score ~95+, fabricated spans score <90"
  - "D-05 conservative conflicting-field tradeoff: any failed ConflictingValue.evidence downgrades whole Field"
  - "D-06 pure functions: model_copy(update=...) throughout, original objects never mutated"
  - "type(obj).model_fields instead of obj.model_fields: pydantic v2.11 deprecation fix"
metrics:
  duration_minutes: 20
  completed: "2026-06-27"
  tasks_completed: 2
  files_created: 0
  files_modified: 4
---

# Phase 02 Plan 02: Grounding Gate Implementation Summary

Two-stage NFKC normalization gate with exacte+fuzzy matching that recomputes evidence spans and downgrades fabricated facts to `unsupported` — all 13 EXTRACT-04 tests GREEN.

## What Was Built

**`grounding/gate.py` — full implementation** replacing all five `NotImplementedError` stubs:

### `_normalize_with_map(text)`

Two-stage normalization building a composed offset map:

- **Stage 1:** NFKC + smart-quote/dash normalization + casefold per character, extending `stage1_to_orig[]` for each NFKC-expanded character (e.g. `ﬁ` U+FB01 → "fi" maps two stage1 positions to the same original index).
- **Stage 2:** Whitespace collapse tracking `surviving_positions[]` into the stage1 string.
- **Trim-together:** Leading/trailing whitespace stripped from both the normalized string and `surviving_positions` simultaneously — stripping the string alone would leave an index skew.
- **Composition:** `orig_indices[i] = stage1_to_orig[surviving_positions[i]]` — O(N), exact.

### `_match_exact` / `_match_fuzzy`

- Exact: `norm_source.find(norm_snippet)` → remap via `orig_indices`.
- Fuzzy: `partial_ratio_alignment(norm_snippet, norm_source, score_cutoff=FUZZY_THRESHOLD)` → `orig_indices[result.dest_end - 1] + 1` for the exclusive end (Pitfall 2 guard).

### `_ground_evidence_item`

Per-evidence helper: empty-snippet guard → empty-source guard → `MIN_SNIPPET_LEN` guard → exact → fuzzy. Returns `(new_Evidence, None)` on success or `(None, DowngradeEntry)` on failure. `field_status` is passed from the enclosing field (not hardcoded) so `DowngradeEntry.original_status` is accurate.

### `ground_field`

- `missing`/`unsupported`: pass-through immediately.
- `conflicting`: iterates `field.values[]`, grounds each `ConflictingValue.evidence` independently; any failure → whole field downgraded to `unsupported` (conservative tradeoff, D-05).
- `present`/`unclear`: iterates `field.evidence`; any missing `source_id` or unlocatable snippet → downgrade all.

### `ground_model` / `_walk_and_ground`

Schema-agnostic recursive walker using `type(obj).model_fields` (avoids pydantic v2.11 instance-access deprecation). Handles `EnvelopeField`, nested `BaseModel`, and `list[]` recursion. Returns `model_copy(update=updates)` at every level — inputs never mutated.

### New tests added (4)

| Test | Class | Behavior |
|------|-------|----------|
| `test_nfkc_ligature_offset_roundtrip` | `TestNormalizeWithMap` | `ﬁ` → orig_indices roundtrip to `ﬁ` in source |
| `test_normalize_strips_leading_trailing_consistently` | `TestNormalizeWithMap` | `len(normalized) == len(orig_indices)` after trim-together |
| `test_missing_source_id_downgrades` | `TestSourceIdMissing` | unknown source_id → unsupported + reason "source_id not in sources" |
| `test_ground_model_does_not_mutate_input` | `TestWalker` | original Field object status unchanged after ground_model() |

## Verification Results

```
uv run pytest tests/test_grounding_gate.py -v
→ 13 passed in 0.04s (0 failed, 0 warnings)

Key tests:
  TestFabricatedSpanDowngrade::test_fabricated_span_is_downgraded       PASSED (Test A)
  TestGenuineSpanPasses::test_genuine_span_passes_grounding             PASSED (Test B)
  TestGenuineSpanPasses::test_offsets_are_recomputed_not_trusted        PASSED
  TestConflictingField::test_conflicting_field_grounded_per_value       PASSED
  TestFuzzyMatching::test_fuzzy_match_above_threshold_grounds           PASSED
  TestFuzzyMatching::test_fuzzy_match_below_threshold_downgrades        PASSED
  TestNFKCLigature::test_nfkc_ligature_offset_mapping                  PASSED
  TestShortSnippetGuard::test_short_snippet_guard                       PASSED
  TestWalker::test_walker_grounds_nested_fields                         PASSED
  TestWalker::test_ground_model_does_not_mutate_input                   PASSED
  TestNormalizeWithMap::test_nfkc_ligature_offset_roundtrip             PASSED
  TestNormalizeWithMap::test_normalize_strips_leading_trailing_consistently PASSED
  TestSourceIdMissing::test_missing_source_id_downgrades                PASSED

Full suite (excluding pre-existing json2ts failure): 93 passed, 1 warning
Pre-existing failures (out of scope): test_codegen_drift.py (json2ts not installed),
  test_sample_fixtures.py 5 tests (data/rfq.json not yet generated — plan 02-03).
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pydantic v2.11 model_fields instance-access deprecation**
- **Found during:** Task 2 — first full test run showed PydanticDeprecatedSince211 warning
- **Issue:** `obj.model_fields` in `_walk_and_ground` accessed the attribute on the instance; pydantic v2.11 deprecates this in favor of class-level access
- **Fix:** Changed to `type(obj).model_fields` — semantically identical, warning-free, forward-compatible with pydantic v3
- **Files modified:** `services/ai/grounding/gate.py`
- **Commit:** 41ab8e1 (included in same commit)

### Plan Structure Note

Tasks 1 and 2 were implemented in a single commit (`41ab8e1`) because the helper functions (`_normalize_with_map`, `_match_exact`, `_match_fuzzy`) and the high-level functions (`ground_field`, `ground_model`) share the same internal helper `_ground_evidence_item`. Splitting them would have left an intermediate state with importable but broken code. The plan's logical split is preserved in the commit message structure.

## FUZZY_THRESHOLD Calibration

Starting threshold **90.0 passes all tests without adjustment**:
- `test_fuzzy_match_above_threshold_grounds`: snippet with extra space + lowercase scores above threshold → PASS
- `test_fuzzy_match_below_threshold_downgrades`: unrelated snippet scores below threshold → PASS

Calibration note in gate.py: "genuine minor-whitespace diffs score ~95+; set to 90.0 to accept genuine fuzzy matches while rejecting fabricated spans."

## Known Stubs

None — this plan implements the gate fully. All `NotImplementedError` stubs from plan 02-01 are replaced.

The following remain RED-state in other test files (out of scope for this plan):
- `tests/test_sample_fixtures.py` — 5 tests waiting for plan 02-03 sample data generation.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. This plan implements pure, LLM-free, deterministic Python code. The T-02-03 through T-02-SC mitigations from the plan's threat register are all implemented:
- T-02-03 (model-supplied offsets): gate ignores them entirely, recomputes via _normalize_with_map
- T-02-04 (model-asserted verified flag): no such field in schema; gate reads only raw snippet vs source
- T-02-05 (fabricated short snippet): MIN_SNIPPET_LEN=15 guard + FUZZY_THRESHOLD=90.0
- T-02-SC (rapidfuzz install): VERIFIED package, no blocking checkpoint needed

## Self-Check: PASSED

Files modified exist:
- FOUND: services/ai/grounding/gate.py
- FOUND: services/ai/pyproject.toml
- FOUND: services/ai/uv.lock
- FOUND: services/ai/tests/test_grounding_gate.py

Commit exists:
- FOUND: 41ab8e1 (feat(02-02): implement grounding gate)
