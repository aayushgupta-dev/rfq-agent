# Retrospective: Bid Desk

A living retrospective, appended at each milestone.

## Milestone: v1.0 — MVP

**Shipped:** 2026-06-29
**Phases:** 5 | **Plans:** 27 | **Tasks:** 39 | **Timeline:** 3 days (2026-06-27 → 06-29) | **Commits:** 292 (40 `feat`)

### What Was Built

A prompt-driven procurement copilot that turns messy vendor proposals into a grounded, evidence-backed comparison without inventing anything. Five buyer screens over a FastAPI + LangGraph AI service: a 7-prompt versioned Prompt Pack, a code-enforced grounding gate, grounding-gated extraction with four absence flags, comparability-before-ranking comparison, and an in-app prompt trace. Deployed live on Vercel + Render. 31/31 v1 requirements satisfied.

### What Worked

- **AI-first, UI-last sequencing.** Building the contract (`Field[T]` absence envelope) and the grounding gate *before* any agent meant the reliability machinery was proven in isolation, and every downstream agent inherited it. The headline rubric property (no hallucinated claims) was structural, not bolted on.
- **Code-enforced grounding over model trust.** The gate is one-directional and LLM-free — it downgrades unlocatable spans, never upgrades or invents. This held transitively all the way to the comparison agent (which consumes only validated `ExtractionResult[]`).
- **Phase verifications carried real evidence.** Each VERIFICATION.md tied requirements to code + tests + behavioral spot-checks, which made the milestone audit fast and trustworthy.
- **Honest gap handling.** The UAT-discovered conflicting-grand-totals miss was diagnosed read-only first, then fixed prompt-side with a live behavioral test — not papered over by detuning the gate.

### What Was Inefficient

- **Documentation drift.** The REQUIREMENTS.md traceability table sat 17/31 stale at audit time despite the work being done; SUMMARY frontmatter never carried `requirements_completed`. The audit had to reconcile three sources. Lesson: update traceability at phase close, not milestone close.
- **Tracker/convention mismatches.** Quick-task SUMMARYs used prefixed filenames while `audit-open` scans for a bare `SUMMARY.md` — so genuinely-complete work read as "missing" at close. A diagnosed-and-fixed debug session was never moved to `resolved/`. Both surfaced as false open items.
- **A user-visible no-op shipped.** The RFQ "Regenerate" button fetched a live RFQ then reloaded a static import — caught only at audit. A reviewer clicking it would have seen nothing change.
- **Branch hygiene.** All recent v1.0 work accumulated on `fix/vercel-disable-git` while `main` fell 27 commits behind, despite a `none` branching strategy that expects work on the base branch.

### Patterns Established

- A UAT-discovered model-judgment gap is closed prompt-side (instruction + a matching few-shot anchor) + committed-sample backing + a deterministic CI guard + a live behavioral proof — never a mocked fake.
- Same-field conflict detection is model judgment; the grounding gate must stay one-directional (proves/downgrades, never invents the dropped claim — CLAUDE.md §8).
- Prompt edits that don't change the output contract stay at the same version (registry pins id+version, not body hash).

### Key Lessons

1. Reliability that's enforced in code (not promised by the model) is both the rubric differentiator and the thing that survives integration — invest there first.
2. Keep the tracker honest *continuously*: traceability checkboxes, debug-session resolution, and quick-task status should be flipped at the moment work lands, or milestone close inherits the cleanup.
3. Audit the demo path as a user, not just as code — a wired endpoint isn't a working feature if the UI discards its result.

### Cost / Process Observations

- Model mix: predominantly Opus for planning/execution/verification; subagents (Explore, integration-checker) for fan-out.
- 5-day prototype delivered in 3 active days. Coarse granularity (Phase 5 merged UI+deploy+submission) kept the chain short without losing the strict AI dependency ordering.
