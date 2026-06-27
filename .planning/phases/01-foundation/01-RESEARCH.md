# Phase 1: Foundation - Research

**Researched:** 2026-06-27
**Domain:** pnpm+turbo monorepo wiring · pydantic v2 generic contract → TS codegen · LangGraph v1 custom-stream → SSE · OpenAI GPT-5.4 access via langchain-openai · Markdown-frontmatter prompt registry
**Confidence:** HIGH (the D-05 generic-vs-concrete verdict is settled by direct empirical test, not inference)

## Summary

Phase 1 stands up the typed contract, model access, and streaming spine and *proves* each one. The highest-uncertainty item — whether a generic pydantic `Field[T]` envelope produces usable TypeScript — was tested empirically this session against pydantic **2.13.4** + `pydantic-to-typescript` **2.0.0** + `json-schema-to-typescript` **15.0.4**, and the answer is a clear **GO on the generic**: json2ts monomorphizes `Field[T]` into clean, concrete, correctly-typed interfaces (`FieldStr`, `FieldDecimal`, `FieldInt`, plus matching `ConflictingValueStr/...` for the `values[]` list). You get D-05's "concrete per-type classes" fallback *for free* from a single generic source definition. Output is byte-identical across runs, so the D-14 drift-check needs no special determinism work.

The LangGraph streaming spine maps cleanly: emit `writer({"type": ..., "payload": ...})` from a node via `get_stream_writer()` with `stream_mode="custom"`, and re-shape each chunk into an `sse-starlette` `EventSourceResponse`. The LLM tier factory wraps `init_chat_model(env_model_id, ...)` (langchain-openai 1.3.x); access verification is a 1-token `.invoke()` in both a standalone script and a FastAPI `lifespan` handler that raises on failure. The Prompt Pack registry is ~30 lines of stdlib + `python-frontmatter`.

**Primary recommendation:** Build the generic `Field[T]` envelope (D-05 GO). Pin `pydantic-to-typescript==2.0.0`, `json-schema-to-typescript@15` (a real npm dependency — `pydantic2ts` shells out to it), set `model_config = ConfigDict(extra="forbid")` on every contract model to keep the TS strict, and make the drift-check a `pytest` test that regenerates into a temp dir and `assert`s byte-equality with the committed file.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full monorepo skeleton now, including an `apps/web` Next.js (App Router) shell (nothing renders until P5).
- **D-02:** Relocate the Python project from repo root into `services/ai/` (own `pyproject.toml` + uv env); **delete placeholder `main.py`**. Repo root becomes a JS workspace root.
- **D-03:** **turbo + pnpm** workspaces from the start (user explicitly chose this over pnpm-only). pnpm workspace links `apps/web` → `packages/shared-types`.
- **D-04:** Evidence = `{snippet, char_start, char_end, source_id}`. Offsets enable grounding-gate location + UI span highlighting. **Offsets computed/validated in code, never trusted from the model.**
- **D-05:** Model the per-field absence envelope as a **generic `Field[T]`** = `{status, value: T | None, evidence}`. Verify pydantic2ts output is clean; **fall back to concrete per-type classes if the generic produces ugly TS** — the Phase 1 codegen proof is where this gets caught.
- **D-06:** The `conflicting` status carries a **`values[]` list**, each entry with its own evidence.
- **D-07:** The 5-state flag is a first-class enum: `present | missing | unclear | conflicting | unsupported`. No nullable that silently collapses to blank.
- **D-08:** Fully build the foundational primitives now (`Field[T]`, evidence type, flag enum, SSE envelope). Define RFQ / VendorResponse / ExtractionResult / ComparisonResult as **minimal compiling stubs** that codegen cleanly; flesh out real fields in P2/P3/P4.
- **D-09:** Lock the full canonical SSE taxonomy now: `status | partial | result | error | done`. `type` is a **closed enum** in the schema. Phase 1 proves it with a trivial emitter.
- **D-10:** First-class `error` event with payload `{code, message, recoverable}`. Defined in the P1 envelope even though nothing emits it yet.
- **D-11:** Each prompt = a `.md` file = YAML frontmatter (id, version, intent, model_tier, failure_handling) + markdown body, loaded by a small Python registry by id.
- **D-12:** Versioning via filename suffix (`extraction.v1.md`); new version = new file; registry resolves "latest". Frontmatter carries metadata; filename is the version of record.
- **D-13:** Create **all 7 prompt stubs** in P1 (rfq-gen, vendor-gen, messy-data-gen, ui-ux-gen, extraction, comparison, clarification) with full frontmatter + placeholder bodies + TODO markers.
- **D-14:** Codegen **script + drift-check test**: regenerate TS into a temp dir and **fail if it differs** from committed `packages/shared-types`.
- **D-15:** Tier factory `get_llm('reasoning' | 'cheap')` returning a configured LangChain chat model, picking `gpt-5.4` vs `gpt-5.4-mini` by tier, **model IDs read from env**.
- **D-16:** GPT-5.4 access live-ping = standalone `verify-access` script **+** a lightweight FastAPI startup check that fails loudly if the org/key lacks access.
- **D-17:** Python: **ruff** (`ruff check` + `ruff format`) in `services/ai/pyproject.toml`; **pytest** for tests.
- **D-18:** TypeScript: **Prettier** + **ESLint** for `apps/web` (+ `packages/shared-types` where it applies). Generated output is Prettier-exempt/owned by codegen.

