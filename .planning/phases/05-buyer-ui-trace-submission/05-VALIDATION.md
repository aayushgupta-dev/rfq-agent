---
phase: 5
slug: buyer-ui-trace-submission
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-28
validated: 2026-06-29
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Detailed architecture lives in `05-RESEARCH.md § Validation Architecture` — this is the executable contract derived from it.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python, configured in `services/ai/pyproject.toml`) + Playwright (E2E) |
| **Config file** | `services/ai/pyproject.toml`; Playwright via global v1.58.0 (add `@playwright/test` devDep) |
| **Quick run command** | `cd services/ai && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd services/ai && uv run pytest tests/` + Playwright E2E against running stack |
| **Estimated runtime** | ~20 seconds (pytest) + ~60s (Playwright smoke) |

*Note: `apps/web` has no TS unit framework — thin client, logic lives server-side per CLAUDE.md §5. No TS unit tests warranted.*

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest tests/ -x -q`
- **After every plan wave:** Run full pytest suite + Playwright smoke against local running stack
- **Before `/gsd:verify-work`:** Full pytest suite green AND Playwright E2E buyer journey passes
- **Max feedback latency:** 30 seconds (pytest path)

---

## Per-Task Verification Map

> Per-task rows are completed by the planner/executor once PLAN.md task IDs exist. Requirement → test-type mapping below is the binding contract.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| INPUT-01 | Paste path wraps raw text into VendorResponse | unit | `uv run pytest tests/test_input_wrap.py -x` | ✅ | ✅ green |
| INPUT-02 | File text extraction: PDF/DOCX/XLSX/PPTX → text string | unit | `uv run pytest tests/test_file_extract.py -x` | ✅ | ✅ green |
| INPUT-03 | Sample load path: vendor JSON readable and valid | unit | `test_sample_fixtures.py` | ✅ | ✅ green |
| INPUT-04 | Dynamic output: extraction called live, not hardcoded | E2E | `playwright test` (sample load → live extract) | ✅ | ✅ green |
| UI-01..06 | Buyer screens render correct content + evidence/comparability | E2E | `playwright test` (RFQ/Extraction/Comparison) | ✅ | ✅ green |
| PROMPT-02 | Prompt trace surfaced (input→prompt→output→final) | E2E + unit | `playwright test` (trace screen) + `test_prompts_api.py` | ✅ | ✅ green |
| SHIP-01 | CORS allows Vercel origin; SSE streams through Render | smoke | `test_sse_demo.py` (code) + manual deploy | ✅ | ✅ green (code); deploy → manual-only |
| SHIP-02..05 | README, write-up, demo, architecture diagram present | manual | file existence + reviewer read | ✅ | ✅ files present; quality → manual-only |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `services/ai/tests/test_file_extract.py` — unit tests for file-text dispatcher (PDF/DOCX/XLSX/PPTX)
- [x] `services/ai/tests/test_input_wrap.py` — unit test for `POST /input/raw-text` returns valid `VendorResponse`
- [x] `docs/qa/phase5-playwright.spec.ts` — Playwright E2E covering the full buyer journey (7 tests) per CLAUDE.md §11
- [x] `@playwright/test` in root devDependencies (`^1.61.1`); `playwright.config.ts` → `testDir: ./docs/qa`

*No TypeScript unit tests warranted (thin client; logic lives server-side).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live SSE streams incrementally in deployed demo | SHIP-01 | Requires deployed Render service + real proxy buffering behavior | Deploy, open Network tab, confirm `data:` chunks arrive incrementally not as one blob |
| Submission package is reviewer-compelling | SHIP-02..05 | Quality of prose/diagram/demo is subjective, not assertable | Aerchain-reviewer read-through of README, write-up, demo video, architecture diagram |
| Prompt design quality (30% of grade) | PROMPT-02 | Prompt *design* quality is not mechanically checkable | Peer/human review of each Prompt Pack doc (carry-forward from Phase 3 UAT) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s (pytest ~22s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-06-29

---

## Validation Audit 2026-06-29

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All Wave 0 test files exist and the suite is green (`150 passed, 1 xfailed` in ~22s).
Playwright E2E (`docs/qa/phase5-playwright.spec.ts`, 7 tests) covers the full buyer
journey; `@playwright/test ^1.61.1` wired via `playwright.config.ts`. Every automatable
requirement (INPUT-01..04, UI-01..06, PROMPT-02, SHIP-01 code-level) has a green automated
verify. Remaining items are genuinely manual-only: deployed-SSE behavior, submission-quality
read-through, and prompt-design quality. No auditor spawn needed — no MISSING gaps.
