---
phase: 01-foundation
plan: "04"
subsystem: prompts
tags: [python-frontmatter, prompt-registry, prompt-pack, versioned-prompts]

requires:
  - phase: 01-foundation plan 01
    provides: services/ai uv env with python-frontmatter installed; prompts/ directory mountpoint

provides:
  - services/ai/prompts/registry.py — load(prompt_id, base_dir) resolving latest-by-filename with prompt_id regex guard
  - services/ai/prompts/__init__.py — re-exports load
  - 7 versioned prompt stubs with full YAML frontmatter (id/version/intent/model_tier/failure_handling) + TODO bodies naming owning phase + req ID

affects:
  - Phase 2 (data generation): rfq-gen, vendor-gen, messy-data-gen stubs become full prompts
  - Phase 3 (extraction): extraction.v1.md stub becomes the full extraction prompt
  - Phase 4 (comparison): comparison.v1.md and clarification.v1.md become full prompts
  - Phase 5 (UI/deploy): ui-ux-gen.v1.md becomes full prompt

tech-stack:
  added:
    - python-frontmatter 1.3.0 (already installed in Plan 01 — consumed here for the first time)
  patterns:
    - Prompt-as-.md-with-YAML-frontmatter loaded by registry id (D-11)
    - Versioning via filename suffix extraction.vN.md; registry resolves latest (D-12)
    - Injectable base_dir in registry.load() for test isolation (no tmp writes to real dir)
    - prompt_id validated against ^[a-z0-9-]+$ before glob to prevent path traversal (T-04-03)

key-files:
  created:
    - services/ai/prompts/__init__.py (re-exports load)
    - services/ai/prompts/registry.py (_find_latest + load with base_dir injection)
    - services/ai/prompts/rfq-gen.v1.md (stub; TODO P2/DATA-01)
    - services/ai/prompts/vendor-gen.v1.md (stub; TODO P2/DATA-02)
    - services/ai/prompts/messy-data-gen.v1.md (stub; TODO P2/DATA-03)
    - services/ai/prompts/ui-ux-gen.v1.md (stub; TODO P5/UI-01)
    - services/ai/prompts/extraction.v1.md (stub; TODO P3/EXTRACT-01)
    - services/ai/prompts/comparison.v1.md (stub; TODO P4/COMPARE-01)
    - services/ai/prompts/clarification.v1.md (stub; cheap tier; TODO P4/COMPARE-04)
    - services/ai/tests/test_prompt_registry.py (35 tests; RED da4b8fb → GREEN 66b882f)
  modified: []

key-decisions:
  - "D-11 realised: .md+frontmatter is the prompt source format; the registry loads by id — prompts are first-class versioned source not buried strings"
  - "D-12 realised: filename suffix is the version of record; _find_latest globs {id}.v*.md and selects max(n)"
  - "D-13 realised: all 7 stubs created in Phase 1 with full frontmatter + TODO markers naming owning phase and requirement ID"
  - "clarification prompt uses model_tier cheap per CLAUDE.md §5 (lighter drafting task vs reasoning-heavy generation/extraction/comparison)"
  - "# ponytail: no caching added to _find_latest — prompts are first-party source files, not a hot path; D-12 required latest-by-suffix, not perf"

patterns-established:
  - "Prompt Pack pattern: services/ai/prompts/{id}.v{n}.md — YAML frontmatter + Markdown body; load by id via registry"
  - "TDD cycle in services/ai: write failing test → commit RED → implement → commit GREEN; ruff check+format before GREEN commit"

requirements-completed: [PROMPT-01]

duration: 8min
completed: "2026-06-27"
---

# Phase 01 Plan 04: Prompt Pack Registry Summary

**Minimal ~40-line python-frontmatter registry loading all 7 versioned .md prompt stubs by id with injectable base_dir, prompt_id regex guard, and latest-by-filename resolution (D-11/D-12/D-13, PROMPT-01).**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-27T12:00:00Z
- **Completed:** 2026-06-27T12:08:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 10

## Accomplishments

- `prompts/registry.py`: `_find_latest(prompt_id, base_dir)` globs `{id}.v*.md`, parses version suffix, returns highest-version path; `load(prompt_id, base_dir=_DIR)` validates id with `^[a-z0-9-]+$` then calls `_find_latest`. Intentionally minimal per PonyTail.
- All 7 prompt stubs created with YAML frontmatter keys `id/version/intent/model_tier/failure_handling` + TODO bodies naming owning phase (P2/P3/P4/P5) and requirement IDs (DATA-01..03, EXTRACT-01, COMPARE-01, COMPARE-04, UI-01).
- 35 pytest tests green: all 7 load by id, model_tier valid, intent/failure_handling non-empty, frontmatter `id` matches filename stem, latest-version resolves via `tmp_path` (no writes to real dir), missing id raises `KeyError`, invalid ids raise `ValueError`.

