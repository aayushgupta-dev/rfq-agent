---
phase: 01-foundation
plan: "02"
subsystem: schema-contract
tags: [pydantic, generics, typescript, codegen, pydantic2ts, json2ts, absence-enum, sse]

dependency_graph:
  requires:
    - phase: 01-foundation/01-01
      provides: pnpm+turbo workspace with json2ts binary; services/ai uv env with pydantic + pydantic-to-typescript
  provides:
    - Generic Field[T] absence envelope with model_validator semantic rules (PLAT-01)
    - FlagStatus StrEnum with 5 members: present/missing/unclear/conflicting/unsupported
    - Evidence model with snippet + char offsets + source_id
    - ConflictingValue[T] generic for conflicting-status entries
    - EventEnvelope with closed Literal SSE taxonomy + EVENT_TYPES constant
    - ErrorPayload with code/message/recoverable (D-10)
    - RFQ/VendorResponse/ExtractionResult/ComparisonResult compiling stubs (D-08)
    - scripts/codegen.py with repo_root() helper + generate() function (PLAT-02)
    - packages/shared-types/index.d.ts — full generated TS contract (overwrites Plan 01 placeholder)
    - tests/test_field_envelope.py — 20 semantic validation tests (PLAT-01 proof)
    - tests/test_codegen_drift.py — drift-check test (PLAT-02 enforcement)
  affects:
    - 01-03 (SSE spine + LLM factory consume EventEnvelope/EVENT_TYPES and the schemas package)
    - 01-04 (prompt registry stubs reference these schemas as the contract)
    - All P2/P3/P4 agents (ExtractionResult/ComparisonResult stubs to be fleshed out)
    - apps/web (consumes packages/shared-types TS contract via workspace:* link)

tech-stack:
  added: []
  patterns:
    - "Generic Field[T] envelope with model_validator: one pydantic generic → clean monomorphized TS via codegen (D-05 confirmed)"
    - "repo_root() helper walks up to pnpm-workspace.yaml — avoids fragile parents[N] index for cross-service path resolution"
    - "Pass absolute __init__.py path to pydantic2ts to avoid Pitfall 1 (directory exists check causes spec_from_file_location failure)"
    - "noqa: UP046 on Generic[T] pydantic classes — PEP 695 class[T] syntax breaks pydantic-to-typescript; ruff suppressed intentionally"
    - "StrEnum replaces (str, Enum) for FlagStatus — cleaner Python 3.12 idiom, verified compatible with pydantic json schema output"

key-files:
  created:
    - services/ai/schemas/__init__.py
    - services/ai/schemas/envelope.py
    - services/ai/schemas/events.py
    - services/ai/schemas/domain.py
    - services/ai/scripts/__init__.py
    - services/ai/scripts/codegen.py
    - services/ai/tests/test_field_envelope.py
    - services/ai/tests/test_codegen_drift.py
  modified:
    - packages/shared-types/index.d.ts

key-decisions:
  - "UP046 noqa suppressed on Generic[T] classes: ruff UP046 wants PEP 695 class[T] syntax which breaks pydantic-to-typescript 2.0.0; kept Generic[T] with noqa comment naming the reason"
  - "UP042 applied: FlagStatus changed from (str, Enum) to StrEnum — verified byte-identical JSON schema output, no codegen impact"
  - "schemas/__init__.py uses absolute __init__.py path for pydantic2ts to avoid Pitfall 1 (when 'schemas' directory exists in cwd, pydantic2ts takes file-loading path via spec_from_file_location which fails for packages)"
  - "Decimal fields codegen to string in TS (value?: string | null) — correct, JSON has no decimal type; UI side confirmed in Plan 05"

patterns-established:
  - "Absence-enum contract: every domain fact uses Field[T] with model_validator semantic rules — invalid combos raise ValidationError at schema boundary, not at the UI or agent level"
  - "Codegen-as-test: drift-check test in pytest regenerates TS to temp dir, byte-compares — stale contract turns test red, blocking any merge"
  - "repo_root() centralized: one place for cross-service path resolution; drift test imports it rather than recomputing independently"

requirements-completed: [PLAT-01, PLAT-02]

duration: 6min
completed: "2026-06-27"
---

# Phase 01 Plan 02: Contract Primitives and Codegen Summary

