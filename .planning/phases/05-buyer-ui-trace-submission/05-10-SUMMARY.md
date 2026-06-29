---
phase: 05-buyer-ui-trace-submission
plan: 10
subsystem: ai
tags: [extraction, prompt-pack, grounding, conflicting, total_price, langchain, gpt-5.4]

# Dependency graph
requires:
  - phase: 03-extraction-agent
    provides: extraction.v1.md prompt, ExtractionResult/conflicting envelope, grounding gate, run_extraction wrapper
  - phase: 02-sample-data
    provides: vendor_fluff.json polished-fluff fixture, deterministic sample-fixture test pattern
provides:
  - total_price=conflicting prompt branch + numeric/price conflicting few-shot (Example 5)
  - vendor_fluff sample now carries two contradictory all-in grand totals (USD 1.2M vs $950,000)
  - deterministic CI guard (test_polished_fluff_has_total_price_conflict)
  - live behavioral guard (test_total_price_conflict_live, @pytest.mark.live)
  - prompt-doc grand-total conflict-handling row
affects: [comparison-agent, buyer-ui-extraction-review, prompt-pack, uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Same-field conflict detection is prompt-side model judgment; the grounding gate stays one-directional (never invents the dropped claim — CLAUDE.md §8)"
    - "Behavior-only model judgment is proven by an @pytest.mark.live test, never a mocked fake-conflicting test"

key-files:
  created: []
  modified:
    - services/ai/prompts/extraction.v1.md
    - data/vendor_fluff.json
    - services/ai/tests/test_sample_fixtures.py
    - services/ai/tests/test_extraction_agent.py
    - docs/prompts/extraction-prompt-doc.md

key-decisions:
  - "Edited extraction.v1.md in place (version stays 1) — bugfix within the unchanged ExtractionResult contract; the prompt registry pins id+version, not body hash."
  - "No mocked conflicting test added — same-field conflict is true model judgment; only a live test honestly proves the prompt fix."
  - "grounding/gate.py untouched — by §8 code must not fabricate the dropped second claim to upgrade present→conflicting."

patterns-established:
  - "Pattern: a UAT-discovered model-judgment gap is closed prompt-side (instruction + numeric few-shot anchor) + committed-sample backing + deterministic CI guard + live behavioral proof."

requirements-completed: [EXTRACT-01, EXTRACT-03]

# Metrics
duration: 3min
completed: 2026-06-29
---

# Phase 5 Plan 10: Contradictory Grand-Total Conflict Detection Summary

**Two different stated grand totals now flag total_price=conflicting (both surfaced in values[], never silently resolved) — prompt instruction + a numeric price few-shot, backed by a committed sample contradiction, a deterministic CI guard, and a live behavioral test.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-29T04:57:01Z
- **Completed:** 2026-06-29T05:00:22Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- extraction.v1.md total_price bullet now branches present / missing / **conflicting (>1 distinct grand total)**, instructing the model to surface both totals via values[] and never pick, average, or reconcile.
- Added "Example 5 — conflicting (numeric / grand total)" few-shot mirroring Example 4's values[] envelope, giving the model the numeric/price anchor it previously lacked (the only conflicting few-shot was a timeline narrative).
- Injected a same-field grand-total contradiction into vendor_fluff (USD 1.2M all-in fee vs $950,000 fully inclusive) + an "overall" internal_conflict mess_spec, so the conflicting-on-price path now has committed coverage matching the UAT-reported Cobalt scenario.
- Deterministic CI guard pins both totals; live behavioral guard proves the model actually emits total_price=conflicting.
- prompt-doc conflict-handling table extended with the grand-total row (integrated, not appended).

## Task Commits

Each task was committed atomically:

1. **Task 1: Prompt fix — total_price conflict instruction + price-conflict few-shot** - `d273376` (fix)
2. **Task 2: Committed sample contradiction + deterministic fixture test** - `1d26bde` (test)
3. **Task 3: Live behavioral test — model emits total_price=conflicting** - `e58ef44` (test)

**Plan metadata:** (final docs commit — this SUMMARY + STATE/ROADMAP)

## Files Created/Modified
- `services/ai/prompts/extraction.v1.md` - total_price conflict branch + Example 5 numeric/price conflicting few-shot (version stays 1)
- `data/vendor_fluff.json` - two contradictory all-in grand totals injected into raw_text + "overall" internal_conflict mess_spec
- `services/ai/tests/test_sample_fixtures.py` - test_polished_fluff_has_total_price_conflict (deterministic string-search guard, no LLM)
- `services/ai/tests/test_extraction_agent.py` - test_total_price_conflict_live (@pytest.mark.live behavioral proof)
- `docs/prompts/extraction-prompt-doc.md` - grand-total conflict row added to the conflict-handling table

## Decisions Made
- **In-place v1 edit:** This is a bugfix within the unchanged ExtractionResult contract; output shape and schema are identical, so the prompt stays version 1. Confirmed the registry (test_prompt_registry.py) resolves by id+version, not by prompt-body hash — editing in place does not break it.
- **No mocked conflicting test:** Same-field conflict is genuine model judgment (CLAUDE.md §8). A mocked test feeding a canned conflicting result would assert nothing about the real prompt fix. The live test is the honest behavioral proof; CI gets the deterministic fixture guard.
- **gate.py untouched:** The grounding gate is one-directional by design — it downgrades but must not invent the dropped second claim to upgrade present→conflicting (§8). Detection is prompt-side.

## Deviations from Plan

None - plan executed exactly as written.

The plan's `<action>` for the live test listed minimal RFQ line items "1-2 line items is fine"; the LineItem schema (`extra="forbid"`, required `deliverables: list[str]`) meant the line-item dict had to include `deliverables` — this is following the schema the plan referenced, not a deviation. Verified by constructing both RFQ and VendorResponse standalone (no LLM call) before committing.

## Issues Encountered
None. All three task verify commands and the phase-level non-live suite passed first try (after including the schema-required `deliverables` field in the live test's line item).

## Verify Results
- **Task 1:** `7 conflicting refs` (≥4 required), `few-shot present` — PASS
- **Task 2:** `JSON valid` + `test_polished_fluff_has_total_price_conflict` 1 passed — PASS
- **Task 3:** extraction non-live suite `8 passed, 2 deselected`; `live test collectable (skipped in CI)` — PASS
- **Phase-level non-live suite:** `149 passed, 2 deselected` (the 2 deselected are the live tests) — GREEN, no regression
- **vendor_fluff.json:** valid JSON

## Live / Demo Verification (NOT run here — orchestrator's behavioral proof)
- `cd services/ai && uv run pytest tests/test_extraction_agent.py::test_total_price_conflict_live -m live -x` against a real gpt-5.4 key → expect total_price=conflicting with both 1.2M and 950,000 in values[].
- Playwright (§11): load vendor_fluff via the buyer UI → run extraction → /extraction should show total_price flagged Conflicting with both USD 1.2M and $950,000 in the Gaps & Risks panel; no single number presented as definitive.

## Out of Scope (explicitly excluded by the plan)
- Evidence drill-down (UAT test-7), currency formatting (test-2), regenerate latency (test-3) — untouched.

## Next Phase Readiness
- UAT test-8 (major) closed at the prompt + sample + test layers. Behavioral confirmation (live test / Playwright) is the orchestrator's final proof before handoff.
- No blockers introduced; grounding gate and ExtractionResult contract unchanged, so comparison agent and buyer UI are unaffected.

## Self-Check: PASSED

---
*Phase: 05-buyer-ui-trace-submission*
*Completed: 2026-06-29*
