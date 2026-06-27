---
phase: 2
slug: grounding-gate-messy-data
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-27
completed: 2026-06-27
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` → "## Validation Architecture". Task IDs are bound at planning time.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (services/ai) |
| **Config file** | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd services/ai && uv run pytest tests/test_grounding_gate.py -x -q` |
| **Full suite command** | `cd services/ai && uv run pytest -x -q` |
| **Estimated runtime** | ~10 seconds (LLM-free; generation paths are smoke-only, not content-asserted) |

---

## Sampling Rate

- **After every task commit:** Run `cd services/ai && uv run pytest tests/test_grounding_gate.py -x -q`
- **After every plan wave:** Run `cd services/ai && uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

> Task IDs (`02-PP-TT`) are assigned by the planner; this map binds each phase requirement to its
> proving test. Falsifiability tests (Test A / Test B below) are the phase-goal gate.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| EXTRACT-04 (fabricated downgrade) | Fabricated snippet (not in source) → `unsupported`, value + evidence suppressed | unit | `uv run pytest tests/test_grounding_gate.py::test_fabricated_span_is_downgraded -x` | ✅ | ✅ green |
| EXTRACT-04 (genuine passes) | Genuine snippet keeps `present` + gets recomputed offsets (no over-reject) | unit | `uv run pytest tests/test_grounding_gate.py::test_genuine_span_passes_grounding -x` | ✅ | ✅ green |
| EXTRACT-04 (offset recompute) | `source[char_start:char_end]` confirms the snippet region; model offsets never trusted | unit | `uv run pytest tests/test_grounding_gate.py::test_offsets_are_recomputed_not_trusted -x` | ✅ | ✅ green |
| EXTRACT-04 (conflicting field) | `status=conflicting` grounds each `ConflictingValue.evidence` independently | unit | `uv run pytest tests/test_grounding_gate.py::test_conflicting_field_grounded_per_value -x` | ✅ | ✅ green |
| EXTRACT-04 (fuzzy hit) | Minor whitespace/normalization diff grounds above threshold | unit | `uv run pytest tests/test_grounding_gate.py::test_fuzzy_match_above_threshold_grounds -x` | ✅ | ✅ green |
| EXTRACT-04 (fuzzy miss) | Below-threshold snippet downgraded | unit | `uv run pytest tests/test_grounding_gate.py::test_fuzzy_match_below_threshold_downgrades -x` | ✅ | ✅ green |
| EXTRACT-04 (NFKC ligature) | `ﬁ`↔"fi" matches with correct recomputed offsets (two-stage offset map) | unit | `uv run pytest tests/test_grounding_gate.py::test_nfkc_ligature_offset_mapping -x` | ✅ | ✅ green |
| EXTRACT-04 (short-snippet guard) | Sub-minimum-length snippet cannot pass fuzzy on a coincidental window | unit | `uv run pytest tests/test_grounding_gate.py::test_short_snippet_guard -x` | ✅ | ✅ green |
| EXTRACT-04 (walker) | Recursive walker finds + re-grounds every `Field[T]` in a nested pydantic model | unit | `uv run pytest tests/test_grounding_gate.py::test_walker_grounds_nested_fields -x` | ✅ | ✅ green |
| DATA-01 | `data/rfq.json` deserializes to a valid `RFQ` with 8 line items | fixture | `uv run pytest tests/test_sample_fixtures.py::test_rfq_fixture_valid -x` | ✅ | ✅ green |
| DATA-02 | 3× `data/vendor_*.json` deserialize to valid `VendorResponse` instances | fixture | `uv run pytest tests/test_sample_fixtures.py::test_vendor_fixtures_exist_and_valid -x` | ✅ | ✅ green |
| DATA-03 (persona messiness) | Each persona fixture contains its declared issue types | fixture+string | `uv run pytest tests/test_sample_fixtures.py::test_vendor_fixture_messiness -x` | ✅ | ✅ green |
| DATA-03 (missing price) | cheap-but-incomplete fixture has ≥1 line item with no price | fixture | `uv run pytest tests/test_sample_fixtures.py::test_cheap_incomplete_has_missing_price -x` | ✅ | ✅ green |
| DATA-03 (conflict) | polished-fluff fixture has two contradictory statements | fixture | `uv run pytest tests/test_sample_fixtures.py::test_polished_fluff_has_conflict -x` | ✅ | ✅ green |
| DATA-04 (codegen drift) | After `RFQ`/`VendorResponse` flesh-out, pydantic2ts output matches committed TS | codegen | `uv run pytest tests/test_codegen_drift.py -x` | ✅ existing | ✅ green |
| PROMPT-04 | rfq-gen / vendor-gen / messy-data-gen prompts load from registry without error | unit | `uv run pytest tests/test_prompt_registry.py -x` | ✅ existing | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### The Falsifiability Tests (phase-goal gate — write before implementation)

- **Test A — fabricated span IS downgraded** (success criterion 1): a snippet absent from the source
  is forced to `unsupported` with value + evidence suppressed and a downgrade-report entry emitted.
- **Test B — genuine span survives** (success criterion 2): a real snippet keeps its value, gets
  recomputed offsets, emits no downgrade, and `source[char_start:char_end]` equals the snippet.

Full reference implementations live in `02-RESEARCH.md` → "The Falsifiability Tests".

---

## Wave 0 Requirements

- [x] `services/ai/tests/test_grounding_gate.py` — all EXTRACT-04 gate unit tests (incl. falsifiability A/B)
- [x] `services/ai/tests/test_sample_fixtures.py` — DATA-01/02/03 fixture existence + messiness assertions
- [x] `services/ai/grounding/__init__.py`, `grounding/gate.py`, `grounding/report.py` — module stubs so imports resolve

*Existing infrastructure covers `tests/test_codegen_drift.py` (DATA-04) and `tests/test_prompt_registry.py` (PROMPT-04 load path).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live in-app regeneration produces a fresh RFQ + 3 vendor responses | DATA-04 | LLM non-determinism + API cost make content assertions flaky; regen is a smoke path only | Trigger the regen endpoint/CLI; confirm it returns a valid `RFQ` + 3 `VendorResponse` without error (shape, not content) |
| Fuzzy threshold (~90) is correctly calibrated against real messy samples | EXTRACT-04 / D-03 | Threshold is tuned empirically against the committed fixtures once they exist | After fixtures land, sweep threshold and confirm genuine spans pass / fabricated spans fail; lock the constant |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < ~10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete — 108 tests GREEN (2026-06-27)
