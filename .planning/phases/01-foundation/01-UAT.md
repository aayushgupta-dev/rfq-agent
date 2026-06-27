---
status: complete
phase: 01-foundation
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md]
started: 2026-06-27T12:30:35Z
updated: 2026-06-27T12:33:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Fresh checkout installs reproducibly from committed lockfiles (`pnpm install --frozen-lockfile`, `uv sync --frozen` both exit 0) and the FastAPI service boots — lifespan startup gate runs verify_access() and reaches "Application startup complete" without error.
result: pass

### 2. Monorepo Workspace Link + Web Quality Gates
expected: `apps/web` imports `FlagStatus` from `@aerchain/shared-types` via `workspace:*` and the link resolves end-to-end. `tsc --noEmit`, `eslint .`, and `prettier --check` all pass clean on apps/web.
result: pass

### 3. Full Python Test Suite
expected: `uv run pytest` from services/ai passes all tests (schema semantics, codegen drift, LLM factory, SSE demo, prompt registry).
result: pass

### 4. Absence-Envelope Schema Validation (PLAT-01)
expected: `Field[T]` enforces all 5-state semantic rules in code — invalid combinations (missing+value, present+None, present/unclear with empty evidence, conflicting with empty values) raise ValidationError at the schema boundary, not silently pass. Evidence rejects char_start<0 / char_end<=char_start.
result: pass

### 5. Codegen Drift Check (PLAT-02)
expected: `python scripts/codegen.py` regenerates `packages/shared-types/index.d.ts` and `git diff --exit-code` is clean — committed TS contract matches the pydantic source (no drift). Drift-check test goes red when they diverge.
result: pass

### 6. Ruff Lint Gate (services/ai)
expected: `uv run ruff check .` from services/ai passes clean (the quality gate every SUMMARY self-check claims passes).
result: pass
note: "Found failing during UAT (E501 at tests/test_field_envelope.py:137, 103>100 — introduced by the 01-02 gap-closure tests; 01-02 SUMMARY wrongly claimed ruff clean). Fixed in commit 241d017 by wrapping the Field[Decimal] constructor. `ruff check .` now passes clean. Separate pre-existing finding (not fixed, out of scope): `ruff format --check .` reports 6 repo-wide files unformatted — ruff format was never consistently enforced; the claimed gate is `ruff check`, which is green."

### 7. LLM Tier Factory + Live Model Access (PLAT-03, D-15, D-16)
expected: `uv run python scripts/verify_access.py` pings both tiers and exits 0, printing reasoning model `gpt-5.4` and cheap model `gpt-5.4-mini` as accessible. The lifespan startup gate aborts boot loudly if access is missing.
result: pass

### 8. SSE Streaming Spine (PLAT-04, D-09)
expected: With uvicorn running, `curl -N /stream/demo` emits the full closed taxonomy in `data: {json}` SSE format in order: status → partial → result → done. Each event is `{type, payload}` only, every type drawn from EVENT_TYPES.
result: pass

### 9. Prompt Registry Load + Traversal Guard (PROMPT-01, D-11/12/13)
expected: `load(id)` resolves all 7 versioned prompt stubs by id (rfq-gen, vendor-gen, messy-data-gen, ui-ux-gen, extraction, comparison reasoning-tier; clarification cheap-tier). A path-traversal id (`../etc/passwd`) raises ValueError; an unknown id raises KeyError.
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "`uv run ruff check .` from services/ai passes clean (the foundation quality gate the SUMMARY self-checks claim passes)"
  status: resolved
  reason: "ruff check failed — E501 line too long (103 > 100) at tests/test_field_envelope.py:137. The line `f: Field[Decimal] = Field[Decimal](status=FlagStatus.present, value=Decimal(\"9.99\"), evidence=[ev])` is 103 chars. Introduced by the post-plan gap-closure tests appended to 01-02 (test_field_decimal_present); the 01-02 SUMMARY self-check wrongly asserts ruff passes."
  severity: minor
  test: 6
  root_cause: "Line 137 of services/ai/tests/test_field_envelope.py is 103 chars, exceeding the 100-char ruff line-length limit. Added during the 01-02 gap-closure round (CR-01/02/03) without a final `ruff check` re-run, so the regression slipped past the self-check claim."
  resolution: "Fixed directly during UAT (commit 241d017): wrapped the Field[Decimal] constructor across lines. `uv run ruff check .` now passes clean; full pytest suite still 90 passed."
  artifacts:
    - path: "services/ai/tests/test_field_envelope.py"
      issue: "Line 137 exceeded 100-char limit (E501) — now wrapped"
  debug_session: ""

## Notes — pre-existing findings (not fixed; out of UAT scope)

- `ruff format --check .` reports 6 repo-wide files unformatted (e.g. tests/test_codegen_drift.py). `ruff format` was never consistently enforced across Phase 1. The documented/claimed gate is `ruff check` (now green); `ruff format` conformance is a separate cleanup worth a `/gsd:fast` pass before Phase 2 but is not a Phase 1 acceptance criterion.
