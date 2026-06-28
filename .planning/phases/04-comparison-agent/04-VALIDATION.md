---
phase: 4
slug: comparison-agent
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (services/ai) |
| **Config file** | services/ai/pyproject.toml |
| **Quick run command** | `cd services/ai && uv run pytest -q tests/test_comparison*.py` |
| **Full suite command** | `cd services/ai && uv run pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest -q tests/test_comparison*.py`
- **After every plan wave:** Run `cd services/ai && uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | — | — | COMPARE-01..05 | — | populated during planning | unit | `cd services/ai && uv run pytest -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Populated by gsd-planner from the RESEARCH.md Validation Architecture section during Phase 4 planning.*

---

## Wave 0 Requirements

- [ ] Comparison test stubs covering COMPARE-01..05 (per RESEARCH.md Validation Architecture)
- [ ] Reuse existing services/ai/tests/conftest.py fixtures (ExtractionResult builders)

*Existing pytest infrastructure (Phases 1–3) covers the framework; only comparison-specific test files are new.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Comparison trace readability for an Aerchain reviewer | COMPARE-03, COMPARE-05 | Prompt/trace design quality is a deliverable-quality judgement, not a code assertion | Render a comparison trace; confirm comparability badges, attention points, and clarification questions read clearly with no fabricated numbers |

*Per-task automated coverage is set during planning; this row tracks the carry-forward deliverable-quality gate from STATE.md.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
