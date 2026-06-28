---
phase: 3
slug: extraction-agent
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-27
audited: 2026-06-28
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `03-RESEARCH.md` § Validation Architecture.
> **Audited 2026-06-28** post-execution: all mapped requirements COVERED (green).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/test_extraction_agent.py -x` |
| **Full suite command** | `uv run pytest tests/ -x -m "not live"` |
| **Estimated runtime** | ~2 seconds (mocked LLM; no live calls in unit tests) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_extraction_agent.py tests/test_grounding_gate.py tests/test_field_envelope.py -x`
- **After every plan wave:** Run `uv run pytest tests/ -x -m "not live"`
- **Before `/gsd:verify-work 3`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

> Audited 2026-06-28: every row's named test exists, targets the behavior, and runs green.

| Req | Wave | Behavior | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----|------|----------|-----------------|-----------|-------------------|-------------|--------|
| EXTRACT-01 | 1 | `ExtractionResult` covers all 8 categories; `vendor_name` is plain `str` (Pitfall 5 fix) | N/A | unit | `uv run pytest tests/test_extraction_agent.py::test_schema_shape -x` | ✅ | ✅ green |
| EXTRACT-02 | 2 | Every `present`/`unclear` field has non-empty evidence; evidence passes grounding | Grounding code-enforced (no model `verified` flag) | unit | `uv run pytest tests/test_extraction_agent.py::test_evidence_required -x` | ✅ | ✅ green |
| EXTRACT-03 | 2 | `missing`/`unclear`/`conflicting` never `None`-collapsed; model never fills missing | N/A | unit | `uv run pytest tests/test_field_envelope.py -x` | ✅ | ✅ green |
| EXTRACT-05 | 2 | `LengthFinishReasonError` → `error` event `{recoverable: true}`, no parse; refusal → `{recoverable: false}` | No partial/truncated output ever parsed | unit (mocked) | `uv run pytest tests/test_extraction_agent.py::test_truncation_raises_error_event tests/test_extraction_agent.py::test_refusal_raises_error_event -x` | ✅ | ✅ green |
| EXTRACT-05 | 1 | `unsupported` fields carry no value/evidence (envelope model_validator) | N/A | unit | `uv run pytest tests/test_field_envelope.py -x` | ✅ | ✅ green |
| walker | 1 | Every `Field[T]` in `ExtractionResult` reached by `_walk_and_ground` (closes IN-04) | No grounded field silently bypassed | unit | `uv run pytest tests/test_extraction_agent.py::test_walker_covers_all_fields -x` | ✅ | ✅ green |
| PROMPT-03 | 3 | ≥3 trace JSON files under `docs/traces/` with D-14 keys (input/resolved_prompt/raw_model_output/grounding_step/final_result); every shown fact's evidence is locatable in source (verbatim-evidence integrity) — **D-15 reframe** | Traces from real gpt-5.4 runs, never staged; integrity re-checked by gate's own matcher | filesystem | `uv run pytest tests/test_extraction_agent.py::test_traces_committed -x` | ✅ | ✅ green |
| grounding | — | fabricated span downgraded; genuine span survives | Code disproves model | unit | `uv run pytest tests/test_grounding_gate.py -x` | ✅ | ✅ green |
| SSE | 2 | All emitted event types in `EVENT_TYPES`; each chunk validated via `EventEnvelope` | Malformed emit fails validation, never streams | unit | `uv run pytest tests/test_extraction_agent.py::test_sse_event_taxonomy -x` | ✅ | ✅ green |
| codegen | 1 | `ExtractionResult` change regenerates `shared-types` | N/A | unit | `uv run pytest tests/test_codegen_drift.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_extraction_agent.py` — RED stubs for EXTRACT-01/02/05, walker coverage, SSE taxonomy, trace files check (landed Plan 03-01; all now GREEN)
- [x] `docs/traces/` directory — for committed traces (populated Plan 03-04: 4 JSON + 4 MD traces)

*Existing infrastructure reused: pytest + conftest, `tests/test_grounding_gate.py`, `tests/test_field_envelope.py`, `tests/test_sse_demo.py`, `tests/test_codegen_drift.py` — all cover their domains.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|--------|
| Live SSE stream renders `{type,payload}` events end-to-end | EXTRACT-05 | Requires running FastAPI + live gpt-5.4 call | `curl -N <extraction SSE endpoint>` with a sample vendor; observe `status` → `result` → `done` events. (Truncation failure-shape has an automated live guard: `pytest -m live tests/test_extraction_agent.py::test_truncation_live_guard`.) | manual — pending live run |

> **Superseded (D-15 reframe, 2026-06-28):** the original "≥1 trace exhibits a genuine code-enforced downgrade" manual verification was dropped by product-owner decision. gpt-5.4 quotes verbatim, so 0 trace-level downgrades fire on the committed samples. The downgrade *path* is proven by automated `test_grounding_gate.py` units (`test_fabricated_span_is_downgraded`, `test_fuzzy_match_below_threshold_downgrades`, `test_missing_source_id_downgrades`, `test_short_snippet_guard`); `test_traces_committed` now asserts the complementary half (verbatim-evidence integrity). No manual step remains for this behavior. FUZZY_THRESHOLD untouched (B-R3).

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (`test_extraction_agent.py`, `docs/traces/`)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-06-28 — 10/10 mapped requirements COVERED (green), 1 manual-only (live SSE) pending a live run, 0 gaps requiring test generation.

---

## Validation Audit 2026-06-28

| Metric | Count |
|--------|-------|
| Requirements mapped | 10 |
| COVERED (green) | 10 |
| PARTIAL | 0 |
| MISSING | 0 |
| Gaps found | 0 |
| Tests generated | 0 |
| Manual-only remaining | 1 (live SSE end-to-end) |

**Method:** ran every mapped command by exact node ID — 56 tests passed, 0 failed/errored. No renames or missing tests. Reconciled the PROMPT-03 row and Manual-Only table to the D-15 reframe (verbatim-evidence integrity replaces "≥1 real downgrade"). No `gsd-nyquist-auditor` spawn needed — zero test-generation gaps.
