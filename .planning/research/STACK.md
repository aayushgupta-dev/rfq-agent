# Stack Research

**Domain:** Prompt-driven procurement RFQ extraction & vendor-comparison AI prototype (5-day build)
**Researched:** 2026-06-27
**Confidence:** HIGH (all versions verified against PyPI/npm/official docs as of June 2026, not training data)

> **Scope note.** The stack is pre-decided in `CLAUDE.md` §5. This document does **not** relitigate
> those choices — it pins **current, specific versions** for June 2026, fills the gaps the spec left
> open (SSE transport lib, OpenAI API surface, pydantic→TS tooling), and flags the version/compat
> pitfalls that can burn time on a 5-day timeline. The biggest substantive findings:
> 1. **GPT-5.4 is real and current** (released March 5 2026); model strings are `gpt-5.4` and
>    `gpt-5.4-mini`. Confirmed against OpenAI docs.
> 2. **LangChain + LangGraph are both past 1.0** (LangChain 1.3.x, LangGraph 1.2.x). The v1 API
>    surface (`init_chat_model`, `with_structured_output`) is stable and is the path to use.
> 3. **`openai` Python SDK is now 2.x** and defaults to the **Responses API**. This matters for the
>    "low-level client" escape hatch — see the gotcha below.
> 4. **LangGraph 1.x streaming uses a `StreamPart` (`version="v2"`) format**, not the old
>    `(mode, chunk)` tuple. This is the load-bearing detail for the SSE wiring.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.12 (pin `>=3.11,<3.13`) | Runtime for `services/ai` | 3.12 is the safe sweet spot — all libs below support 3.10–3.13; 3.12 has the broadest wheel coverage and avoids any 3.13-only edge cases on a 5-day clock. |
| **LangChain (Python)** | 1.3.11 (`langchain`), `langchain-core` 1.4.x, `langchain-openai` 1.2.x | Model abstraction, prompt templating, structured-output binding | Mandated by CLAUDE.md. v1 line is stable; `init_chat_model("openai:gpt-5.4")` + `with_structured_output(Model)` is the canonical, documented path (confirmed via Context7). |
| **LangGraph (Python)** | 1.2.6 | Agent/graph orchestration for the 4 agents (rfq_gen, vendor_gen, extraction, comparison) | Mandated. 1.x is GA, durable execution + first-class streaming. `StateGraph` is the right abstraction for the extraction→comparison pipeline. |
| **OpenAI Python SDK** | 2.x (latest, June 2026) | Low-level model client only (per CLAUDE.md — orchestration stays in LangChain) | Only needed for the rare one-off structured call where LangChain doesn't fit. `langchain-openai` wraps it; you mostly won't import `openai` directly. |
| **OpenAI model** | `gpt-5.4` (reasoning-heavy), `gpt-5.4-mini` (cheap tasks) | The LLM | Confirmed available on Chat Completions + Responses API. CLAUDE.md forbids GPT-5.5 (cost) — honored. Keep model IDs env-configured (`OPENAI_MODEL_MAIN`, `OPENAI_MODEL_MINI`). |
| **FastAPI** | 0.135.x | AI service HTTP + SSE endpoints | Mandated. 0.135.0 added a **built-in `EventSourceResponse`** with Rust-side pydantic serialization — but see SSE note below; prefer `sse-starlette` for control. |
| **uvicorn** | latest (June 2026) | ASGI server, hot reload in dev | Standard FastAPI pairing. Run `uvicorn ... --reload` locally. |
| **pydantic** | 2.13.4 | Structured-output schemas (source of truth for the contract) | Mandated v2. All extraction/comparison outputs are validated pydantic objects. `pydantic.v1` shim exists but is irrelevant here — write pure v2. |
| **Next.js** | 16.2 (App Router) | Buyer-facing web app (thin client) | Mandated. 16.x ships Turbopack + React 19.2 by default. App Router only. No AI SDKs, no business logic. |
| **pnpm** | 9.x (use 10.x if available; pin via `packageManager` in root `package.json`) | Monorepo package manager | Mandated. Workspace-aware, fast, disk-efficient. Pin the exact version with Corepack to avoid CI drift. |
| **Turborepo** | 2.x | Monorepo task runner / caching | Mandated. For a 2-app + 1-package repo, you mainly need `turbo run build/dev/lint`; remote caching is optional for a solo 5-day build. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **sse-starlette** | latest (released May 2026) | SSE transport for FastAPI → Next.js streaming | **Recommended for all streaming endpoints.** More control than FastAPI's built-in `EventSourceResponse`; battle-tested generator-based API. Install `sse-starlette[uvicorn]`. |
| **pypdf** | 6.14.2 | Best-effort PDF text extraction | Vendor upload (PDF). Pure-Python, no system deps — critical for clean Render/Railway deploy. `page.extract_text()`. No OCR (out of scope per assignment §11). |
| **python-docx** | 1.2.0 | Word (.docx) text extraction | Vendor upload (Word). Iterate paragraphs + tables. |
| **openpyxl** | 3.1.5 | Excel (.xlsx) cell extraction | Vendor upload (Excel). Read-only mode for speed. Pricing tables often live here. |
| **python-pptx** | 1.0.2 | PowerPoint (.pptx) text extraction | Vendor upload (PPT). Walk slides → shapes → text frames. Vendor proposals are frequently decks. |
| **python-multipart** | latest | File upload parsing in FastAPI | Required for `UploadFile` form handling. Easy to forget — FastAPI errors without it. |
| **pydantic-settings** | latest (v2) | Env/config loading (`OPENAI_API_KEY`, model IDs, AI base URL) | Typed settings object; keeps env handling clean and documented for the README. |
| **httpx** | latest | (Already a transitive dep of openai/FastAPI) | Only if you make direct outbound HTTP; usually not needed. |
| **pydantic-to-typescript** (`pydantic2ts`, `>=2`) | latest | Generate `packages/shared-types` from pydantic schemas | **The recommended contract bridge — see dedicated section below.** |

