---
phase: 1
slug: foundation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-27
---

# Phase 1 — Validation Strategy

> Retroactively reconstructed from phase artifacts (5 SUMMARY files) via /gsd:validate-phase.
> Phase 1 (foundation) builds the platform contract + tooling spine: absence-enum schema, codegen
> drift gate, LLM tier factory + access ping, SSE streaming spine, prompt registry, and the Next 16
> UI substrate.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend); no vitest (web has no unit logic worth covering) |
| **Config file** | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd services/ai && uv run pytest -q` |
| **Full suite command** | `cd services/ai && uv run pytest` + web gates (`pnpm --filter @aerchain/web exec tsc --noEmit && eslint . && build`) |
| **Estimated runtime** | ~0.6 s (backend, 90 tests) |

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest -q`
- **After every plan wave:** Run full backend suite + affected web gates
- **Before `/gsd:verify-work`:** Full suite green (currently 90 passed)
- **Max feedback latency:** ~1 second (backend)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PLAT-02 | T-01-01 (supply-chain) | version-pinned + committed lockfiles → reproducible installs | build | `cd apps/web && pnpm exec tsc --noEmit` (cross-package link resolves) | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | PLAT-02 | T-01-02 (gitignore) | `apps/web → @aerchain/shared-types` workspace link type-checks | build | `pnpm --filter @aerchain/web exec tsc --noEmit` | ✅ | ✅ green |
| 01-02-01 | 02 | 2 | PLAT-01 | T-02-04 (validator bypass) | invalid absence-enum combos (missing+value, present+None, conflicting+empty, empty-evidence) raise ValidationError | unit | `cd services/ai && uv run pytest tests/test_field_envelope.py` (34) | ✅ | ✅ green |
| 01-02-02 | 02 | 2 | PLAT-02 | T-02-01 (contract drift) | stale/hand-edited TS contract turns drift test red | unit | `cd services/ai && uv run pytest tests/test_codegen_drift.py` (1) | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | PLAT-03 | T-03-01 (key leak) / T-03-03 (over-tier) | API key never logged; callers pass a tier, never a model string; access-denied vs param-rejection distinguished | unit | `cd services/ai && uv run pytest tests/test_llm_factory.py` (11) | ✅ | ✅ green |
| 01-03-02 | 03 | 2 | PLAT-04 | T-03-02 (DoS) | every emitted SSE `type` is a member of the closed EVENT_TYPES taxonomy; `{type,payload}` shape | unit | `cd services/ai && uv run pytest tests/test_sse_demo.py` (9) | ✅ | ✅ green |
| 01-04-01 | 04 | 2 | PROMPT-01 | T-04-03 (path traversal) | `prompt_id` validated against `^[a-z0-9-]+$` before glob; latest-by-suffix resolution | unit | `cd services/ai && uv run pytest tests/test_prompt_registry.py` (11) | ✅ | ✅ green |
| 01-05-01 | 05 | 3 | FOUND-UPGRADE | T-01-05-SC (supply-chain) | exact version pins + committed lockfile; Turbopack build clean | build | `pnpm --filter @aerchain/web build` | ✅ (no pytest) | ⚠️ manual |
| 01-05-02 | 05 | 3 | FOUND-UPGRADE | T-01-05-INFO | styled shadcn Button renders; workspace-link (FlagStatus) proof preserved | manual (Playwright) | see Manual-Only | ✅ (UAT 9/9) | ⚠️ manual |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky/manual*

Backend totals: **90 tests, all green** (`test_field_envelope.py` 34 · `test_sse_demo.py` 9 · `test_llm_factory.py` 11 · `test_prompt_registry.py` 11 · `test_codegen_drift.py` 1 — plus parametrized cases).

---

## Wave 0 Requirements

*Existing infrastructure covers all automatable phase requirements.* No new test files needed — the
five backend requirements (PLAT-01, PLAT-02, PLAT-03, PLAT-04, PROMPT-01) were each delivered TDD
with committed RED→GREEN tests. FOUND-UPGRADE is inherently manual-only (see below).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Next 16 / React 19.2 / Tailwind v4 / shadcn substrate upgrade + Button render proof | FOUND-UPGRADE | A framework version upgrade has no unit logic to cover; a `next == 16.2.9` assertion would be brittle and duplicate what the build already enforces (PonyTail YAGNI). The build gates + a live render are the meaningful regression guard. | (1) `pnpm --filter @aerchain/web build` compiles on Turbopack with no errors; (2) `tsc --noEmit` + `eslint .` exit 0; (3) `prettier --check 'apps/web/**/*.{ts,tsx,css,json,mjs}'` clean; (4) `pnpm --filter @aerchain/web dev`, then Playwright navigate → confirm a Tailwind-styled shadcn Button renders (themed, rounded) alongside the "Bid Desk — workspace link verified (missing)" FlagStatus line. Screenshot: `docs/demo/01-05-ui-substrate-proof.png`. Full record: `01-05-UAT.md` (9/9 pass). |
| Live gpt-5.4 / gpt-5.4-mini access ping | PLAT-03 | The live ping needs a real `OPENAI_API_KEY` with confirmed model access (the exact account-specific blocker PLAT-03 exists to catch); the unit suite mocks `init_chat_model`. | `cd services/ai && uv run python scripts/verify_access.py` exits 0 and prints both model IDs; or boot `uv run uvicorn api.app:app` — the FastAPI lifespan gate aborts startup loudly on missing access. Live proof captured in `01-03-SUMMARY.md`. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or a documented manual-only justification
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (5 of 6 requirements automated)
- [x] Wave 0 covers all MISSING references (none — no automatable gaps)
- [x] No watch-mode flags
- [x] Feedback latency < 2s (backend ~0.6s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-27

---

## Validation Audit 2026-06-27

| Metric | Count |
|--------|-------|
| Requirements audited | 6 |
| COVERED (automated) | 5 |
| MANUAL-ONLY (by design) | 1 |
| Gaps found (automatable, unfilled) | 0 |
| Tests generated | 0 |

**Verdict:** Phase 1 is Nyquist-compliant. Every testable platform/contract behavior has automated
verification (90 green pytest tests); the sole non-automated requirement (FOUND-UPGRADE) is a
framework upgrade whose regression guard is the build + a documented Playwright render proof, and
PLAT-03's live ping is manual by design. No tests were generated — there were no automatable gaps.
