---
phase: 04-comparison-agent
plan: "04"
subsystem: services/ai/prompts, services/ai/scripts, docs/traces
tags: [comparison-agent, prompt-pack, fixture-mode, clamp-trace, tdd]
dependency_graph:
  requires: [04-03]
  provides: []
  affects:
    - services/ai/prompts/comparison.v1.md
    - services/ai/prompts/clarification.v1.md
    - services/ai/scripts/capture_comparison_trace.py
    - docs/traces/comparison_trace_1.json
    - docs/traces/comparison_trace_1.md
    - services/ai/tests/test_comparison_agent.py
    - services/ai/tests/test_extraction_agent.py
tech_stack:
  added: []
  patterns:
    - fixture-mode-trace (deterministic over-optimistic ComparisonDraft; real clamp runs against real ExtractionResult)
    - code-authority-guarantee (model proposes, code clamps — trace makes the diff visible)
key_files:
  created:
    - services/ai/scripts/capture_comparison_trace.py
    - docs/traces/comparison_trace_1.json
    - docs/traces/comparison_trace_1.md
  modified:
    - services/ai/prompts/comparison.v1.md
    - services/ai/tests/test_comparison_agent.py
    - services/ai/tests/test_extraction_agent.py
decisions:
  - "comparison.v1.md augmented with REQUIRED model_proposed section and Humility instruction — both previously missing from Wave 3 body (Review Fix 3)"
  - "Fixture-mode trace uses deterministic all-comparable draft; real _apply_verdict_clamp produces 7 entries — no live model call needed (Review Fix 5)"
  - "test_traces_committed in extraction tests now globs trace_*.json (not *.json) to avoid picking up comparison traces (Rule 1 - Bug fix)"
metrics:
  duration: "15 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_created: 3
  files_modified: 3
---

# Phase 04 Plan 04: Comparison Trace, Prompt Refinement, and Human Checkpoint

Wave 4: refined the comparison.v1.md prompt (added missing model_proposed requirement and humility instruction), created the fixture-mode trace capture script, committed the comparison trace with 7 clamp entries, made all 20 comparison tests GREEN, and full suite green at 136 passed.

## What Was Built

**services/ai/prompts/comparison.v1.md** (refined from Wave 3):

- Added `## REQUIRED: model_proposed per verdict` section — the exact text the plan specifies (Review Fix 3 BLOCKER). States the field is required for the audit trail and trace diff, must be one of comparable/partially/not_comparable, includes a JSON example.
- Added `## Humility instruction` section — "a not_comparable that prevents a misleading comparison is better than a comparable built on incomplete data" (makes `'humility' in comp_body or 'not_comparable that prevents' in comp_body` assert pass).
- Prompt now 174 lines (>=120 min), 7,450 chars (>2000 min). All automated quality bar assertions pass.

**services/ai/scripts/capture_comparison_trace.py** (new, 214 lines):

- `_load_extractions_from_traces()` — loads 3 committed ExtractionResults from `docs/traces/trace_vendor_*.json` using the `final_result` key.
- `_build_fixture_draft(extractions)` — builds all-comparable ComparisonDraft + computes real ceilings via `_compute_ceilings`.
- `_build_comparison_trace(extractions, rfq)` — runs real `_apply_verdict_clamp`, asserts `has_downgrades`, builds trace dict with `_fixture_mode: True` and all required keys.
- `_write_comparison_markdown(trace, path)` — 6 sections including the verdict-clamp diff table and Fixture Mode Note.
- Script produces 7 clamp entries (cheap-but-incomplete: technical, commercial, scope, timeline; polished-fluff: commercial, timeline; thorough-but-pricey: commercial). Fails hard via `sys.exit(1)` if `has_downgrades == False`.

**docs/traces/comparison_trace_1.json** (new):

- Keys: `_fixture_mode`, `input`, `resolved_prompt`, `raw_model_output`, `clamp_step` (7 entries), `clarification_step`, `final_result`.
- `clamp_step.entries` all show model_proposed=comparable clamped to not_comparable/partially.

**docs/traces/comparison_trace_1.md** (new):