### Frontend Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **React** | 19.2 (ships with Next 16.2) | UI runtime | Bundled with Next.js; don't pin separately beyond what Next requires. |
| **TypeScript** | 5.x (latest) | Web app + shared-types typing | Standard. `strict: true`. |
| **EventSource (native)** or **`@microsoft/fetch-event-source`** | native / latest | Consume SSE in the browser | Native `EventSource` is GET-only and can't send a body/headers easily. If extraction is triggered by a POST with a payload, use `@microsoft/fetch-event-source` (POST + SSE). Decide based on endpoint shape. |
| **Tailwind CSS** | 4.x | Styling (design tokens + primitives, per CLAUDE.md "no third-party UI kits") | Optional but the fastest path to a clean, token-driven buyer UI without a component library. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | Python dependency + venv management for `services/ai` | Mandated by CLAUDE.md §10. `uv add <pkg>`, `uv run uvicorn ...`, `uv run pytest`. Fast, lockfile-based. |
| **Corepack** | Pin pnpm version across machines/CI | `corepack enable` + `packageManager` field. Prevents "works on my machine" pnpm drift. |
| **pytest** | Python code-level tests (schema validation, grounding, comparability) | `uv run pytest` from `services/ai/` (CLAUDE.md §11). Prioritize grounding tests (every fact has an evidence span). |
| **vitest** | Web logic tests | Only where there's logic worth covering (CLAUDE.md §11). |
| **ruff** | Python lint + format | Fast, single-tool replacement for flake8/black/isort. Optional but cheap to add. |
| **curl -N** | Manual SSE verification | `curl -N <url>` to confirm `data: {...}` events stream (CLAUDE.md §11). |

## The pydantic → TypeScript Contract (concrete recommendation)

`services/ai/schemas/` (pydantic) is the source of truth; `packages/shared-types` mirrors it
(CLAUDE.md §15). **Recommended approach: `pydantic-to-typescript` (`pydantic2ts`), run as a
codegen script — not a manual mirror.**

**Why `pydantic2ts` over the alternatives:**
- **vs. manual mirror:** A manual mirror is the documented fallback, but on a 5-day build with
  evolving extraction/comparison schemas it *will* drift, and silent drift between the UI and AI is
  called out as a top gotcha (CLAUDE.md §15). Codegen makes the contract enforceable.
- **vs. `datamodel-code-generator`:** That tool generates *pydantic from a schema* (the wrong
  direction here, though it can emit TS via JSON Schema). `pydantic2ts` is purpose-built for the
  exact direction we need (pydantic → TS interfaces) and has a one-line CLI.

**Recommended wiring:**

```bash
# in services/ai (uv environment)
uv add --dev pydantic-to-typescript

# codegen: point at the module that re-exports all schema models
uv run pydantic2ts --module services.ai.schemas --output ../../packages/shared-types/index.d.ts
```

- Expose a single `schemas/__init__.py` (or a `models.py`) that re-exports every model the UI needs,
  so one command regenerates the whole contract.
