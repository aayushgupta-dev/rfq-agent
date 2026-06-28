---
phase: 05-buyer-ui-trace-submission
plan: "01"
subsystem: testing
tags: [pytest, playwright, xfail, red-stubs, e2e, tdd]

requires:
  - phase: 04-comparison-agent
    provides: "Comparison agent + domain schemas (VendorResponse, ExtractionResult)"

provides:
  - "6 strict-xfail Python test stubs for POST /extract/file-text and POST /input/raw-text (RED gate for Wave 1)"
  - "Playwright E2E spec covering all 5 buyer screens in serial execution"
  - "playwright.config.ts at monorepo root"
  - "@playwright/test added to root devDependencies"

affects: [05-02, 05-04, 05-06]

tech-stack:
  added: ["@playwright/test ^1.61.1"]
  patterns:
    - "Strict-xfail stubs (not skip) guarantee RED state — xpass errors out, preventing silent drift to GREEN"
    - "TestClient(app) without context manager skips lifespan (no OpenAI key needed in unit tests)"
    - "Playwright serial describe block: tests share browser/session state for stateful flows"

key-files:
  created:
    - services/ai/tests/test_file_extract.py
    - services/ai/tests/test_input_wrap.py
    - docs/qa/phase5-playwright.spec.ts
    - playwright.config.ts
  modified:
    - package.json
    - pnpm-lock.yaml

key-decisions:
  - "strict-xfail not pytest.mark.skip: strict=True means an unexpected PASS becomes an ERROR, guaranteeing the RED state is real until Plan 05-02 removes the markers"
  - "TestClient(app) without context manager: same pattern as test_sse_demo.py, skips lifespan/verify_access(), no live OpenAI key required for RED stubs"
  - "Playwright serial describe: buyer journey is stateful (vendor loaded in step 2 is needed in step 3); serial prevents ordering-fragile failures"
  - "data-testid contracts documented in spec comment: implementation tasks (05-04/05-06) know exactly which testids to add"

patterns-established:
  - "Wave 0 = RED stubs only, no production code: Nyquist contract enforced before any implementation"
  - "xfail(strict=True) is the project standard for Wave 0 stubs"

requirements-completed:
  - INPUT-01
  - INPUT-02

duration: 8min
completed: 2026-06-28
---

# Phase 05 Plan 01: Nyquist Test Infrastructure Summary

**6 strict-xfail Python stubs (file-text + raw-text routes) and a 7-test serial Playwright E2E spec covering the full buyer journey — Wave 0 RED gate before any implementation**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-28T11:28:39Z
- **Completed:** 2026-06-28T11:36:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `test_file_extract.py` with 5 strict-xfail stubs covering PDF/DOCX/XLSX/PPTX + weak-extraction cases for POST /extract/file-text
- Created `test_input_wrap.py` with 1 strict-xfail stub asserting POST /input/raw-text returns a VendorResponse-valid body
- Created `docs/qa/phase5-playwright.spec.ts` with 7 tests in a serial describe block covering all 5 buyer screens (RFQ, vendor input, extraction, comparison, trace, empty-state)
- Added `playwright.config.ts` at monorepo root; added `@playwright/test` to root devDependencies

## Task Commits

1. **Task 1: RED stubs for file-text and raw-text wrap endpoints** - `2e6596d` (test)
2. **Task 2: Playwright E2E spec for full buyer journey** - `2f25920` (test)

## Files Created/Modified

- `services/ai/tests/test_file_extract.py` — 5 strict-xfail stubs for POST /extract/file-text dispatcher (PDF/DOCX/XLSX/PPTX + weak extraction)
- `services/ai/tests/test_input_wrap.py` — 1 strict-xfail stub for POST /input/raw-text → VendorResponse contract round-trip
- `docs/qa/phase5-playwright.spec.ts` — 7-test serial Playwright spec for the full 5-screen buyer journey
- `playwright.config.ts` — monorepo Playwright config, baseURL via env fallback
- `package.json` — @playwright/test ^1.61.1 added to root devDependencies
- `pnpm-lock.yaml` — lockfile updated

## Decisions Made

- `strict=True` on all xfail markers: an unexpected PASS becomes a test ERROR, preventing silent drift from RED to GREEN without implementing the route. Plan 05-02 removes markers after implementation.
- `TestClient(app)` without context manager (no lifespan): same as `test_sse_demo.py` — skips `verify_access()` so no live OpenAI key is needed for RED stubs.
- `test.describe.serial`: buyer journey is stateful; the Cheap/Thorough vendor loaded in test 2 must still be in session for test 3. Serial prevents ordering-fragile failures.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 05-02 (GREEN) can proceed: implement POST /extract/file-text and POST /input/raw-text, then remove all xfail markers; pytest will confirm GREEN (6 tests pass).
- Playwright spec is ready to run against the live app from Wave 5 onward.
- data-testid contracts documented in spec comments give Plans 05-04/05-06 the exact testid list to implement.

## Self-Check: PASSED

- `services/ai/tests/test_file_extract.py` — FOUND
- `services/ai/tests/test_input_wrap.py` — FOUND
- `docs/qa/phase5-playwright.spec.ts` — FOUND
- `playwright.config.ts` — FOUND
- Commits `2e6596d` and `2f25920` — FOUND in git log
- pytest: 6 xfailed, 0 errors, 0 skips
- playwright --list: 7 tests

---
*Phase: 05-buyer-ui-trace-submission*
*Completed: 2026-06-28*