### Claude's Discretion
- Exact directory layout within `services/ai/` (`schemas/`, `llm/`, `prompts/`, `api/`, `agents/`), FastAPI app/router structure, ruff/ESLint/Prettier rule sets.
- Whether the codegen drift-check runs under pytest, a pnpm script, or both — implementer's call.
- The trivial LangGraph graph used to prove the SSE spine (any minimal node emitting the taxonomy).

### Deferred Ideas (OUT OF SCOPE)
- CORS + disabled proxy buffering for live SSE in deploy → Phase 5 (SHIP-01).
- turbo task pipeline depth (caching, cross-package tasks) → Phase 5.
- Full domain-schema field shapes (RFQ items, pricing, extraction fields, comparison dimensions) → P2/P3/P4.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLAT-01 | pydantic schemas (RFQ, VendorResponse, ExtractionResult, ComparisonResult, SSE envelope) with absence as first-class enum per field | `Field[T]` generic envelope verified to model `{status, value, evidence, values}`; 5-state `FlagStatus` enum; SSE `EventEnvelope` closed-enum type — all in *Architecture Patterns* below |
| PLAT-02 | pydantic → `packages/shared-types` TS via pydantic2ts; never hand-mirrored | `pydantic-to-typescript==2.0.0` + `json-schema-to-typescript@15` verified to emit clean strict TS from the generic; drift-check pattern in *Code Examples* |
| PLAT-03 | env-configured LLM client (gpt-5.4 / gpt-5.4-mini); access verified by live ping | `init_chat_model(env_id)` tier factory + 1-token `.invoke()` ping in script + FastAPI `lifespan`; *Code Examples* |
| PLAT-04 | SSE `{type, payload}` envelope (FastAPI emits, Next.js consumes); never buffer-and-return | LangGraph `get_stream_writer` + `stream_mode="custom"` → `EventSourceResponse`; trivial proof graph; *Code Examples* |
| PROMPT-01 | versioned prompt source in `services/ai/prompts/` for all 7 prompts; first-class artifacts | `.md`+frontmatter via `python-frontmatter`, ~30-line registry resolving latest-by-filename; all 7 stubs; *Code Examples* |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Contract schema definition | API/Backend (`services/ai/schemas/`) | — | pydantic is the single source of truth (CLAUDE.md §15); TS is derived, never authored |
| TS contract artifact | Build/Codegen (`packages/shared-types`) | — | Mechanically generated from the backend schema; `apps/web` only consumes it |
| LLM client + access check | API/Backend (`services/ai/llm/`) | — | All OpenAI calls and tier discipline live in one place; web never touches an AI SDK |
| SSE event emission | API/Backend (FastAPI) | — | FastAPI emits, Next.js consumes; web is a thin client (CLAUDE.md §5) |
| SSE event consumption | Frontend Server / Client (`apps/web`) | — | P1 only proves the *emit* side via `curl -N`; real consumption is P5 |
| Prompt source-of-truth | API/Backend (`services/ai/prompts/`) | Docs (`docs/prompts/`) | Loaded as data by the registry; documented for the Prompt Pack deliverable |
| Workspace orchestration | Build (turbo + pnpm) | — | turbo orchestrates the JS side; **uv owns the Python service entirely** |

## Standard Stack

### Core (Python — `services/ai`)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | 2.13.4 | Contract schemas, the `Field[T]` envelope, structured output later | CLAUDE.md mandate; v2 generics + JSON-schema export are the codegen source [VERIFIED: PyPI 2026-05-06] |
| `pydantic-to-typescript` | 2.0.0 | CLI `pydantic2ts` that drives codegen | The actual package behind the `pydantic2ts` command; v2 supports pydantic v2 [VERIFIED: PyPI 2024-11-22] |
| `langgraph` | 1.2.6 | Agent/graph orchestration + custom streaming | CLAUDE.md mandate; **now v1.x** (training data is v0.x — stale) [VERIFIED: PyPI 2026-06-18] |
| `langchain-openai` | 1.3.3 | `ChatOpenAI` / `init_chat_model` for OpenAI | CLAUDE.md mandate; the tier factory wraps this [VERIFIED: PyPI 2026-06-22] |
| `langchain-core` | 1.4.8 | Pulled transitively; `init_chat_model` lives in `langchain` | Peer of langgraph 1.x [VERIFIED: PyPI 2026-06-18] |
| `fastapi` | 0.138.1 | HTTP + SSE endpoints, `lifespan` startup check | CLAUDE.md mandate [VERIFIED: PyPI 2026-06-25] |
| `uvicorn` | 0.49.0 | ASGI server (hot reload in dev) | Standard FastAPI runner [VERIFIED: PyPI 2026-06-03] |
| `sse-starlette` | 3.4.5 | `EventSourceResponse` — SSE done right (ping, graceful shutdown) | Idiomatic SSE for Starlette/FastAPI; avoids hand-rolling event framing [VERIFIED: PyPI 2026-06-20] |
| `python-frontmatter` | 1.3.0 | Parse `.md` YAML frontmatter for the prompt registry | Smallest correct way to parse frontmatter; one call `frontmatter.load()` [VERIFIED: PyPI 2026-05-20] |