**Generic Field[T] absence envelope with semantic model_validator enforcement + pydantic-to-TypeScript codegen producing clean FieldStr/FieldDecimal/FieldInt with a pytest drift-check that goes red on schema drift.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-27T11:16:44Z
- **Completed:** 2026-06-27T11:22:50Z
- **Tasks:** 2 (Task 1 TDD: RED + GREEN; Task 2 codegen + drift-check)
- **Files modified:** 9 (8 created, 1 overwritten)

## Accomplishments

- Defined `Field[T]` generic absence envelope with `model_validator(mode="after")` enforcing all 5-state semantic rules in code — invalid combinations (missing+value, present+None, conflicting+empty values[]) raise `ValidationError` at the schema boundary, not silently pass through (PLAT-01)
- Defined `EventEnvelope` with closed `Literal["status","partial","result","error","done"]` type and `EVENT_TYPES` constant — Plan 03 imports the constant to validate SSE emitter output without duplicating the tuple
- Built `codegen.py` with `repo_root()` helper that walks `pnpm-workspace.yaml` upward; `generate()` overwrites `packages/shared-types/index.d.ts` with the full pydantic-derived TS contract — proves D-05 by producing clean `FieldStr`, `FieldDecimal`, `FieldInt` interfaces with no index signature
- Drift-check test regenerates to a temp dir and byte-compares to committed file — verified red on un-regenerated schema change, green when in sync (PLAT-02)

## Task Commits

| Task | Commit | Message |
|------|--------|---------|
| RED (TDD) | e8ce16c | `test(01-02): add failing tests for Field[T] absence envelope semantics (RED)` |
| Task 1 GREEN | 1357db7 | `feat(01-02): define Field[T] absence envelope, event taxonomy, and domain stubs (PLAT-01)` |
| Task 2 | fc181ea | `feat(01-02): codegen script + drift-check test; generate committed TS contract (PLAT-02, D-14)` |

## TDD Gate Compliance

- RED commit: e8ce16c (`test(01-02): ...`) — 20 failing tests
- GREEN commit: 1357db7 (`feat(01-02): ...`) — 20 passing tests
- No REFACTOR commit needed (code was clean from the start)

## Files Created/Modified

- `services/ai/schemas/__init__.py` — re-exports all contract types for `pydantic2ts` discovery
- `services/ai/schemas/envelope.py` — `FlagStatus` (StrEnum), `Evidence`, `ConflictingValue[T]`, `Field[T]` with `model_validator` semantic rules
- `services/ai/schemas/events.py` — `EVENT_TYPES` tuple constant, `ErrorPayload`, `EventEnvelope` (closed Literal)
- `services/ai/schemas/domain.py` — `RFQ`, `VendorResponse`, `ExtractionResult`, `ComparisonResult` compiling stubs (Field[str], Field[Decimal], Field[int] across them)
- `services/ai/scripts/__init__.py` — makes scripts a package
- `services/ai/scripts/codegen.py` — `repo_root()` + `schemas_path()` + `generate()` codegen entry point
- `services/ai/tests/test_field_envelope.py` — 20 semantic validation tests (all behaviors from plan)
- `services/ai/tests/test_codegen_drift.py` — drift-check test (imports `repo_root` from `scripts.codegen`)
- `packages/shared-types/index.d.ts` — generated TS contract (replaces Plan 01 placeholder)

## Decisions Made

- **UP046 noqa on Generic[T]:** ruff UP046 suggests PEP 695 `class Foo[T]` syntax (Python 3.12+). Suppressed with `# noqa: UP046` because pydantic-to-typescript 2.0.0 does not handle PEP 695 type parameters — the RESEARCH.md-verified `Generic[T]` pattern must be preserved. Comment names the reason explicitly.
- **StrEnum for FlagStatus:** Changed from `(str, Enum)` to `StrEnum` per ruff UP042 — verified identical JSON schema output, no codegen regression.
- **Absolute path to `schemas/__init__.py`:** When passing `"schemas"` (dotted name) to `pydantic2ts`, `os.path.exists("schemas")` returns `True` from `services/ai/` cwd, triggering `spec_from_file_location` which fails for packages. Solution: pass the absolute path to `schemas/__init__.py` — triggers the file-loading branch correctly (Pitfall 1 from RESEARCH.md).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used absolute `schemas/__init__.py` path instead of dotted module name**
- **Found during:** Task 2 (running codegen script)
- **Issue:** `generate_typescript_defs("schemas", ...)` with dotted module name failed with `spec_from_file_location failed for schemas` because pydantic2ts checks `os.path.exists("schemas")` first — when that returns True (the directory exists in cwd), it uses the file-loading path which fails for packages. The RESEARCH.md Pitfall 1 warned about this; the plan specified the dotted name approach.
- **Fix:** Added `schemas_path()` helper returning the absolute path to `schemas/__init__.py`; passed that to `generate_typescript_defs` instead of the dotted name. Documented with a comment explaining the pydantic2ts internals.
- **Files modified:** `services/ai/scripts/codegen.py`
- **Verification:** `uv run python scripts/codegen.py` runs cleanly; drift test passes
- **Committed in:** fc181ea (Task 2 commit)

