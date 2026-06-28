---
phase: "05"
plan: "05"
subsystem: prompts-docs
tags:
  - prompt-pack
  - ui-ux-gen
  - documentation
  - PROMPT-02
  - PROMPT-04
dependency_graph:
  requires:
    - "05-01"
  provides:
    - "ui-ux-gen.v1.md full prompt"
    - "docs/traces/ui-ux-gen-run.md live artifact"
    - "docs/prompts/ PROMPT-02 complete (7 prompt docs)"
    - "docs/prompts/prompt-04-failure-example.md"
  affects:
    - "apps/web (ui-ux-gen artifact informs component structure)"
    - "docs/traces/ (ui-ux-gen-run.md joins extraction/comparison traces)"
tech_stack:
  added: []
  patterns:
    - "per-prompt what/why/how-it-handles-unreliable-info documentation (extraction-prompt-doc.md structure)"
    - "live model run via registry.load() + get_llm('cheap') + HumanMessage"
key_files:
  created:
    - services/ai/prompts/ui-ux-gen.v1.md
    - docs/traces/ui-ux-gen-run.md
    - docs/prompts/rfq-gen-doc.md
    - docs/prompts/vendor-gen-doc.md
    - docs/prompts/messy-data-gen-doc.md
    - docs/prompts/ui-ux-gen-doc.md
    - docs/prompts/comparison-doc.md
    - docs/prompts/clarification-doc.md
    - docs/prompts/prompt-04-failure-example.md
  modified: []
decisions:
  - "ui-ux-gen uses cheap model tier (gpt-5.4-mini) — task is structured Markdown output, not extraction reasoning; cheap tier sufficient and cost-proportionate"
  - "Live run used env-sourced env vars (main repo .env) via 'env $(grep -v ^ xargs)' invocation — worktree .env path drift prevented factory auto-load; no symlink added (gitignored file, out of scope)"
metrics:
  duration: "~25 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_created: 9
---

# Phase 05 Plan 05: UI/UX Gen Prompt + PROMPT-02 Docs Summary

**One-liner:** Full ui-ux-gen prompt with absence-first design rules, live gpt-5.4-mini run artifact (19k chars), and complete PROMPT-02 documentation for all 7 prompts including PROMPT-04 extraction humility-bias failure example.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Author full ui-ux-gen.v1.md + capture live run artifact | 3b4292f | services/ai/prompts/ui-ux-gen.v1.md, docs/traces/ui-ux-gen-run.md |
| 2 | PROMPT-02 docs for 6 remaining prompts + PROMPT-04 failure example | aaea3dc | docs/prompts/{rfq-gen,vendor-gen,messy-data-gen,ui-ux-gen,comparison,clarification}-doc.md, docs/prompts/prompt-04-failure-example.md |

---

## What Was Built

### Task 1: ui-ux-gen.v1.md prompt + live run

**`services/ai/prompts/ui-ux-gen.v1.md`** (256 lines, replaces 18-line stub):
- Procurement-UX designer persona (not generic SaaS designer)
- 5 product principles embedded as non-negotiables (evidence over assertion, absence first-class, comparability before ranking, buyer-first hierarchy, no fabricated claims)
- Absent-State Design Rule section covering all five FlagStatus values before per-screen specs
- Per-screen instructions for all 5 buyer screens with explicit information hierarchy, key components, interactions, UX copy, and empty/error states
- cheap model tier (gpt-5.4-mini) — structured Markdown output task, not reasoning-heavy extraction

**`docs/traces/ui-ux-gen-run.md`** (19,006 chars):
- Real gpt-5.4-mini output from one live run via `registry.load("ui-ux-gen")` + `get_llm("cheap")`
- Provenance header: Prompt ui-ux-gen v1, Model gpt-5.4-mini, Run date 2026-06-28
- Full per-screen UI specification: RFQ Overview, Vendor Upload, Extraction Review, Comparison, Prompt Trace
- Explicit FlagStatus designs in all AI-rendering screens
- No traceback or error content; artifact length 37x above the 500-char minimum