### Core (JS — root / `apps/web` / `packages/shared-types`)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json-schema-to-typescript` | 15.0.4 | `json2ts` CLI that `pydantic2ts` shells out to — **a real npm dep, not optional** | Required by pydantic-to-typescript; install at the workspace root (or in `packages/shared-types`) [VERIFIED: npm 15.0.4] |
| `pnpm` | 10.28.1 (installed) | Workspace package manager + linking | D-03; installed locally [VERIFIED: local] |
| `turbo` | latest 2.x | JS-side task orchestration | D-03; **not yet installed** — add as a root devDependency [ASSUMED latest] |
| `next` | latest 15.x | App Router shell | D-01; thin client only in P1 [ASSUMED latest] |
| `prettier` + `eslint` | latest | TS lint+format (D-18) | Next.js ships an ESLint baseline; add Prettier and reconcile [ASSUMED latest] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ruff` | 0.15.13 (installed) | Python lint+format (D-17) | `ruff check` + `ruff format`, configured in `services/ai/pyproject.toml` [VERIFIED: local] |
| `pytest` | 9.0.2 (installed) | Tests incl. the drift-check (D-14) | `uv run pytest` from `services/ai/` [VERIFIED: local] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| generic `Field[T]` | concrete `FieldStr`/`FieldDecimal` hand-written pydantic classes | **Not needed** — the generic produces exactly these via codegen; hand-writing them is more code for identical output. D-05 fallback is unnecessary (see verdict). |
| `sse-starlette` | raw FastAPI `StreamingResponse` yielding `f"data: {json}\n\n"` | Works, but you reimplement event framing, ping/keepalive, and disconnect handling. `sse-starlette` is ~1 dep for correct SSE. Keep it. |
| `python-frontmatter` | manual `text.split("---")` split | Manual split is fragile on `---` inside the body and YAML edge cases. `python-frontmatter` is one import, one call. |
| `init_chat_model(...)` | `ChatOpenAI(model=..., ...)` directly | `init_chat_model` reads provider+model from a single string and is the current-docs idiom; either works since the tier factory is the only call site. `ChatOpenAI` is fine if you want the explicit class. |

**Installation:**
```bash
# Python (services/ai) — via uv
uv add pydantic langgraph langchain langchain-openai fastapi uvicorn "sse-starlette" python-frontmatter
uv add --dev "pydantic-to-typescript==2.0.0" ruff pytest