- Add a `turbo`/`package.json` script (e.g. `gen:types`) and run it whenever a schema changes.
- Optional (valuable for the rubric's "structured schemas" bonus): a CI/pre-commit check that fails
  if generated TS is stale — the project's own §15 drift guard, automated.

**Confidence:** HIGH. `pydantic-to-typescript>=2` explicitly supports pydantic v2.

## Installation

```bash
# --- AI service (services/ai) via uv ---
uv add langchain langchain-openai langgraph pydantic pydantic-settings \
       fastapi "uvicorn[standard]" "sse-starlette[uvicorn]" python-multipart \
       pypdf python-docx openpyxl python-pptx openai
uv add --dev pytest ruff pydantic-to-typescript

# --- Web app (apps/web) via pnpm ---
pnpm add next@16 react@19 react-dom@19
pnpm add -D typescript @types/react @types/node vitest tailwindcss
# if POST-triggered SSE:
pnpm add @microsoft/fetch-event-source

# --- Monorepo root ---
pnpm add -D turbo
# pin pnpm: set "packageManager": "pnpm@9.x.x" in root package.json, then `corepack enable`
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `sse-starlette` | FastAPI 0.135 built-in `EventSourceResponse` | If you want zero extra deps and a very simple stream; built-in does pydantic serialization Rust-side (faster). For LangGraph streaming with custom event types/heartbeats, `sse-starlette`'s generator API is easier to reason about — recommended here. |
| `pydantic2ts` codegen | Manual TS mirror | Only if codegen fails on a tricky generic/union and you're out of time — but treat manual mirroring as a debt, not the plan. |
| `pypdf` | PyMuPDF (`fitz`) | If text extraction quality on a specific messy PDF is poor and you need better layout handling. PyMuPDF is AGPL/commercial-licensed — fine for a prototype but heavier. Start with `pypdf` (pure-Python, MIT). |
| `with_structured_output` (LangChain) | `openai` SDK `responses.parse()` directly | Use the raw SDK only for a one-off call where LangChain's binding is awkward (CLAUDE.md sanctions this narrow use). Default to LangChain so orchestration stays in one place. |
| `@microsoft/fetch-event-source` | native `EventSource` | Native is simpler **if** extraction is triggered by a GET with query params. Use the lib when you need POST + body + headers for SSE. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **OpenAI Agents SDK** (`openai-agents`) | Explicitly forbidden (CLAUDE.md §5, PROJECT.md). Note: it now requires `openai` 2.x, but that's irrelevant — orchestration stays in LangGraph. | LangChain + LangGraph |
| **GPT-5.5** | Forbidden (cost). Also `responses.create()` examples online default to it — don't copy-paste model strings blindly. | `gpt-5.4` / `gpt-5.4-mini` |
| **Database / vector store / queue** | No feature in a 5-day prototype needs persistence beyond files/in-memory (PROJECT.md Out of Scope, CLAUDE.md §10/§15). | In-memory + `data/` files |
| **Heavy OCR / layout parsers** (Tesseract, Unstructured, AWS Textract) | Out of scope (assignment §11); best-effort text extraction is enough. Adds system deps that complicate Render/Railway deploy. | `pypdf` / `python-docx` / `openpyxl` / `python-pptx` |
| **PyPDF2** | Deprecated/merged into `pypdf`. Old tutorials still reference it. | `pypdf` 6.x |
| **Running FastAPI/LangGraph on Vercel** | Vercel is for the Next.js app only; the Python service is long-running (CLAUDE.md §12/§15). | Render or Railway for `services/ai` |
| **AI SDKs / business logic in `apps/web`** | The web app is a thin client (CLAUDE.md §5). | Call the AI service over HTTP/SSE |
| **LangChain `streaming=False` blanket setting** | Would defeat the SSE requirement (never buffer-and-return). | Stream via LangGraph `.stream(..., version="v2")` |

## Stack Patterns by Variant

**If extraction is triggered by a POST with a JSON payload (likely — you're posting vendor text):**
- Use `sse-starlette` `EventSourceResponse` on the server and `@microsoft/fetch-event-source` on the client.
- Because native browser `EventSource` only supports GET and can't carry a request body.

**If you want the absolute simplest streaming path for the demo:**
- A GET endpoint keyed by a pre-uploaded vendor ID + native `EventSource`.
- Because it removes a client dependency; the tradeoff is you upload/stage the response first, then stream extraction by ID.

**If `pypdf` text quality is poor on a specific messy sample:**
- Swap that one path to PyMuPDF; keep the others on the pure-Python libs.
- Because only PDFs tend to have layout issues; don't add the dep globally.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `langchain` 1.3.x | `langchain-core` 1.4.x, `langchain-openai` 1.2.x | Keep the `langchain-*` family on the same major (1.x). Don't mix a 0.x `langchain-community` feature in unless needed. |
| `langchain-openai` 1.2.x | `openai` 2.x | `langchain-openai` pulls a compatible `openai`; don't pin `openai` 1.x by hand (would conflict). |
| `langgraph` 1.2.x | `langchain-core` 1.4.x | Same 1.x era. Streaming API is **v2 `StreamPart`** — see gotcha. |
| `pydantic` 2.13.x | `langchain` 1.x, `fastapi` 0.135.x, `pydantic2ts` >=2 | All are pydantic-v2 native. `pydantic2ts` <2 only supports v1 — pin `>=2`. |
| Python 3.12 | every lib above | All support 3.10–3.13; 3.12 maximizes wheel availability. |
| `sse-starlette` (May 2026) | `fastapi` 0.135.x, Python 3.10–3.13 | Install the `[uvicorn]` extra. |
| Next.js 16.2 | React 19.2, Node 20+ | React is bundled; let Next pin it. |

## Critical Gotchas for a 5-Day Timeline

Ordered by likelihood-to-burn-time:

1. **LangGraph 1.x streaming format changed.** Use `graph.stream(input, stream_mode=[...],
   version="v2")` which yields unified `StreamPart` dicts (`chunk["type"]`, `chunk["data"]`). Older
   tutorials unpack `(mode, chunk)` tuples — that's the legacy format and will mismatch your SSE
   serializer. **This is the riskiest copy-paste trap.** (Confidence: HIGH — Context7 docs.)
2. **`openai` SDK is 2.x and defaults to the Responses API.** Most blog examples now use
   `client.responses.create(model="gpt-5.5", ...)`. If you reach for the raw SDK, (a) use
   `gpt-5.4`, not 5.5, and (b) be aware Responses vs Chat Completions have different shapes. Easiest
   to avoid entirely by staying in `langchain-openai`. (Confidence: HIGH.)
3. **Confirm the exact model string before hardcoding.** CLAUDE.md mandates this. Use `gpt-5.4` /
   `gpt-5.4-mini` from env vars; do a single live "ping" call on day 1 to confirm your API key/org
   has access before building on it. (Confidence: HIGH model exists; access is account-specific.)
4. **`python-multipart` is a hidden requirement** for FastAPI file uploads — install it explicitly
   or `UploadFile` endpoints raise at runtime. (Confidence: HIGH.)
5. **pydantic→TS drift** is the named §15 failure mode. Wire `pydantic2ts` as a script on day 1, not
   day 4, so the contract is enforceable from the start. (Confidence: HIGH.)
6. **Grounding must be enforced in code, not by the model.** Not a version issue but a stack
   discipline one: after `with_structured_output` returns evidence spans, validate each span is a
   substring of the source text in Python before display. The schema can *carry* the span; it cannot
   *guarantee* it. (Confidence: HIGH — restating CLAUDE.md §8 as a stack requirement.)
7. **Pin pnpm via `packageManager` + Corepack** so the monorepo resolves identically in dev and on
   Vercel's build. (Confidence: MEDIUM — best practice, not a hard blocker.)

## Sources

- OpenAI — `https://developers.openai.com/api/docs/models/gpt-5.4`, `https://openai.com/index/introducing-gpt-5-4/` — confirmed GPT-5.4 (released 2026-03-05), model strings `gpt-5.4`/`gpt-5.4-mini`. HIGH.
- PyPI / GitHub releases — `langchain` 1.3.11 (2026-06-22), `langchain-core` 1.4.8, `langchain-openai` 1.2.2; `langgraph` 1.2.6 (2026-06-18); `pydantic` 2.13.4; `pypdf` 6.14.2 (2026-06-23); `openpyxl` 3.1.5; `python-docx` 1.2.0; `python-pptx` 1.0.2; `openai` 2.x (2026-06-01); `sse-starlette` (2026-05-12). HIGH.
- FastAPI docs — `https://fastapi.tiangolo.com/tutorial/server-sent-events/`, FastAPI 0.135.1 (2026-03-01) added built-in `EventSourceResponse`. HIGH.
- Context7 `/websites/langchain_oss_python_langchain` — `init_chat_model("openai:gpt-5.4-mini")`, `with_structured_output(Model)`, LangGraph v2 `StreamPart` streaming. HIGH.
- Next.js / Turborepo — `https://nextjs.org/docs`, Next.js 16.2 + React 19.2 + Turbopack default; Turborepo 2.x + pnpm monorepo. HIGH.
- `pydantic-to-typescript` (`pydantic2ts`) PyPI + GitHub — `>=2` supports pydantic v2; CLI `pydantic2ts --module ... --output ...`. HIGH.

---
*Stack research for: prompt-driven procurement RFQ extraction & vendor-comparison AI prototype*
*Researched: 2026-06-27*
