---
phase: 02-grounding-gate-messy-data
plan: FIXES
subsystem: api
tags: [pydantic, fastapi, langchain, grounding, testing, vendor-gen]

# Dependency graph
requires:
  - phase: 02-grounding-gate-messy-data
    provides: grounding gate, vendor_gen agent, rfq_gen agent, domain schemas, FastAPI app, test fixtures
provides:
  - Persona dict consistency guard on vendor_gen import
  - Valid JSON mess_spec in LLM prompt (not Python repr)
  - Bounded rfq_text / persona fields on POST /data/vendor-gen
  - Module-level FastAPI HTTPException import
  - budget_range_usd 2-element [min, max] validator on LineItem
  - Module-level import re in test_sample_fixtures.py
  - ponytail comment documenting dict-traversal gap in grounding walker
affects: [03-extraction-agent, 04-comparison-agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level assertions to guard parallel-dict key parity at import time"
    - "json.dumps for LLM template interpolation instead of relying on str() repr"
    - "pydantic Field max_length on API request models to cap LLM call cost"
    - "model_validator(mode='after') for tuple-as-list invariants in structured output"

key-files:
  created: []
  modified:
    - services/ai/agents/vendor_gen.py
    - services/ai/api/app.py
    - services/ai/schemas/domain.py
    - services/ai/grounding/gate.py
    - services/ai/tests/test_sample_fixtures.py

key-decisions:
  - "budget_range_usd validator checks both len==2 AND min<=max (not just length) per fix spec"
  - "mess_spec JSON serialization uses ensure_ascii=False to preserve currency symbols and unicode in instructions"
  - "IN-04 is documentation-only — no dict-traversal code added per spec; ponytail comment placed after elif list block"

requirements-completed: []

# Metrics
duration: 20min
completed: 2026-06-27
---

# Phase 02 (Fixes): Code Review Remediation Summary

**Six targeted correctness/security fixes from REVIEW.md: persona-dict parity guard, JSON-safe LLM prompt serialization, bounded API request fields, hoisted imports, budget range validator, and dict-gap documentation in grounding walker.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-27T00:00:00Z
- **Completed:** 2026-06-27T00:00:00Z
- **Tasks:** 6 fixes + 1 doc comment (7 changes across 5 files)
- **Files modified:** 5

## Accomplishments

- Applied all 6 REVIEW.md items (WR-02, WR-03, WR-04, WR-05, IN-01, IN-03) plus IN-04 doc comment exactly as specified
- All 108 existing tests continue to pass after every fix
- WR-01 and IN-02 deliberately deferred per instructions (left untouched)

## Task Commits

1. **WR-02 + WR-04: vendor_gen.py — persona parity guard + JSON serialization** - `fdec188` (fix)
2. **WR-03 + IN-03: app.py — bounded request fields + hoisted import** - `ee87398` (fix)
3. **WR-05: domain.py — budget_range_usd model_validator** - `e128c4b` (fix)
4. **IN-01 + IN-04: test_sample_fixtures.py + gate.py — import hygiene + doc comment** - `fb5c9e1` (fix)

## Files Created/Modified

- `services/ai/agents/vendor_gen.py` - Added `import json`; module-level assertion on FIXTURE_FILENAMES/MESS_SPECS/FORMAT_LABELS key parity; serialize mess_spec via json.dumps instead of passing list[dict] directly
- `services/ai/api/app.py` - Moved HTTPException to module-level fastapi import; added pydantic Field import; constrained persona (max_length=64) and rfq_text (max_length=200_000) on VendorGenRequest
- `services/ai/schemas/domain.py` - Added model_validator import; added _validate_budget_range validator to LineItem enforcing exactly 2 elements with [0] <= [1]
- `services/ai/grounding/gate.py` - Added ponytail comment after elif isinstance(value, list) block noting dict-valued Field containers are intentionally not traversed in Phase 2
- `services/ai/tests/test_sample_fixtures.py` - Moved two in-function `import re` statements to a single module-level import

## Decisions Made

- The budget range validator checks both the 2-element length constraint AND that `budget_range_usd[0] <= budget_range_usd[1]`, matching the fix spec exactly ("exactly 2 elements with budget_range_usd[0] <= budget_range_usd[1]").
- `json.dumps` uses `ensure_ascii=False` to preserve unicode characters (currency symbols, em-dashes) in the mess_spec instructions, which contain natural language prose.
- WR-01 (`FlagStatus` missing `not-comparable`) and IN-02 (`_check_api_access` error swallowing) are deliberately deferred — left untouched as specified.

## Deviations from Plan

None — all 7 changes applied exactly as specified in the fix list. No additional changes made.

## Issues Encountered

- The worktree was initialized from a historical commit before Phase 2 code merged to main. The `<worktree_branch_check>` reset procedure corrected the worktree base to `3b8feb48` (main HEAD), making all Phase 2 source files available. No code was affected — the reset only updated the working tree to include files already on main.

## Known Stubs

None introduced by these fixes. Existing stubs (ExtractionResult, ComparisonResult) unchanged and already tracked in prior summaries.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes at trust boundaries. The max_length bounds on WR-03 reduce the existing attack surface.

## Self-Check

- [ ] `services/ai/agents/vendor_gen.py` — FOUND
- [ ] `services/ai/api/app.py` — FOUND
- [ ] `services/ai/schemas/domain.py` — FOUND
- [ ] `services/ai/grounding/gate.py` — FOUND
- [ ] `services/ai/tests/test_sample_fixtures.py` — FOUND
- [ ] Commits fdec188, ee87398, e128c4b, fb5c9e1 — FOUND (git log confirmed)
- [ ] 108 tests passing — CONFIRMED

## Self-Check: PASSED

---
*Phase: 02-grounding-gate-messy-data (fixes)*
*Completed: 2026-06-27*