### Task 2: PROMPT-02 docs + PROMPT-04 failure example

All 7 docs follow the `extraction-prompt-doc.md` structure (## What It Does / ## Why It Is Structured This Way / ## How It Handles Unreliable / Missing / Conflicting Information):

| Doc | Key content |
|-----|-------------|
| rfq-gen-doc.md | Persona grounding, 8 line items with schema IDs, anti-hallucination, JSON-only output |
| vendor-gen-doc.md | One-pass generation rationale, structured mess spec, double anti-cleanup instruction |
| messy-data-gen-doc.md | Taxonomy reference (not generation call), FlagStatus mapping as calibration record |
| ui-ux-gen-doc.md | Procurement-UX persona, absent-state design rule, cheap tier rationale, v1 link |
| comparison-doc.md | Comparability-before-ranking principle, code gate, attention triggers, no-ranking prohibition |
| clarification-doc.md | Grounded question generation, one-per-flag ordering, why_needed field, cheap tier |
| prompt-04-failure-example.md | Extraction humility-bias failure: paraphrased evidence as verbatim, $80K fabrication example, verbatim fix + FUZZY_THRESHOLD=90 gate, defense-in-depth rationale, test_grounding_gate.py regression guard |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree .env path drift in factory.py**
- **Found during:** Task 1 live run attempt
- **Issue:** `factory.py` resolves `.env` as `Path(__file__).resolve().parents[3] / ".env"` — in the main repo this points to the repo root, but from the worktree at `aerchain/.claude/worktrees/agent-*/services/ai/llm/factory.py`, `parents[3]` resolves to the worktree root which has no `.env`. The env vars (OPENAI_API_KEY, MODEL_CHEAP) were not loaded.
- **Fix:** Used `env $(grep -v '^#' /path/to/main/repo/.env | xargs)` to inject env vars into the live run invocation. No code change — this is a dev-environment workaround for the worktree isolation. The factory.py path computation is correct for normal use; the worktree just has no symlinked .env (gitignored, correctly absent from the worktree).
- **Files modified:** None (invocation-level fix only)
- **Commit:** Not committed (invocation detail)

**2. [Rule 2 - Model tier correction] Changed ui-ux-gen model_tier from reasoning to cheap**
- **Found during:** Task 1 prompt authoring
- **Issue:** The stub had `model_tier: reasoning` but the task (generate structured Markdown for a UI spec) does not require extraction reasoning or comparison analysis — it is a structured-output generation task well within the cheap model's capability.
- **Fix:** Changed `model_tier: reasoning` to `model_tier: cheap` in the frontmatter. This is consistent with clarification (also cheap) and prevents unnecessary cost for a one-time artifact capture.
- **Files modified:** `services/ai/prompts/ui-ux-gen.v1.md`
- **Commit:** 3b4292f

---

## Known Stubs

None. All 9 files contain real, complete content. The live run artifact is genuine model output (19,006 chars), not a placeholder.

---

## Self-Check: PASSED

Created files exist:
- [x] services/ai/prompts/ui-ux-gen.v1.md (256 lines)
- [x] docs/traces/ui-ux-gen-run.md (19006 chars)
- [x] docs/prompts/rfq-gen-doc.md
- [x] docs/prompts/vendor-gen-doc.md
- [x] docs/prompts/messy-data-gen-doc.md
- [x] docs/prompts/ui-ux-gen-doc.md
- [x] docs/prompts/comparison-doc.md
- [x] docs/prompts/clarification-doc.md
- [x] docs/prompts/prompt-04-failure-example.md

Commits exist:
- [x] 3b4292f — feat(05-05): author full ui-ux-gen.v1.md prompt + capture live run artifact
- [x] aaea3dc — docs(05-05): write PROMPT-02 docs for 6 prompts + PROMPT-04 failure example
