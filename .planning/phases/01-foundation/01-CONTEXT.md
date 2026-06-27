# Phase 1: Foundation - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

The typed contract, model access, and streaming spine that everything downstream depends on — stood up as a real monorepo and **proven**, before any agent exists.

**In scope:**
- pnpm + turbo monorepo scaffold with `services/ai` (FastAPI + LangGraph, Python/uv), `apps/web` (Next.js App Router shell), `packages/shared-types`.
- pydantic foundational primitives: the `Field[T]` absence envelope, the evidence type, the 5-state flag enum, and the SSE event envelope — fully defined.
- The five named domain schemas (RFQ, VendorResponse, ExtractionResult, ComparisonResult) as **compiling stubs** that codegen cleanly; full field shapes are fleshed out in their owning phases.
- pydantic → TS codegen (pydantic2ts) script **plus** a drift-check test.
- env-configured LLM tier factory + a live GPT-5.4 / 5.4-mini access verification (script + startup check).
- A minimal LangGraph stream observable end-to-end as `{type, payload}` SSE via `curl -N`.
- Prompt Pack registry skeleton in `services/ai/prompts/` with all 7 prompt stubs.
- Dev tooling spine: ruff (Python lint+format) + pytest, Prettier + ESLint (TypeScript).

**Out of scope (later phases):** the grounding gate + messy data (P2), extraction agent (P3), comparison agent (P4), buyer UI rendering / deploy / CORS (P5). Full domain-schema field shapes are designed in the phase that uses them.
</domain>

<decisions>
## Implementation Decisions

### Monorepo scaffolding & layout
- **D-01:** Stand up the **full monorepo skeleton now**, including an `apps/web` Next.js (App Router) shell — even though nothing renders until Phase 5. Proves the whole workspace wiring early.
- **D-02:** Relocate the Python project from repo root into `services/ai/` (its own `pyproject.toml` + uv env); **delete the placeholder `main.py`**. The repo root becomes a JS workspace root.
- **D-03:** Use **turbo + pnpm** workspaces from the start, literal to CLAUDE.md §5. (User explicitly chose this over a pnpm-workspaces-only option that was recommended for simplicity — turbo stays.) pnpm workspace links `apps/web` → `packages/shared-types`.

### Schema envelope & evidence shape (the contract)
- **D-04:** Evidence = `{snippet, char_start, char_end, source_id}`. Offsets enable precise grounding-gate location and exact UI span highlighting. **Offsets are computed/validated in code, never trusted from the model.**
- **D-05:** Model the per-field absence envelope as a **generic `Field[T]`** = `{status, value: T | None, evidence}`. Verify the pydantic2ts output is clean; **fall back to concrete per-type classes if the generic produces ugly TS** — the Phase 1 codegen proof is exactly where this gets caught.
- **D-06:** The `conflicting` status carries a **`values[]` list**, each entry with its own evidence — so the UI can show "Vendor says X here, Y there" with both sources. Serves the "surface contradictions, don't hide" principle.
- **D-07:** The 5-state flag is a first-class enum: `present | missing | unclear | conflicting | unsupported`. No nullable that silently collapses to blank (PLAT-01).

### Schema breadth in Phase 1
- **D-08:** Fully build the **foundational primitives now** (`Field[T]`, evidence type, flag enum, SSE envelope). Define RFQ / VendorResponse / ExtractionResult / ComparisonResult as **minimal compiling stubs** that codegen cleanly; flesh out their real fields in P2 (RFQ/vendor), P3 (extraction), P4 (comparison). Avoids locking domain field shapes before those agents are designed.

### SSE event vocabulary
- **D-09:** Lock the **full canonical event taxonomy now**: `status` (phase/progress) · `partial` (incremental structured chunk) · `result` (final validated object) · `error` · `done`. `type` is a **closed enum** in the schema so extraction + comparison don't each invent their own. Phase 1 proves it with a trivial emitter.
- **D-10:** A **first-class `error` event** with payload `{code, message, recoverable}`. Truncation (`finish_reason: length`) and refusals map to this in Phase 3. Defined in the Phase 1 envelope even though nothing emits it yet.

### Prompt Pack structure (30% of grade)
- **D-11:** Each prompt is a **`.md` file = YAML frontmatter (id, version, intent, model_tier, failure_handling notes) + markdown body**, loaded by a small Python registry by id. Reads as first-class authored source (good for the docs Prompt Pack + UI trace) yet loaded as data, not buried in code.
- **D-12:** Versioning expressed via **filename suffix** (`extraction.v1.md`); new version = new file; the registry resolves "latest". (Frontmatter still carries metadata; the filename is the version of record.)
- **D-13:** Create **all 7 prompt stubs** in Phase 1 (rfq-gen, vendor-gen, messy-data-gen, ui-ux-gen, extraction, comparison, clarification) with full frontmatter + placeholder bodies + TODO markers. Proves the registry loads every prompt and locks the structure.

