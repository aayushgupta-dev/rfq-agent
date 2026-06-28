---
phase: 04-comparison-agent
plan: "02"
subsystem: services/ai/schemas
tags: [schema, pydantic, tdd, codegen, comparison-agent, draft-result-split]
dependency_graph:
  requires: [04-01]
  provides: [04-03, 04-04]
  affects:
    - services/ai/schemas/domain.py
    - services/ai/schemas/__init__.py
    - packages/shared-types/index.d.ts
    - services/ai/tests/test_comparison_agent.py
tech_stack:
  added: []
  patterns:
    - draft-result-split (ComparisonDraft→ComparisonResult, model target vs code-constructed)
    - StrEnum-fail-closed (ComparisonDimension rejects mis-cased strings)
    - ClampReport-mirrors-DowngradeReport (comparison-level verdict clamp parallels grounding gate)
    - list[BaseModel]-not-dict (pydantic2ts compat — no Record<string,> output)
key_files:
  created: []
  modified:
    - services/ai/schemas/domain.py
    - services/ai/schemas/__init__.py
    - packages/shared-types/index.d.ts
    - services/ai/tests/test_comparison_agent.py
decisions:
  - "ComparisonDraft is the model's structured output target; ComparisonResult is code-constructed — draft/result split closes the model-authors-reliability-critical-surfaces BLOCKER (Review Fix 1+2)"
  - "ComparabilityVerdict(StrEnum) lives in domain.py not envelope.py — resolves WR-01 (D-02)"
  - "ComparisonDimension(StrEnum) added — fail-closed on unrecognized dimension strings (Review Fix 1)"
  - "ClarificationSet moved to domain.py for drift-check scope (Review Fix 12)"
  - "clamp_report: ClampReport is a field ON ComparisonResult, not a sibling key (Pitfall 5 / D-11)"
  - "All sub-models use list[BaseModel] — no dict[str, Model] shapes (pydantic2ts compat, PLAT-02)"
metrics:
  duration: "12 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_created: 0
  files_modified: 4
---

# Phase 04 Plan 02: Schema Redesign — ComparisonResult + ComparisonDraft Summary

Wave 2: replaced the 2-field ComparisonResult stub with a full 15-model schema family, added the model-draft/code-result split, and regenerated the TypeScript contract. The draft/result split is the phase's headline reliability move: `ComparisonDraft` is structurally incapable of carrying `clamp_report`, `line_item_offers`, or `vendor_readiness` — making it impossible for the model to author those surfaces even if the prompt were compromised.

## What Was Built

**services/ai/schemas/domain.py** — 15 new models + 2 StrEnums:

- `ComparabilityVerdict(StrEnum)` — `comparable | partially | not_comparable`; in `domain.py`, never `envelope.py` (D-02/WR-01)
- `ComparisonDimension(StrEnum)` — 6 typed dimension names; rejects mis-cased strings fail-closed (Review Fix 1)
- `ClampEntry` / `ClampReport` — verdict downgrade records; mirrors `DowngradeEntry`/`DowngradeReport` from `grounding/report.py`; `has_downgrades` property
- `DimensionVerdictDraft` / `DimensionComparisonDraft` — model-emitted draft shapes (one per vendor/dimension)
- `ComparisonDraft` — THE model's structured output target; no `clamp_report`, no `line_item_offers`, no `vendor_readiness` (Review Fix 1+2 BLOCKER)
- `DimensionVerdict` / `DimensionComparison` — code-constructed badge matrix (D-01); `model_proposed` kept for D-11 trace diff
- `LineItemOffer` — code-built 8×vendor offer table cell (D-06); `non_equivalence_flag` for bundling/currency mismatch (D-05)
- `VendorReadiness` — qualitative descriptor + X/N count; no sort key, no rank (D-07 guardrail)
- `AttentionPoint` — code-triggered shell; `clarification_generation_failed` trigger_type added (Review Fix 8)
- `ClarificationQuestion` — one question per flagged field (D-09/D-10)
- `ClarificationSet` — moved to `domain.py` so pydantic2ts picks it up (Review Fix 12)
- `FlaggedField` — code-collected input to the clarification prompt (D-09); never model-generated
- `ComparisonResult` (full) — 7 fields; `clamp_report` is a field ON the result, not a sibling key

**services/ai/schemas/__init__.py** — all 15 new types exported for pydantic2ts discovery.

**packages/shared-types/index.d.ts** — regenerated; `ComparabilityVerdict`, `ComparisonDimension` appear as TS string unions; all 15 new models appear as typed interfaces; no `Record<string, ...>` shapes.

**services/ai/tests/test_comparison_agent.py** — two RED stubs made GREEN:
- `test_schema_shape` — asserts required fields, no score/rank/vendor_count, draft/result split, `ClarificationSet` in `domain`, `ComparisonDimension` in `domain`
- `test_no_dict_shapes` — asserts no `dict` origin annotation on any `ComparisonResult` field

## Verification

- `test_codegen_drift.py::test_ts_contract_not_stale` — PASSED
- `test_comparison_agent.py::test_schema_shape` — PASSED (was RED stub)
- `test_comparison_agent.py::test_no_dict_shapes` — PASSED (was RED stub)
- Full suite: 118 passed, 18 failed (all 18 are Wave 1 RED stubs — NotImplementedError — unchanged), 1 xfailed. No regressions.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None introduced. The 18 remaining RED stubs in `test_comparison_agent.py` are Wave 1 intentional stubs (Wave 3 makes them GREEN).

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns. Schema-only change. The plan's STRIDE threat register mitigations are all implemented:

| Threat ID | Status |
|-----------|--------|
| T-04-02-01 | Mitigated — `test_schema_shape` asserts `ComparabilityVerdict.__module__` contains `domain` |
| T-04-02-02 | Mitigated — `test_no_dict_shapes` asserts no dict origin; drift-check passes |
| T-04-02-03 | Mitigated — `test_schema_shape` asserts `vendor_count` not in `model_fields` |
| T-04-02-04 | Mitigated — `ComparisonDraft` structurally has no `clamp_report`; `test_schema_shape` asserts |
| T-04-02-05 | Mitigated — `ComparisonDimension(StrEnum)` rejects `'Commercial'` (test_dimension_enum_fail_closed stub covers Wave 3) |
| T-04-02-06 | Mitigated — `ClarificationSet` in `domain.py`; `test_schema_shape` asserts `__module__` contains `domain` |

## Self-Check

- [x] `services/ai/schemas/domain.py` — modified with 15 new models + 2 StrEnums
- [x] `services/ai/schemas/__init__.py` — exports all 15 new types
- [x] `packages/shared-types/index.d.ts` — regenerated, contains `ComparabilityVerdict` and `ComparisonDraft`
- [x] `services/ai/tests/test_comparison_agent.py` — `test_schema_shape` and `test_no_dict_shapes` GREEN
- [x] Commit `66949e4`: full ComparisonResult + ComparisonDraft schema
- [x] Commit `054236e`: codegen + test stubs GREEN

## Self-Check: PASSED
