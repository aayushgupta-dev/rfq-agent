---
phase: 3
slug: extraction-agent
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `03-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/test_extraction_agent.py -x` |
| **Full suite command** | `uv run pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds (mocked LLM; no live calls in unit tests) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_extraction_agent.py tests/test_grounding_gate.py tests/test_field_envelope.py -x`
- **After every plan wave:** Run `uv run pytest tests/ -x`
- **Before `/gsd:verify-work 3`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

> Task IDs finalized by the planner; rows below map each phase requirement to its automated proof.
> The planner MUST attach each row's command to the matching task's `<automated>` verify block.

| Req | Wave | Behavior | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----|------|----------|-----------------|-----------|-------------------|-------------|--------|
| EXTRACT-01 | 1 | `ExtractionResult` covers all 8 categories; `vendor_name` is plain `str` (Pitfall 5 fix) | N/A | unit | `uv run pytest tests/test_extraction_agent.py::test_schema_shape -x` | ❌ W0 | ⬜ pending |
| EXTRACT-02 | 2 | Every `present`/`unclear` field has non-empty evidence; evidence passes grounding | Grounding code-enforced (no model `verified` flag) | unit | `uv run pytest tests/test_extraction_agent.py::test_evidence_required -x` | ❌ W0 | ⬜ pending |
| EXTRACT-03 | 2 | `missing`/`unclear`/`conflicting` never `None`-collapsed; model never fills missing | N/A | unit | `uv run pytest tests/test_field_envelope.py -x` | ✅ | ⬜ pending |
| EXTRACT-05 | 2 | `LengthFinishReasonError` → `error` event `{recoverable: true}`, no parse; refusal → `{recoverable: false}` | No partial/truncated output ever parsed | unit (mocked) | `uv run pytest tests/test_extraction_agent.py::test_truncation_raises_error_event -x` | ❌ W0 | ⬜ pending |
| EXTRACT-05 | 1 | `unsupported` fields carry no value/evidence (envelope model_validator) | N/A | unit | `uv run pytest tests/test_field_envelope.py -x` | ✅ | ⬜ pending |
| walker | 1 | Every `Field[T]` in `ExtractionResult` reached by `_walk_and_ground` (closes IN-04) | No grounded field silently bypassed | unit | `uv run pytest tests/test_extraction_agent.py::test_walker_covers_all_fields -x` | ❌ W0 | ⬜ pending |
| PROMPT-03 | 3 | ≥3 trace JSON files under `docs/traces/`, each with raw + grounded diff; ≥1 real downgrade | Traces from real runs, never staged | filesystem | `uv run pytest tests/test_extraction_agent.py::test_traces_committed -x` | ❌ W0 | ⬜ pending |
| grounding | — | fabricated span → `unsupported`; genuine span survives | Code disproves model | unit | `uv run pytest tests/test_grounding_gate.py -x` | ✅ | ⬜ pending |
| SSE | 2 | All emitted event types in `EVENT_TYPES`; each chunk validated via `EventEnvelope` | Malformed emit fails validation, never streams | unit | `uv run pytest tests/test_extraction_agent.py::test_sse_event_taxonomy -x` | ❌ W0 | ⬜ pending |
| codegen | 1 | `ExtractionResult` change regenerates `shared-types` | N/A | unit | `uv run pytest tests/test_codegen_drift.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_extraction_agent.py` — RED stubs for EXTRACT-01/02/05, walker coverage, SSE taxonomy, trace files check
- [ ] `docs/traces/` directory — for D-13 committed traces (populated during the trace-capture task)

*Existing infrastructure reused: pytest + conftest, `tests/test_grounding_gate.py`, `tests/test_field_envelope.py`, `tests/test_sse_demo.py`, `tests/test_codegen_drift.py` — all cover their domains.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live SSE stream renders `{type,payload}` events end-to-end | EXTRACT-05 | Requires running FastAPI + live gpt-5.4 call | `curl -N <extraction SSE endpoint>` with a sample vendor; observe `status` → `result` → `done` events |
| ≥1 trace exhibits a genuine code-enforced `unsupported` downgrade | PROMPT-03 / D-15 | Downgrade must come from a real model run on committed messy samples, not staged | Run extraction on all 3 sample vendors; inspect `docs/traces/*.json` raw-vs-grounded diff for a real downgrade (doubles as fuzzy-threshold calibration evidence) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (`test_extraction_agent.py`, `docs/traces/`)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