### Codegen enforcement
- **D-14:** Codegen **script + drift-check test**: a pytest/CI check regenerates the TS into a temp dir and **fails if it differs** from the committed `packages/shared-types`. Makes "never hand-mirrored" (PLAT-02) actually enforced — stale contract breaks the build.

### LLM client & access verification
- **D-15:** A **tier factory** `get_llm('reasoning' | 'cheap')` returning a configured LangChain `ChatOpenAI`, picking `gpt-5.4` vs `gpt-5.4-mini` by tier, **model IDs read from env**. Callers ask for a tier, not a model string — enforces the "GPT-5.4 reasoning / mini cheap, never 5.5" discipline in one place.
- **D-16:** GPT-5.4 access live-ping = a **standalone `verify-access` script** (runnable in README setup) **+ a lightweight FastAPI startup check** that fails loudly with a clear message if the org/key lacks `gpt-5.4` / `gpt-5.4-mini`. Catches the known account-specific blocker before anything is built on it.

### Dev tooling spine
- **D-17:** Python: **ruff** for both lint and format (`ruff check` + `ruff format`), configured in `services/ai/pyproject.toml`; **pytest** for tests (per CLAUDE.md §11).
- **D-18:** TypeScript: **Prettier** + **ESLint** for `apps/web` (and `packages/shared-types` where it applies). Next.js ships an ESLint baseline; add Prettier + reconcile the two. (Generated `shared-types` output is exempted/Prettier-formatted as appropriate — codegen owns its shape.)

### Claude's Discretion
- Exact directory layout within `services/ai/` (e.g. `schemas/`, `llm/`, `prompts/`, `api/`, `agents/`), FastAPI app/router structure, and ruff/ESLint/Prettier rule sets — pick sensible conventions matching CLAUDE.md §5.
- Whether the codegen drift-check runs under pytest, a pnpm script, or both — implementer's call.
- The trivial LangGraph graph used to prove the SSE spine (any minimal node that emits the taxonomy events).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of truth (the brief & rubric)
- `docs/assignment.md` — the assignment brief; §22 rubric (70% AI/prompts), §24 anti-patterns, §11 (best-effort extraction).

### Product vision & architecture
- `CLAUDE.md` §5 — monorepo architecture (apps/web, services/ai, packages/shared-types), LLM & framework rules, model-tier discipline.
- `CLAUDE.md` §7 — Prompt Pack & traceability requirements (the 7 prompts, per-prompt documentation).
- `CLAUDE.md` §8 — AI reliability (grounding enforced in code, not by the model).
- `CLAUDE.md` §10 / §15 — local dev (uv, pnpm) and gotchas (Vercel = web only; schemas are the contract; don't over-build infra).

### Planning inputs
- `.planning/PROJECT.md` — product framing, key decisions, constraints.
- `.planning/REQUIREMENTS.md` — PLAT-01..04 + PROMPT-01 are this phase's mandated requirements.
- `.planning/ROADMAP.md` §"Phase 1: Foundation" — the 5 success criteria this phase must make TRUE.

No external ADRs exist yet — decisions above are the authoritative source for this phase.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None of substance yet. The repo is a fresh `uv`-initialized Python project at root.

### Established Patterns
- `pyproject.toml` (root, `name = "aerchain"`, `requires-python = ">=3.12"`, empty deps) and `.python-version` (3.12) — these move/inform the new `services/ai/pyproject.toml`.
- `main.py` is a placeholder hello-world — to be deleted in restructure (D-02).
- `.env` exists (empty) and is gitignored — `OPENAI_API_KEY` + model IDs go here.

### Integration Points
- `packages/shared-types` is mechanically generated FROM `services/ai/schemas/` — the only contract boundary; both sides move together (CLAUDE.md §15).
- `apps/web` consumes the AI service over HTTP/SSE only; in Phase 1 it is a shell that imports `shared-types` to prove the link, nothing more.
</code_context>

<specifics>
## Specific Ideas

- "Prove it" is the theme: every Phase 1 deliverable has an observable proof — a `curl -N` SSE stream, a live model ping, a codegen drift test that goes red on drift.
- Generic `Field[T]` is the preferred shape but is explicitly conditional on clean codegen output — the codegen proof is the deciding test, not a guess.
</specifics>

<deferred>
## Deferred Ideas

- CORS + disabled proxy buffering for live SSE in deploy — belongs to Phase 5 (SHIP-01).
- turbo task pipeline depth (caching, cross-package tasks) — only matters once `apps/web` has real build/test work in Phase 5.
- Full domain-schema field shapes (RFQ items, pricing structures, extraction fields, comparison dimensions) — designed in P2/P3/P4 respectively.

None of the above is lost; each is anchored to its owning phase.
</deferred>

---

*Phase: 1-Foundation*
*Context gathered: 2026-06-27*