## Task Commits

1. **Task 1 RED: Failing test for prompt registry** - `da4b8fb` (test)
2. **Task 1 GREEN: Registry + all 7 stubs implementation** - `66b882f` (feat)

**Plan metadata:** _(this commit)_

_TDD: RED commit (failing import) precedes GREEN commit (registry + stubs)._

## Files Created/Modified

- `services/ai/prompts/__init__.py` — re-exports `load` for `from prompts import load`
- `services/ai/prompts/registry.py` — `_find_latest` + `load` (~40 lines, stdlib + python-frontmatter)
- `services/ai/prompts/rfq-gen.v1.md` — stub (reasoning; TODO P2/DATA-01)
- `services/ai/prompts/vendor-gen.v1.md` — stub (reasoning; TODO P2/DATA-02)
- `services/ai/prompts/messy-data-gen.v1.md` — stub (reasoning; TODO P2/DATA-03)
- `services/ai/prompts/ui-ux-gen.v1.md` — stub (reasoning; TODO P5/UI-01)
- `services/ai/prompts/extraction.v1.md` — stub (reasoning; TODO P3/EXTRACT-01)
- `services/ai/prompts/comparison.v1.md` — stub (reasoning; TODO P4/COMPARE-01)
- `services/ai/prompts/clarification.v1.md` — stub (cheap; TODO P4/COMPARE-04)
- `services/ai/tests/test_prompt_registry.py` — 35 tests covering all acceptance criteria

## Decisions Made

- `clarification` uses `model_tier: cheap` — drafting focused clarification questions is a lightweight rewrite task, not a reasoning-heavy structured extraction/comparison; this matches the CLAUDE.md §5 tier discipline.
- No caching in `_find_latest` — prompts are first-party committed source files on a non-hot path; caching is YAGNI. Marked with `# ponytail:` comment naming D-12.
- `_find_latest` uses an additional guard `m["id"] == prompt_id` beyond just the glob, to avoid a glob like `rfq-gen.v*.md` accidentally matching `rfq-gen-v2.v1.md` (defensive correctness, not over-engineering).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Ruff `E501` (line too long) on three lines in the test file during the GREEN phase — the frontmatter string literal for the `tmp_path` test was 111 characters. Fixed by extracting a `_stub(v)` helper. No logic changes.

## User Setup Required

None — no external service configuration required for the prompt registry.

## Known Stubs

All 7 prompt stubs are intentional, per D-13. Each stub's body is a `TODO` placeholder naming the owning phase and requirement ID. The stubs are the Phase 1 deliverable — the full prompt bodies are authored in their owning phases (P2/P3/P4/P5). The registry loads and returns them correctly; the bodies are placeholders by design.

## Threat Flags

No new threat surface beyond the T-04-01/T-04-02/T-04-03 entries in the plan threat model. T-04-03 (path traversal via prompt_id) is fully mitigated by the `^[a-z0-9-]+$` regex guard in `load()`, tested by three `TestInvalidPromptId` test cases.

## TDD Gate Compliance

- RED gate: commit `da4b8fb` — `test(01-04): add failing tests for prompt registry and 7 stubs (RED)`
- GREEN gate: commit `66b882f` — `feat(01-04): prompt registry + all 7 versioned stubs (D-11, D-12, D-13, PROMPT-01)`
- REFACTOR gate: not required — code was clean after formatting pass.

## Self-Check: PASSED

- `services/ai/prompts/registry.py` exists — FOUND
- `services/ai/prompts/__init__.py` exists — FOUND
- `ls services/ai/prompts/*.v*.md` lists exactly 7 stubs — CONFIRMED
- `uv run python -c "from prompts import load; [load(i) for ...]"` exits 0 — CONFIRMED
- `load("does-not-exist")` raises KeyError — CONFIRMED (test passes)
- `load("../etc/passwd")` raises ValueError — CONFIRMED (test passes)
- Latest-version test uses tmp_path, no writes to real dir — CONFIRMED
- All 7 stubs have frontmatter id matching filename stem — CONFIRMED
- `uv run pytest tests/test_prompt_registry.py` — 35 passed
- RED commit `da4b8fb` exists — CONFIRMED
- GREEN commit `66b882f` exists — CONFIRMED