# JS (root workspace) — json2ts is REQUIRED for codegen
pnpm add -D -w json-schema-to-typescript@15 turbo prettier
# apps/web: create-next-app (App Router); add eslint via the Next baseline
```

**Version verification:** All Python versions above confirmed against the PyPI JSON API on 2026-06-27 (upload dates shown). `json-schema-to-typescript` confirmed via `npm view`. LangGraph/langchain-openai are now **major v1** — assistant training data describes v0.x and is stale; the v1 streaming API (`get_stream_writer`, `stream_mode`) is confirmed current via Context7.

## Package Legitimacy Audit

> slopcheck could **not** be installed in this environment (`pip install slopcheck` failed — no network/permission). Per protocol, packages are tagged `[ASSUMED]` and the planner SHOULD gate any unfamiliar install behind a `checkpoint:human-verify`. That said, all packages below are long-established, CLAUDE.md-mandated, and version-verified against their correct registries — the legitimacy risk is low.

| Package | Registry | Age (approx) | Source Repo | slopcheck | Disposition |
|---------|----------|--------------|-------------|-----------|-------------|
| pydantic | PyPI | 8+ yrs | github.com/pydantic/pydantic | unavailable | Approved (mandated) |
| pydantic-to-typescript | PyPI | 4+ yrs | github.com/phillipdupuis/pydantic-to-typescript | unavailable | Approved (tested this session) |
| langgraph | PyPI | 2+ yrs | github.com/langchain-ai/langgraph | unavailable | Approved (mandated) |
| langchain-openai | PyPI | 2+ yrs | github.com/langchain-ai/langchain | unavailable | Approved (mandated) |
| fastapi | PyPI | 6+ yrs | github.com/fastapi/fastapi | unavailable | Approved (mandated) |
| uvicorn | PyPI | 7+ yrs | github.com/encode/uvicorn | unavailable | Approved |
| sse-starlette | PyPI | 5+ yrs | github.com/sysid/sse-starlette | unavailable | Approved |
| python-frontmatter | PyPI | 8+ yrs | github.com/eyeseast/python-frontmatter | unavailable | Approved |
| json-schema-to-typescript | npm | 8+ yrs | github.com/bcherny/json-schema-to-typescript | unavailable | Approved (required by pydantic2ts; tested) |

**Packages removed due to slopcheck [SLOP]:** none (slopcheck unavailable).
**Packages flagged [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram (Phase 1 scope only)

```
                          services/ai  (FastAPI + LangGraph, Python/uv)
                          ┌──────────────────────────────────────────────┐
                          │  schemas/          llm/            prompts/    │
                          │  Field[T]          get_llm(tier)   registry    │
                          │  Evidence          init_chat_model 7 .md stubs │
                          │  FlagStatus enum         │              │      │
   OPENAI_API_KEY  ─────► │  EventEnvelope           ▼              ▼      │
   MODEL_REASONING  ───►  │     │              ┌─────────────┐  load by id │
   MODEL_CHEAP      ───►  │     │              │  OpenAI ping │  (latest)   │
                          │     │              │  (1 token)   │             │
                          │     │              └──────┬──────┘             │
                          │     │   FastAPI lifespan ◄┘ fail-loud on no    │
                          │     │                       gpt-5.4 access     │
                          │     ▼                                          │
                          │  GET /stream/demo                              │
                          │  trivial LangGraph node                        │
                          │   writer({type,payload})  ──stream_mode=custom │
                          │          │                                     │
                          │          ▼  reshape chunk → ServerSentEvent    │
                          │   EventSourceResponse (status→partial→result→  │
                          │                          done; error on fail)  │
                          └──────────┬─────────────────────────┬──────────┘
                                     │ SSE  data:{type,payload} │
                       curl -N ◄─────┘                          │ (P5: apps/web consumes)
                       (the P1 proof)                           ▼
                                                          apps/web shell
   schemas/*.py  ──pydantic2ts──►  packages/shared-types/index.d.ts  ──pnpm link──► apps/web
        ▲                                   ▲
        └──── pytest drift-check ───────────┘  (regen to temp, assert byte-equal, red on drift)
```

### Recommended Project Structure
```
aerchain/                          # JS workspace root (pnpm + turbo)
├─ package.json                    # workspace root: turbo, json-schema-to-typescript, prettier
├─ pnpm-workspace.yaml             # packages: ["apps/*", "packages/*"]
├─ turbo.json                      # minimal pipeline (lint/build); depth deferred to P5
├─ apps/
│  └─ web/                         # Next.js App Router shell; depends on shared-types
│     └─ package.json              # "@aerchain/shared-types": "workspace:*"
├─ packages/
│  └─ shared-types/
│     ├─ package.json              # name: @aerchain/shared-types; main: index.d.ts
│     └─ index.d.ts                # GENERATED — committed, drift-checked, never hand-edited
└─ services/
   └─ ai/                          # Python service (uv owns this; turbo ignores it)
      ├─ pyproject.toml            # name=aerchain-ai; ruff+pytest config; deps moved from root
      ├─ .python-version           # 3.12 (moved from root)
      ├─ schemas/
      │  ├─ envelope.py            # Field[T], Evidence, ConflictingValue[T], FlagStatus
      │  ├─ events.py              # EventEnvelope (closed-enum type), ErrorPayload
      │  └─ domain.py              # RFQ/VendorResponse/ExtractionResult/ComparisonResult stubs
      ├─ llm/
      │  └─ factory.py             # get_llm('reasoning'|'cheap'); ping_access()
      ├─ prompts/
      │  ├─ registry.py            # load-by-id, resolve latest-by-filename
      │  ├─ rfq-gen.v1.md  vendor-gen.v1.md  messy-data-gen.v1.md
      │  ├─ ui-ux-gen.v1.md  extraction.v1.md  comparison.v1.md  clarification.v1.md
      ├─ api/
      │  └─ app.py                 # FastAPI app, lifespan access-check, GET /stream/demo
      ├─ agents/                   # (empty/placeholder in P1; trivial demo graph may live here)
      ├─ scripts/
      │  ├─ codegen.py             # calls generate_typescript_defs → packages/shared-types
      │  └─ verify_access.py       # standalone CLI ping (README setup step)
      └─ tests/
         └─ test_codegen_drift.py  # D-14 drift-check
```
*Note: the root `pyproject.toml` (name=aerchain) and `main.py` are deleted/relocated per D-02. The repo root becomes JS-only; the Python project's `pyproject.toml` lives in `services/ai/`.*

### Pattern 1: Generic `Field[T]` envelope (the contract core)
**What:** One generic pydantic model parametrized per concrete type; codegen monomorphizes it into concrete TS interfaces.
**When to use:** Every contract field that must carry absence + evidence (D-05).
**Why it works (verified):** `VendorResponseStub.model_json_schema()` emits `$defs` keys `Field_str_`, `Field_Decimal_`, `Field_int_` (one per parametrization). `json2ts` sanitizes these to clean `FieldStr` / `FieldDecimal` / `FieldInt` interfaces, each with a correctly-typed `value`. **No generic survives into TS** — json2ts has no generics; it produces exactly the "concrete per-type classes" D-05 names as the fallback, automatically.

### Pattern 2: SSE closed-enum event envelope
**What:** `EventEnvelope` with `type: Literal["status","partial","result","error","done"]` and a `payload` field; `ErrorPayload = {code, message, recoverable}` (D-09/D-10).
**When to use:** Every streamed agent response across P3/P4 reuses this — defined once in P1.
**Anti-pattern it prevents:** each agent inventing its own event names.

### Pattern 3: Tier factory over `init_chat_model`
**What:** `get_llm('reasoning'|'cheap')` reads `MODEL_REASONING` / `MODEL_CHEAP` from env and returns a configured chat model. Callers never pass a model string (D-15). Enforces "gpt-5.4 reasoning / mini cheap, never 5.5" in one place.

### Anti-Patterns to Avoid
- **Hand-mirroring TS types** — violates PLAT-02. The TS file is generated and drift-checked; treat it as a build artifact (Prettier-exempt, D-18).
- **Buffer-and-return agent work** — violates PLAT-04/CLAUDE.md §15. Always stream via `writer()` + `EventSourceResponse`.
- **Trusting a model-supplied "verified" flag** — CLAUDE.md §8. Not exercised in P1, but the envelope's offsets exist so P2 can validate in code.
- **Running turbo/Next over the Python service** — turbo orchestrates JS only; uv owns `services/ai`. `pnpm-workspace.yaml` lists `apps/*` and `packages/*`, **not** `services/*`.
- **A shared `extra="forbid"` base class that gets exported** — codegen emits an empty `export interface Strict {}`. Use a non-exported mixin or set `model_config` per model, or strip the empty interface post-gen (see Pitfall 3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| pydantic → TS | A custom AST/JSON-schema walker | `pydantic-to-typescript` + `json2ts` | Battle-tested; handles enums, refs, optionals, nesting correctly (verified output) |
| Per-type envelope classes | Hand-written `FieldStr`, `FieldInt`, … | A single generic `Field[T]` | The generic *generates* the concrete classes; hand-writing duplicates them |
| SSE framing / keepalive | `f"data: ...\n\n"` string building | `sse-starlette` `EventSourceResponse` | Correct event framing, ping, disconnect/shutdown handling |
| Frontmatter parsing | `text.split("---")` | `python-frontmatter` (`frontmatter.load`) | Robust against `---` in body + YAML edge cases; one call |
| Custom event streaming from LangGraph | Threading/queues to surface progress | `get_stream_writer()` + `stream_mode="custom"` | First-class LangGraph API; the chunk *is* your `{type, payload}` |
| OpenAI client config | Raw `openai` SDK plumbing | `init_chat_model` / `ChatOpenAI` | CLAUDE.md mandates LangChain orchestration; raw `openai` only as low-level fallback |

**Key insight:** The whole D-05 "generic vs concrete" debate dissolves — the generic source and the concrete-classes fallback produce the *same* TypeScript. Pick the generic; you write it once.

## Runtime State Inventory

> This phase **relocates** the Python project root → `services/ai/` (D-02), which has rename-like side effects. Inventory below.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — fresh repo, no datastore (CLAUDE.md §10 forbids DB/queue/vector store). Verified: only `.env` (empty), docs, scaffolding. | None |
| Live service config | None — no deployed service yet (deploy is P5). | None |
| OS-registered state | None — no scheduled tasks, daemons, or services registered. | None |
| Secrets/env vars | `.env` exists at root, empty, gitignored. `OPENAI_API_KEY`, `MODEL_REASONING`, `MODEL_CHEAP` will be added. The AI service must read `.env` from `services/ai/` (or root) — **decide the `.env` location when relocating** so `verify_access.py` finds the key. | Code: env loading path |
| Build artifacts | Root `pyproject.toml` (name=`aerchain`) and `main.py` are being **deleted/moved** (D-02). No `*.egg-info`, no `.venv` committed (gitignored). `graphify-out/` is a regenerable build artifact (gitignored per recent commits) — unaffected. `.python-version` (3.12) moves with the project. | Move `pyproject.toml`+`.python-version` to `services/ai/`; delete `main.py`; recreate uv env there |

**The canonical question — after every file is updated, what still references the old root layout?** Nothing external. The only consumers of the root Python project are local dev (`uv run`) and the (about-to-be-replaced) `main.py`. No CI, no deploy, no imports exist yet. The relocation is clean.

## Common Pitfalls

### Pitfall 1: `pydantic2ts` can't import the schema module
**What goes wrong:** `ModuleNotFoundError` when running codegen (reproduced this session).
**Why it happens:** `pydantic2ts --module` imports by dotted path; the module must be importable (on `PYTHONPATH` / installed). Passing a bare filename from a different cwd fails.
**How to avoid:** Either pass the **absolute file path** (`--module /abs/path/schemas/__init__.py`) or run codegen from `services/ai/` with the package installed (`uv run`), or call `generate_typescript_defs("schemas", out_path)` from a script inside the package. The `scripts/codegen.py` approach (Python, not CLI) is most robust.

### Pitfall 2: forgetting `json-schema-to-typescript` is a hard dependency
**What goes wrong:** `pydantic2ts` runs, finds models, then fails at "Converting JSON schema to typescript" because `json2ts` isn't on PATH.
**Why it happens:** `pydantic-to-typescript` shells out to the npm `json2ts` binary; it is not bundled.
**How to avoid:** Install `json-schema-to-typescript@15` as a workspace devDependency and ensure the codegen step runs where `node_modules/.bin/json2ts` is resolvable (pnpm script, or pass `--json2ts-cmd ./node_modules/.bin/json2ts`). Document in README.

### Pitfall 3: index signature + empty base interface in generated TS
**What goes wrong:** Default pydantic `additionalProperties` yields `[k: string]: unknown;` on every interface; a shared `extra="forbid"` base exported as `export interface Strict {}`.
**Why it happens:** json2ts faithfully reflects the JSON schema; an exported base model becomes an exported (empty) interface.
**How to avoid (verified):** Set `model_config = ConfigDict(extra="forbid")` on each contract model — this removes the index signature (confirmed: strict TS has no `[k: string]`). Avoid the empty-interface by making the strict base a non-`BaseModel` mixin, setting config per-model, or stripping the empty interface in `codegen.py` post-processing. **The planner must pick one** (recommendation: per-model config or a tiny post-gen strip — keeps the source honest).

### Pitfall 4: stale LangGraph v0 API in training/snippets
**What goes wrong:** Code uses old `StreamMode`/`astream_events` v1 patterns or assumes v0 graph APIs.
**Why it happens:** LangGraph is now **1.2.6**; assistant training data is v0.x.
**How to avoid:** Use the verified v1 surface: `from langgraph.config import get_stream_writer`; `graph.stream(inputs, stream_mode="custom")` (or `astream`). For async nodes on Python <3.11 add a `writer: StreamWriter` arg — **not needed here (3.12)**, so `get_stream_writer()` inside the node is the clean path.

### Pitfall 5: GPT-5.4 reasoning params on the access ping
**What goes wrong:** The "cheapest 1-token ping" sends `max_tokens`/`temperature` that a reasoning model rejects or that inflate cost.
**Why it happens:** GPT-5.x reasoning models have different param handling than chat models.
**How to avoid:** Keep the ping minimal — `init_chat_model(model_id).invoke("ping")` with the smallest output cap the model accepts; catch the exception and re-raise with a clear "org/key lacks access to {model}" message. Confirm the exact param name (`max_tokens` vs `max_completion_tokens`) against the model before hardcoding (CLAUDE.md: confirm model strings/params, don't assume). **[ASSUMED — exact param surface of gpt-5.4 not verified this session]**

## Code Examples

### Generic Field[T] envelope (verified to codegen cleanly)
```python
# Source: tested this session — pydantic 2.13.4 → pydantic2ts 2.0.0 → json2ts 15.0.4
from __future__ import annotations
from enum import Enum
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class FlagStatus(str, Enum):
    present = "present"; missing = "missing"; unclear = "unclear"
    conflicting = "conflicting"; unsupported = "unsupported"

class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snippet: str
    char_start: int
    char_end: int
    source_id: str

class ConflictingValue(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    value: T | None = None
    evidence: list[Evidence] = []

class Field(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    status: FlagStatus
    value: T | None = None
    evidence: list[Evidence] = []
    values: list[ConflictingValue[T]] | None = None  # populated only when status == conflicting
```
Generated TS (verified): clean `FieldStr` / `FieldDecimal` / `FieldInt` interfaces + matching `ConflictingValue*`, no index signature, byte-identical across runs.

### Codegen script + drift-check (D-14)
```python
# services/ai/scripts/codegen.py
from pydantic2ts import generate_typescript_defs
OUT = "../../packages/shared-types/index.d.ts"   # resolve to repo path
generate_typescript_defs("schemas", OUT, json2ts_cmd="./node_modules/.bin/json2ts")
```
```python
# services/ai/tests/test_codegen_drift.py
import tempfile, pathlib
from pydantic2ts import generate_typescript_defs

COMMITTED = pathlib.Path(__file__).parents[2] / "packages/shared-types/index.d.ts"

def test_ts_contract_not_stale():
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d) / "index.d.ts"
        generate_typescript_defs("schemas", str(tmp), json2ts_cmd="./node_modules/.bin/json2ts")
        assert tmp.read_text() == COMMITTED.read_text(), \
            "TS contract is stale — run scripts/codegen.py and commit packages/shared-types"
```
*Output is deterministic (verified: identical SHA across runs), so byte-equality is a safe assertion — no normalization needed.*

### LangGraph trivial graph → SSE (PLAT-04 proof)
```python
# Source: Context7 docs.langchain.com/oss/python/langgraph/streaming + sse-starlette README
from typing import TypedDict
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from sse_starlette import EventSourceResponse
import json

class S(TypedDict):
    topic: str

def demo(state: S):
    w = get_stream_writer()
    w({"type": "status",  "payload": {"phase": "starting"}})
    w({"type": "partial", "payload": {"chunk": "hello"}})
    w({"type": "result",  "payload": {"ok": True}})
    return {}

graph = StateGraph(S).add_node(demo).add_edge(START, "demo").add_edge("demo", END).compile()

# FastAPI route
async def stream_demo(request):
    async def gen():
        async for chunk in graph.astream({"topic": "x"}, stream_mode="custom"):
            yield {"data": json.dumps(chunk)}     # chunk is already {"type":..., "payload":...}
        yield {"data": json.dumps({"type": "done", "payload": {}})}
    return EventSourceResponse(gen())
# Proof: curl -N http://localhost:8000/stream/demo  →  data: {"type":"status",...} ...
```

### LLM tier factory + access ping (PLAT-03)
```python
# Source: Context7 docs.langchain.com/oss/python/langchain/models (init_chat_model)
import os
from langchain.chat_models import init_chat_model

_TIER_ENV = {"reasoning": "MODEL_REASONING", "cheap": "MODEL_CHEAP"}

def get_llm(tier: str):
    model_id = os.environ[_TIER_ENV[tier]]   # e.g. gpt-5.4 / gpt-5.4-mini
    return init_chat_model(model_id)

def verify_access() -> None:
    for tier in ("reasoning", "cheap"):
        try:
            get_llm(tier).invoke("ping")     # smallest live call; see Pitfall 5 re: token cap
        except Exception as e:
            raise RuntimeError(f"No access to {tier} model "
                               f"({os.environ[_TIER_ENV[tier]]}): {e}") from e
```
```python
# FastAPI startup (D-16) — fail loud
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_access()        # raises → server refuses to start with a clear message
    yield

app = FastAPI(lifespan=lifespan)
```

### Prompt registry (PROMPT-01)
```python
# services/ai/prompts/registry.py
import frontmatter, pathlib, re

_DIR = pathlib.Path(__file__).parent
_VER = re.compile(r"^(?P<id>.+)\.v(?P<n>\d+)\.md$")

def load(prompt_id: str):
    """Return the highest-version .md for prompt_id as a frontmatter Post (.metadata + .content)."""
    cands = []
    for p in _DIR.glob(f"{prompt_id}.v*.md"):
        m = _VER.match(p.name)
        if m: cands.append((int(m["n"]), p))
    if not cands:
        raise KeyError(f"no prompt '{prompt_id}'")
    return frontmatter.load(max(cands)[1])   # latest version wins
```
```yaml
# services/ai/prompts/extraction.v1.md  (stub — one of 7)
---
id: extraction
version: 1
intent: Extract per-vendor structured fields with evidence; flag missing/unclear/conflicting/unsupported.
model_tier: reasoning
failure_handling: Never fill missing info. Evidence offsets validated in code (P2 grounding gate).
---
TODO: extraction prompt body (fleshed out in Phase 3).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangGraph 0.x graph/stream API | LangGraph **1.x** (`get_stream_writer`, `stream_mode="custom"`) | LangGraph 1.0 (2026) | Training data is stale; use the v1 surface above |
| `langchain` 0.x imports | `langchain` 1.x; `init_chat_model` in `langchain.chat_models` | LangChain 1.0 (2026) | `langchain-openai` is now 1.3.x; pin accordingly |
| pydantic v1 `GenericModel` + `__concrete_name__` | pydantic v2 `BaseModel, Generic[T]`; auto `$defs` names like `Field_str_` | pydantic 2.x | Generic names are deterministic; codegen handles them |
| Hand-rolled `data: ...\n\n` SSE | `sse-starlette` `EventSourceResponse` | — | Correct framing + keepalive |

**Deprecated/outdated:**
- `pydantic2ts` as a *PyPI package name* — it does not exist on PyPI. The package is **`pydantic-to-typescript`**; `pydantic2ts` is only the CLI command it installs. [VERIFIED: PyPI returns 404 for `pydantic2ts`]
- LangGraph v0 streaming tutorials — superseded by the v1 API.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `turbo` / `next` / `prettier` "latest" versions | Standard Stack (JS) | Low — pin at install time; not load-bearing for the contract |
| A2 | Exact gpt-5.4 access-ping param surface (`max_tokens` vs `max_completion_tokens`, reasoning-model quirks) | Pitfall 5 / Code Examples | Medium — a wrong param makes the ping error spuriously; confirm against the model before hardcoding the cap |
| A3 | slopcheck legitimacy verdicts (tool unavailable) | Package Legitimacy Audit | Low — all packages are mandated/established and version-verified on the correct registry |
| A4 | Decimal → TS `string` is the desired contract shape | Pattern 1 | Low — correct (JSON has no decimal), but planner should confirm UI expects string money |

## Open Questions

1. **`.env` location after the D-02 relocation**
   - What we know: `.env` is at repo root, empty, gitignored. The AI service reads it.
   - What's unclear: whether to keep it at root or move to `services/ai/`.
   - Recommendation: keep one `.env` at repo root and load it from `services/ai` (e.g. `dotenv` pointing up one level), or document a `services/ai/.env`. Either works — pick one and document in README (SHIP-02 lives in P5 but the setup step is referenced by `verify_access.py` now).

2. **Empty `export interface Strict {}` handling**
   - What we know: a shared `extra="forbid"` base leaks into TS.
   - Recommendation: set `model_config` per-model (shown in Code Examples) rather than a shared exported base, OR strip the empty interface in `codegen.py`. Planner picks; per-model config is the lazy correct choice.

3. **Where the trivial demo graph lives** (Claude's discretion per D-09)
   - Recommendation: `services/ai/agents/_demo.py` or inline in `api/app.py`. Trivial; keep it next to the route it proves.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Python deps/env (D-17) | ✓ | 0.9.26 | — |
| pnpm | JS workspace (D-03) | ✓ | 10.28.1 | — |
| node | json2ts, Next.js | ✓ | 25.3.0 | — |
| python3 | services/ai | ✓ | 3.12.12 | — |
| ruff | lint+format (D-17) | ✓ | 0.15.13 | — |
| pytest | tests incl. drift-check (D-14) | ✓ | 9.0.2 | — |
| turbo | JS orchestration (D-03) | ✗ | — | Install as root devDependency (`pnpm add -Dw turbo`) |
| json-schema-to-typescript | codegen (PLAT-02) | ✗ (verified installable, v15.0.4) | — | Install as root devDependency — **blocking for codegen** |
| OpenAI API access to gpt-5.4 / mini | PLAT-03 ping | ? (`.env` empty — no key set yet) | — | None — PLAT-03's whole point is to verify this; the ping must run with a real key during execution |

**Missing dependencies with no fallback:**
- OpenAI org/key access to `gpt-5.4` / `gpt-5.4-mini` — the `.env` is empty. The PLAT-03 deliverable *is* the check; execution must supply a real `OPENAI_API_KEY` (+ model IDs) before the access ping and FastAPI startup can pass. The planner should make "set `.env` keys" an explicit prerequisite/checkpoint.

**Missing dependencies with fallback (just install):**
- `turbo`, `json-schema-to-typescript` — both installed during scaffolding; not blockers beyond a normal `pnpm add`.

## Sources

### Primary (HIGH confidence)
- **Empirical test this session** — pydantic 2.13.4 + pydantic-to-typescript 2.0.0 + json-schema-to-typescript 15.0.4: generated the actual TS from a generic `Field[T]`, confirmed clean output, `extra="forbid"` removes the index signature, and byte-identical output across runs. (The decisive D-05 evidence.)
- Context7 `/websites/langchain_oss_python_langgraph` — custom streaming: `get_stream_writer()`, `stream_mode="custom"`, `astream`.
- Context7 `/websites/langchain_oss_python_langchain` — `init_chat_model("gpt-5.4")` (docs literally use gpt-5.4).
- Context7 `/sysid/sse-starlette` — `EventSourceResponse`, ping/shutdown params.
- PyPI JSON API (2026-06-27) — all Python package versions + Python requirements + upload dates.
- `npm view json-schema-to-typescript version` → 15.0.4.

### Secondary (MEDIUM confidence)
- GitHub `phillipdupuis/pydantic-to-typescript` (via WebFetch) — package name vs `pydantic2ts` CLI, json2ts dependency, `generate_typescript_defs` API.
- pydantic GitHub issues #7376 / #7308 (via WebSearch) — generic-model JSON-schema naming (the `Literal`-param ugliness applies to Literal params, *not* simple `Field[str]` — confirmed by the empirical test).

### Tertiary (LOW confidence)
- gpt-5.4 access-ping exact param surface — not verified against the live model (A2); flagged in Pitfall 5.

## Metadata

**Confidence breakdown:**
- D-05 generic-vs-concrete verdict: **HIGH** — settled by direct empirical codegen, not inference. **Verdict: build the generic `Field[T]`; the fallback is unnecessary.**
- Standard stack + versions: **HIGH** — all verified against the correct registries 2026-06-27.
- LangGraph/SSE/LLM patterns: **HIGH** — current Context7 docs for v1 APIs.
- gpt-5.4 ping param details: **MEDIUM/LOW** — confirm the token-cap param against the model at execution.

**Research date:** 2026-06-27
**Valid until:** ~2026-07-27 for stable packages; ~2026-07-04 for LangGraph/langchain (fast-moving major-version churn — re-verify if planning slips a week).
