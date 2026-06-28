---
phase: 5
slug: buyer-ui-trace-submission
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-28
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
| INPUT-01 | Paste path wraps raw text into VendorResponse | unit | `uv run pytest tests/test_input_wrap.py -x` | ❌ W0 | ⬜ pending |
| INPUT-02 | File text extraction: PDF/DOCX/XLSX/PPTX → text string | unit | `uv run pytest tests/test_file_extract.py -x` | ❌ W0 | ⬜ pending |
| INPUT-03 | Sample load path: vendor JSON readable and valid | unit | existing `test_sample_fixtures.py` | ✅ | ⬜ pending |
| INPUT-04 | Dynamic output: extraction called live, not hardcoded | E2E | `playwright test` | ❌ W0 | ⬜ pending |
| UI-01..06 | Buyer screens render correct content + evidence/comparability | E2E | `playwright test` | ❌ W0 | ⬜ pending |
| PROMPT-02 | Prompt trace surfaced (input→prompt→output→final) | E2E | `playwright test` (trace screen) | ❌ W0 | ⬜ pending |
| SHIP-01 | CORS allows Vercel origin; SSE streams through Render | smoke | `curl -N` + manual browser test | ❌ W0 | ⬜ pending |
| SHIP-02..05 | README, write-up, demo, architecture diagram present | manual | file existence + reviewer read | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `services/ai/tests/test_file_extract.py` — unit tests for file-text dispatcher (PDF/DOCX/XLSX/PPTX)
- [ ] `services/ai/tests/test_input_wrap.py` — unit test for `POST /input/raw-text` returns valid `VendorResponse`
- [ ] `docs/qa/phase5-playwright.spec.ts` (or `.py`) — Playwright E2E covering the full buyer journey per CLAUDE.md §11
- [ ] `@playwright/test` in root devDependencies (`pnpm add -D -w @playwright/test`)

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