**2. [Rule 1 - Bug] Suppressed ruff UP046 on Generic[T] with noqa comment**
- **Found during:** Task 1 ruff check
- **Issue:** ruff UP046 flagged `class Field(BaseModel, Generic[T])` and `class ConflictingValue(BaseModel, Generic[T])` as needing PEP 695 type parameter syntax. Auto-fix would break pydantic-to-typescript compatibility.
- **Fix:** Added `# noqa: UP046` with a comment explaining pydantic-to-typescript incompatibility. Applied `StrEnum` (UP042) which is safe.
- **Files modified:** `services/ai/schemas/envelope.py`
- **Committed in:** 1357db7 (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes essential for correct operation. No scope creep — the codegen path fix was called out in Pitfall 1 of RESEARCH.md; the ruff noqa is preserving the verified pattern.

## Known Stubs

- `services/ai/schemas/domain.py` — `RFQ`, `VendorResponse`, `ExtractionResult`, `ComparisonResult` are intentional Phase 1 stubs with placeholder fields (marked `# ponytail:` comments). Full field shapes land in P2/P3/P4 respectively. These stubs exist to prove the generic Field[T] codegen pipeline; they are not data-flow gaps for this plan's goal.

## Threat Flags

No new threat surface. T-02-01 (contract drift) is mitigated by the drift-check test as designed. T-02-04 (model_validator bypass) is mitigated by the semantic validator running on every `model_validate` call (confirmed in tests).

## Gap Closure (2026-06-27)

Three grounding-enforcement gaps identified during code review (01-REVIEW.md) and confirmed by the verifier (01-VERIFICATION.md) were closed via TDD after plan completion:

| Gap | Fix | Commits |
|-----|-----|---------|
| CR-01: `Field[present]` accepted with `evidence=[]`; `Field[unclear]+value` accepted with `evidence=[]` | Added evidence non-empty check in `_validate_absence_semantics` for `present` and `unclear`-with-value branches | RED: 9610284 / GREEN: 0ebabb4 |
| CR-02: `Evidence` permitted `char_start<0` and `char_end<=char_start` | Added `Evidence._validate_offsets` model_validator enforcing `char_start>=0` and `char_end>char_start`; updated docstring to be precise about what is vs. is not validated at this layer | 0ebabb4 |
| CR-03: `Field[conflicting]` ConflictingValues permitted with `evidence=[]` | Extended conflicting branch to iterate `values[]` and reject any entry with empty evidence | 0ebabb4 |

10 new tests added to `test_field_envelope.py` (30 total). Full suite: **85 passed, 1 warning**. `packages/shared-types/index.d.ts` regenerated to reflect the new `Evidence` validator. PLAT-01 is now fully satisfied.

## Self-Check: PASSED

- `services/ai/schemas/envelope.py` exists with `Field[T]` + `model_validator` — FOUND
- `services/ai/schemas/events.py` exists with `EVENT_TYPES` tuple (5 members) — FOUND
- `services/ai/schemas/domain.py` exists with 4 compiling stubs — FOUND
- `services/ai/scripts/codegen.py` exists with `repo_root()` function — FOUND
- `services/ai/tests/test_field_envelope.py` — 20 tests, all pass — CONFIRMED
- `services/ai/tests/test_codegen_drift.py` — 1 test, passes; red on drift — CONFIRMED
- `packages/shared-types/index.d.ts` contains `FieldStr`, `FieldDecimal`, `FieldInt` — CONFIRMED
- No `[k: string]` index signature in generated TS — CONFIRMED
- No empty `export interface Strict {}` in generated TS — CONFIRMED
- `repo_root()` resolves to git root — CONFIRMED
- `git diff --exit-code packages/shared-types/index.d.ts` exits 0 after codegen — CONFIRMED
- Commits e8ce16c (RED), 1357db7 (GREEN), fc181ea (codegen) exist — CONFIRMED