- Section 3 (THE VERDICT-CLAMP DIFF) has a 7-row table showing vendor/dimension/model-proposed/code-ceiling/clamped-to/reason.
- Section 6 (Fixture Mode Note) explains the deterministic injection approach for Aerchain reviewers.

**services/ai/tests/test_comparison_agent.py** (stub implemented):

- `test_comparison_traces_committed` now asserts: >=1 `comparison_trace_*.json` exists, required keys present, `clamp_step.entries >= 1`, `_fixture_mode == True` or "fixture" in trace.
- All 20 comparison tests GREEN (was 19/20 after Wave 3).

**services/ai/tests/test_extraction_agent.py** (Rule 1 bug fix):

- `test_traces_committed` was globbing `*.json` and picked up the new `comparison_trace_1.json` which lacks `grounding_step` — broke the extraction test.
- Fixed: glob changed to `trace_*.json` (extraction-only pattern). Clarifying ponytail comment added.

## Verification

- `uv run pytest tests/test_comparison_agent.py -v` → 20 passed
- `uv run pytest -q` → 136 passed, 1 xfailed, 0 failures
- `python -c "from prompts.registry import load; comp=load('comparison'); assert 'model_proposed' in comp.content.lower()"` → passes
- `python -c "from prompts.registry import load; comp=load('comparison'); assert len(comp.content) > 2000"` → passes (7,450 chars)
- `comparison_trace_1.json` exists with `clamp_step.entries` = 7

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_traces_committed extraction test cross-contamination**
- **Found during:** Task 2 full-suite run
- **Issue:** `test_traces_committed` in test_extraction_agent.py used `glob("*.json")` which picked up the new `comparison_trace_1.json`. That file lacks `grounding_step` (an extraction-specific key), causing the assertion to fail.
- **Fix:** Changed glob pattern to `trace_*.json` to scope the check to extraction traces only. Added a ponytail comment explaining the intent.
- **Files modified:** `services/ai/tests/test_extraction_agent.py`
- **Commit:** 576b925

**2. [Rule 1 - Bug] comparison.v1.md missing model_proposed requirement and humility instruction**
- **Found during:** Task 1 automated verify
- **Issue:** Wave 3 authored the prompt but the verify script asserts `'required' in comp_body` and `'humility' in comp_body or 'not_comparable that prevents' in comp_body` — both failed. The Wave 3 prompt did not include these two sections.
- **Fix:** Added `## REQUIRED: model_proposed per verdict` section and `## Humility instruction` section to the prompt body.
- **Files modified:** `services/ai/prompts/comparison.v1.md`
- **Commit:** 4b33960

## Known Stubs

None — all stubs resolved.

## Human Checkpoint — APPROVED (2026-06-28)

`type="checkpoint:human-verify"` gate reviewed and approved by the user:
1. comparison.v1.md prompt quality (model_proposed REQUIRED section, humility, no-normalization prohibitions) — approved
2. clarification.v1.md prompt quality (strict-count instruction) — approved
3. comparison_trace_1.md (verdict-clamp diff: model proposed comparable → code clamped 7 verdicts) — approved
4. All 20 comparison tests pass; full suite 136 passed / 1 xfailed / 0 failures — confirmed
5. No regressions — confirmed

Follow-up agreed at approval: capture a **real-model** comparison trace (`comparison_trace_2`, real GPT-5.4) during the Phase 4 functional E2E gate to fully satisfy assignment §16 ("Model output") alongside this deterministic fixture trace.

## Threat Surface Scan

No new security-relevant surface introduced. All STRIDE threats from the plan:
- T-04-04-01 (normalization): no-normalization instruction present and expanded in Task 1.
- T-04-04-02 (model_proposed omission): REQUIRED section added in Task 1 — GREEN.
- T-04-04-03 (clarification extra questions): strict-count instruction present in clarification.v1.md — unchanged, verified GREEN.
- T-04-04-04 (vendor pricing in trace): accepted for prototype — trace is a deliverable.
- T-04-04-05 (0 clamp entries): script exits 1 if has_downgrades==False; test asserts >=1 entry — GREEN.
- T-04-04-06 (fixture not disclosed): Fixture Mode Note section in Markdown + `_fixture_mode: True` in JSON — GREEN.
- T-04-04-SC (no new packages): confirmed — zero new dependencies.

## Self-Check
