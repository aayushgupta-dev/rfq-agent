# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 1-Foundation
**Areas discussed:** Scaffolding scope & layout, Schema envelope & evidence, SSE event vocabulary, Prompt Pack structure, Codegen enforcement, LLM client & live ping, Schema breadth, Build tool, Dev tooling

> User requested covering **all** gray areas (not a subset) plus other Foundation-relevant concerns. Questions were batched per area.

---

## Scaffolding scope & layout

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal | Only services/ai + shared-types; defer apps/web to Phase 5 | |
| Full skeleton now | Stand up apps/web Next.js shell too | ✓ |

**User's choice:** Full skeleton now.

| Option | Description | Selected |
|--------|-------------|----------|
| Move into services/ai | Relocate Python to services/ai, root = JS workspace root | ✓ |
| Keep Python at root | Leave Python at root, add services/ai subpackage | |

**User's choice:** Move into services/ai.

---

## Build tool (turbo vs pnpm only)

| Option | Description | Selected |
|--------|-------------|----------|
| pnpm workspaces only (recommended) | Drop turbo; pnpm handles linking; turbo added later only if justified | |
| Keep turbo + pnpm | Stay literal to CLAUDE.md §5 | ✓ |

**User's choice:** Keep turbo + pnpm.
**Notes:** User initially answered "turbo + pnpm now," then asked mid-discussion whether turbo was even needed. Claude recommended dropping turbo (one JS app + a codegen output don't justify a task pipeline; Python isn't orchestrated by turbo). User reaffirmed keeping turbo + pnpm anyway. Decision stands: turbo stays.

---

## Schema envelope & evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Snippet + char offsets + source ref | Evidence = {snippet, char_start, char_end, source_id} | ✓ |
| Snippet text only | Evidence = quoted substring; grounding does fuzzy search | |

**User's choice:** Snippet + char offsets + source ref. Offsets code-validated, never model-trusted.

| Option | Description | Selected |
|--------|-------------|----------|
| Generic Field[T] | One parametrized generic; verify codegen, concrete fallback if ugly | ✓ |
| Concrete per-type classes | Explicit StringField/MoneyField etc.; verbose but clean TS | |

**User's choice:** Generic Field[T] (with concrete fallback if codegen output is ugly).

| Option | Description | Selected |
|--------|-------------|----------|
| Carry a values[] list | conflicting holds multiple values, each with evidence | ✓ |
| Single value + flag only | conflict detail in notes text | |

**User's choice:** Carry a values[] list.

---

## SSE event vocabulary

| Option | Description | Selected |
|--------|-------------|----------|
| Lock canonical taxonomy now | Full {type, payload} vocab as closed enum: status/partial/result/error/done | ✓ |
| Proof-only minimal set | token/done/error; extend later | |

**User's choice:** Lock canonical taxonomy now.

| Option | Description | Selected |
|--------|-------------|----------|
| First-class error event | Dedicated error event {code, message, recoverable} | ✓ |
| Defer error shape to Phase 3 | Model only success events now | |

**User's choice:** First-class error event.

---

## Prompt Pack structure

| Option | Description | Selected |
|--------|-------------|----------|
| .md + frontmatter, registry loader | Frontmatter metadata + markdown body, loaded by Python registry | ✓ |
| .py template modules | Prompts as Python modules | |
| YAML/TOML registry file | One structured registry file | |

**User's choice:** .md + frontmatter, registry loader.

| Option | Description | Selected |
|--------|-------------|----------|
| version field in frontmatter + git | Semantic version field; git as history | |
| Filename suffix (extraction.v1.md) | Version in filename; new version = new file | ✓ |

**User's choice:** Filename suffix.

| Option | Description | Selected |
|--------|-------------|----------|
| All 7 stubs, registry-loadable | Stub files for all 7 prompts with frontmatter + placeholder bodies | ✓ |
| Registry + 1 example prompt | One worked example; rest added per phase | |

**User's choice:** All 7 stubs.

---

## Codegen enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Script + drift-check test | pytest/CI regenerates into temp dir, fails if differs | ✓ |
| Manual script only | Provide script; rely on discipline | |

**User's choice:** Script + drift-check test.

---

## LLM client & live ping

| Option | Description | Selected |
|--------|-------------|----------|
| Tier factory get_llm('reasoning'\|'cheap') | Thin factory picks model by tier from env | ✓ |
| Direct ChatOpenAI per call | Each agent constructs its own client | |

**User's choice:** Tier factory.

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone script + startup check | verify-access script + FastAPI startup check, fails loudly | ✓ |
| Standalone script only | Manual verification script only | |
| Pytest only | Test that pings the API | |

**User's choice:** Standalone script + startup check.

---

## Schema breadth in Phase 1

| Option | Description | Selected |
|--------|-------------|----------|
| Primitives + envelope now, domain schemas as stubs | Field[T], evidence, flag enum, SSE envelope full; 5 domain schemas as compiling stubs | ✓ |
| Fully define all 5 schemas now | Specify every field of all five schemas | |
| Only Field[T] + envelope, no domain stubs | Primitives only, no domain models | |

**User's choice:** Primitives + envelope now, domain schemas as stubs.

---

## Dev tooling (user-requested addition)

User requested adding testing/linting/formatting setup. Captured directly (clear spec, no options needed):
- Python: ruff (lint + format) + pytest.
- TypeScript: Prettier + ESLint.

---

## Claude's Discretion

- Internal `services/ai/` directory layout, FastAPI app/router structure, ruff/ESLint/Prettier rule sets.
- Whether the codegen drift-check runs under pytest, a pnpm script, or both.
- The trivial LangGraph graph used to prove the SSE spine.

## Deferred Ideas

- CORS + disabled proxy buffering for live SSE → Phase 5 (SHIP-01).
- turbo task-pipeline depth (caching, cross-package tasks) → Phase 5 when apps/web has real build work.
- Full domain-schema field shapes → P2 (RFQ/vendor), P3 (extraction), P4 (comparison).
