# Architecture Research

**Domain:** Prompt-driven procurement RFQ extraction & vendor-comparison AI prototype (Next.js web + FastAPI/LangGraph Python service, monorepo)
**Researched:** 2026-06-27
**Confidence:** HIGH

> Scope note: The *topology* is already decided in `CLAUDE.md §5` (pnpm+turbo monorepo: `apps/web` thin Next.js client + `services/ai` FastAPI/LangGraph + `packages/shared-types` contract). This document does **not** redesign that. It details **how the AI pipeline and the cross-app contract are structured** for reliability and a clean 5-day build: LangGraph graph design, structured-output flow, **code-enforced** grounding/evidence validation, SSE event shape, the pydantic→TS contract, and the build order.

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  apps/web  (Next.js App Router, Vercel)  — THIN CLIENT, no AI logic    │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌──────────┐  │
│  │ RFQ      │ │ Vendor   │ │ Extraction │ │ Vendor    │ │ Prompt   │  │
│  │ Overview │ │ Upload   │ │ Review     │ │ Comparison│ │ Trace    │  │
│  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └─────┬─────┘ └────┬─────┘  │
│       │            │             │              │            │        │
│       └──── EventSource (SSE consume) ──────────┴────────────┘        │
│              fetch() POST for upload; types from @aerchain/shared-types │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │  HTTP + SSE (text/event-stream)
                                     │  data: {"type": "...", "payload": {...}}
┌────────────────────────────────────▼───────────────────────────────────┐
│  services/ai  (FastAPI + LangGraph, Python, Render/Railway)             │
│  ┌────────────────────────── api/ (routers) ─────────────────────────┐  │
│  │  /rfq/generate  /vendor/generate  /extract  /compare  /prompts     │  │
│  │  each long-running route = EventSourceResponse (SSE generator)     │  │
│  └───────────────┬──────────────────────────────┬─────────────────────┘ │
│                  │                               │                       │
│  ┌───────────────▼─────────┐      ┌──────────────▼──────────────┐        │
│  │ agents/ (LangGraph)     │      │ grounding/ (PURE CODE)       │        │
│  │  rfq_gen   vendor_gen   │      │  evidence span verifier      │        │
│  │  extraction  comparison │─────▶│  substring + fuzzy match     │        │
│  │  (StateGraph + nodes)   │      │  flag downgrade on miss      │        │
│  └───────┬─────────────────┘      └──────────────────────────────┘        │
│          │ uses                                                            │
│  ┌───────▼────────┐   ┌───────────────────┐   ┌────────────────────────┐ │
│  │ prompts/       │   │ schemas/ (pydantic)│   │ llm/ (model client)    │ │
│  │ THE PROMPT PACK│   │ SOURCE OF TRUTH    │   │ GPT-5.4 / 5.4-mini     │ │
│  │ versioned text │   │ for the contract   │   │ structured output bind │ │
│  └────────────────┘   └─────────┬──────────┘   └────────────────────────┘ │
└──────────────────────────────────┼───────────────────────────────────────┘
                                    │ generates / mirrors
                          ┌─────────▼──────────────┐
                          │ packages/shared-types  │  TS mirror of pydantic
                          │ (the contract)         │  consumed by apps/web
                          └────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `apps/web` screens | Render buyer experience; consume SSE; never compute AI facts | Next.js App Router server/client components; `EventSource` for streams; `fetch` for upload |
| `api/` routers | HTTP surface; turn an agent run into an SSE event stream; validate request bodies | FastAPI routes returning `EventSourceResponse` (native, FastAPI ≥0.122) or `StreamingResponse(media_type="text/event-stream")` |
| `agents/` (LangGraph) | Orchestrate each agent as a `StateGraph` of nodes; emit progress + tokens | `StateGraph(TypedDict state)`, nodes = python fns, compiled graph `.astream(...)` |
| `grounding/` | **Code-enforced** evidence-span validation; no LLM trust | Pure python: normalize → substring → `rapidfuzz` fuzzy match → flag downgrade |
| `prompts/` | The Prompt Pack — versioned prompt source, the highest-graded artifact | Python module per prompt (template + version tag + docstring) or `.md`/`.j2` + loader |
| `schemas/` | Pydantic models = **single source of truth** for the contract | `pydantic.BaseModel`; `.model_json_schema()` drives both OpenAI structured output AND TS generation |
| `llm/` | Low-level model client + structured-output binding; model-tier discipline | LangChain `ChatOpenAI(...).with_structured_output(Model)`; mini vs full per task |
| `packages/shared-types` | TS mirror of pydantic; keeps UI/AI from drifting | Generated `.ts` from exported JSON Schema (see Contract section) |

---

## Recommended Project Structure

```
services/ai/
├── api/
│   ├── main.py                 # FastAPI app, CORS, router mount, /health
│   ├── deps.py                 # shared deps (llm client, settings)
│   ├── sse.py                  # sse_event(type, payload) -> formatted SSE; one helper, reused
│   └── routers/
│       ├── rfq.py              # POST /rfq/generate            (SSE)
│       ├── vendor.py           # POST /vendor/generate         (SSE)
│       ├── extract.py          # POST /extract                 (SSE)
│       ├── compare.py          # POST /compare                 (SSE)
│       └── prompts.py          # GET  /prompts, GET /prompts/{id}, GET /traces (NOT streamed)
├── agents/
│   ├── extraction/
│   │   ├── graph.py            # build_extraction_graph() -> compiled StateGraph
│   │   ├── state.py            # ExtractionState (TypedDict) — graph-internal, NOT the contract
│   │   └── nodes.py            # segment → extract → ground → flag (node fns)
│   ├── comparison/
│   │   ├── graph.py            # build_comparison_graph()
│   │   ├── state.py            # ComparisonState (TypedDict)
│   │   └── nodes.py            # comparability_gate → dimension_compare → attention_points
│   ├── rfq_gen/                # graph.py + nodes.py
│   └── vendor_gen/             # graph.py + nodes.py
├── grounding/
│   ├── verify.py               # verify_evidence(snippet, source) -> GroundingResult
│   └── normalize.py            # whitespace/quote/case normalization for matching
├── prompts/                    # THE PROMPT PACK (first-class, versioned)
│   ├── registry.py             # load_prompt(id, version) + list_prompts()
│   ├── rfq_generation.py
│   ├── vendor_generation.py
│   ├── messy_data.py
│   ├── ui_ux_generation.py
│   ├── extraction.py
│   ├── comparison.py
│   └── clarification.py
├── schemas/                    # SOURCE OF TRUTH for the contract
│   ├── rfq.py                  # RFQ, LineItem, Questionnaire, Compliance
│   ├── vendor.py               # VendorResponse (raw input wrapper)
│   ├── extraction.py           # ExtractionResult, ExtractedField, Evidence, FieldFlag
│   ├── comparison.py           # ComparisonResult, Comparability, DimensionRow, ClarificationQ
│   └── sse.py                  # SSEEvent[type, payload] envelope (also mirrored to TS)
├── llm/
│   └── client.py               # get_llm(tier) -> ChatOpenAI; with_structured_output helpers
├── scripts/
│   └── export_schema.py        # pydantic -> JSON Schema -> packages/shared-types
└── tests/
    ├── test_grounding.py       # fabricated span is downgraded; real span passes (CRITICAL)
    ├── test_schemas.py         # schema validation round-trips
    └── test_comparability.py   # non-comparable vendors flagged, not silently ranked

apps/web/
├── lib/
│   ├── api.ts                  # base URL, fetch wrappers
│   └── sse.ts                  # openStream(url, body, onEvent) — single SSE consumer
└── app/(buyer)/                # the 5 screens, consume @aerchain/shared-types

packages/shared-types/
├── src/index.ts                # GENERATED — do not hand-edit
└── package.json                # @aerchain/shared-types
```

### Structure Rationale

- **`schemas/` is its own top-level dir, imported by both agents and api.** It is the contract. Treating it as a leaf dependency (nothing in `schemas/` imports `agents/`) keeps the source-of-truth clean and makes the TS export trivially mechanical.
- **`grounding/` is separated from `agents/` deliberately.** Grounding is *pure code with no LLM*. Physically separating it makes the rubric-critical "we don't trust the model" story legible to a reviewer and makes it unit-testable in isolation (`test_grounding.py`).
- **Graph-internal state (`agents/*/state.py`) is NOT the contract.** The `TypedDict` a `StateGraph` threads between nodes is an implementation detail. The pydantic models in `schemas/` are what cross the API boundary. Conflating them couples the UI to LangGraph internals — keep them distinct.
- **`prompts/` is a code module, not buried strings.** Each prompt is a versioned artifact with a docstring (what / why / how it handles missing data). This directly serves the 30%-weighted Prompt Pack deliverable and the `/prompts` + `/traces` endpoints.
- **One SSE helper (`api/sse.py`) and one SSE consumer (`web/lib/sse.ts`).** Every streaming route and every screen uses the same `{type, payload}` envelope. No per-route bespoke event formats.

---

## The AI Pipeline — LangGraph Graph Design

### Extraction agent graph

The extraction agent is a **linear `StateGraph` with a hard grounding gate**. The key design decision: **the LLM extracts, code validates, then code (not the LLM) sets the final flag.** This is the heart of the rubric's reliability requirement.

```
        ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
START ─▶ │ segment      │ ─▶  │ extract     │ ─▶  │ ground       │ ─▶  │ finalize     │ ─▶ END
        │ (chunk +     │     │ (LLM →      │     │ (PURE CODE   │     │ (assemble    │
        │  index src)  │     │  pydantic)  │     │  verify span)│     │  ExtractionResult)│
        └──────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
              │                    │                    │                    │
        emit "stage:segment"  emit "stage:extract" emit per-field      emit "result"
                              + token stream       "evidence:verified/  (final payload)
                                                    downgraded"
```

**Node-by-node:**

1. **`segment`** — Take the raw vendor text (pasted or best-effort-extracted from PDF/Word/Excel/PPT). Split into addressable units (sections/paragraphs) and keep **character offsets** into the original source. This is what makes later span verification possible. *No LLM here* — pure text handling. Emits a `stage` event.

2. **`extract`** — One LLM call per logical area (or one structured call returning all areas), bound to the `ExtractionResult` pydantic schema via `with_structured_output`. The prompt instructs the model to, for every extracted field, return **the verbatim evidence snippet** it copied from the source plus an initial flag (`present`/`missing`/`unclear`/`conflicting`/`unsupported`). **Crucially, the prompt is told the snippet must be copied verbatim** — but we never trust that; the next node checks it. Streams tokens via `stream_mode="messages"`.

3. **`ground`** — **Pure code, no LLM.** For every `ExtractedField` with a claimed evidence snippet, call `grounding.verify_evidence(snippet, source_text)`. If the snippet does not match the source (exact-after-normalization, or fuzzy ≥ threshold), the field's flag is **downgraded to `unsupported` and the value is suppressed from the "fact" view** — regardless of what the model said. Emits an `evidence` event per field so the trace shows verified vs. downgraded.

4. **`finalize`** — Assemble the validated `ExtractionResult` (only code-verified facts shown as facts; everything else carries an explicit flag). Emit the final `result` event.

**Why linear, not agentic/cyclic:** For a 5-day prototype, a cyclic "re-ask the model to fix its evidence" loop adds cost, latency, and failure surface for marginal benefit. The deterministic downgrade ("if you can't prove it, it's `unsupported`") is *more* defensible to a reviewer than a self-correcting model. Keep the graph linear; let code be the authority. (Optional stretch: a single conditional edge that re-prompts once for fields flagged `conflicting` to generate a clarification question — only if time allows.)

### Comparison agent graph

The comparison agent is **comparability-first**: it must establish *who is even comparable* before producing any side-by-side, and it consumes **only the code-validated `ExtractionResult` objects** (never raw vendor text — that prevents it from re-hallucinating facts the extraction step already grounded).

```
        ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
START ─▶ │ comparability_gate │ ─▶  │ dimension_compare  │ ─▶  │ attention_points   │ ─▶ END
        │ (which vendors are │     │ (per dimension:    │     │ (clarification Qs, │
        │  comparable? what  │     │  tech/commercial/  │     │  buyer "look here  │
        │  blocks comparison)│     │  scope/timeline/   │     │  first" summary)   │
        └────────────────────┘     │  compliance/risk)  │     └────────────────────┘
              │                     └────────────────────┘            │
        emit "comparability"        emit per-dimension "row"    emit "attention" + "result"
```

**Node-by-node:**

1. **`comparability_gate`** — Inspect the set of `ExtractionResult`s. Determine, per dimension, whether vendors are comparable (e.g. all priced the same scope in the same currency?) or **not yet comparable** (bundled vs. itemized pricing, missing tax/currency, partial scope). Output an explicit `Comparability` object with reasons. This runs first and gates the framing of everything downstream — it never silently forces an apples-to-oranges comparison.

2. **`dimension_compare`** — For each dimension (technical, commercial, scope, timeline, compliance, risk), build a side-by-side row **grounded in the extracted facts + their evidence**. Where a vendor's field was flagged `missing`/`unclear`/`unsupported` by extraction, the comparison cell shows that flag — it does **not** invent a value to fill the grid. Numbers in the comparison must trace back to a grounded `ExtractedField`.

3. **`attention_points`** — Produce the buyer-first layer: top risks, top gaps, and **clarification questions** the buyer should send each vendor. This is the "what should the buyer see first" output that the 15%-weighted product-thinking rubric rewards.

**Why comparison consumes structured extraction, not raw text:** Re-reading raw vendor text in the comparison step would reopen the hallucination surface that extraction+grounding just closed. By making `ExtractionResult[]` the *only* input, every comparison claim is transitively grounded. This is the single most important boundary in the pipeline.

---

## Structured Output Flow (pydantic + OpenAI JSON Schema)

```
pydantic schema (schemas/extraction.py)
        │  .model_json_schema()
        ▼
LangChain ChatOpenAI(...).with_structured_output(ExtractionResult)
        │  OpenAI structured-output / JSON-schema (strict) path
        ▼
model returns JSON conforming to schema  ──▶  pydantic VALIDATES on parse
        │  (validation error => surfaced, not silently dropped)
        ▼
ExtractionResult instance threaded through the graph state
        │  grounding node mutates flags/values (still a validated model)
        ▼
api/ serializes via .model_dump()  ──▶  SSE payload  ──▶  web consumes typed object
```

- **Bind the schema, don't parse free text.** Use `ChatOpenAI(model=..., ...).with_structured_output(Model)` so OpenAI's strict JSON-schema path enforces shape at generation time, and pydantic validates on receipt. Extraction and comparison return **validated objects, not prose** (`CLAUDE.md §5`).
- **One pydantic model = OpenAI schema AND TS type.** `ExtractionResult.model_json_schema()` is the same artifact that (a) constrains the model and (b) generates the TS mirror. This is why "schemas are the contract" holds end-to-end.
- **Keep the model tier per node:** GPT-5.4 for `extract` and all `comparison` nodes (reasoning-heavy); GPT-5.4-mini is acceptable for `clarification`-style short rewrites. Never GPT-5.5. Model IDs are env-configured — confirm exact strings before hardcoding.

---

## Code-Enforced Grounding / Evidence-Span Validation (CRITICAL)

This is the rubric's headline reliability mechanism and the most important code in the repo. **It must be pure code with zero LLM involvement.**

### Contract

```python
# grounding/verify.py  (design, not final code)

@dataclass
class GroundingResult:
    verified: bool
    method: Literal["exact", "fuzzy", "none"]
    score: float            # 1.0 for exact, fuzzy ratio otherwise
    matched_offset: int | None   # where in source it was found (for UI highlight)

def verify_evidence(snippet: str, source: str, *, threshold: float = 0.90) -> GroundingResult:
    """
    Is `snippet` actually present in `source`?
    1. Normalize both (collapse whitespace, unify quotes/dashes, casefold).
    2. Exact substring? -> verified, method="exact", score=1.0.
    3. Else best fuzzy window (rapidfuzz partial_ratio) >= threshold?
       -> verified, method="fuzzy".
    4. Else -> verified=False.  NEVER trust the model's claim.
    """
```

### Enforcement rule (the part that wins the rubric)

In the `ground` node, after extraction:

```
for field in extraction.fields:
    g = verify_evidence(field.evidence.snippet, source_text)
    field.evidence.grounding = g
    if not g.verified:
        field.flag = "unsupported"     # CODE overrides the model
        field.value = None             # value is suppressed from the "fact" view
```

- **The model never sets the final trust state.** The model proposes a snippet + a flag; **code disposes.** If the snippet isn't provably in the source, the field becomes `unsupported` and its value is withheld from the fact view — exactly mirroring `CLAUDE.md §8` and the `PROJECT.md` core-value statement.
- **Normalization is essential and bounded.** Whitespace/quote/dash/case normalization handles real LLM copy drift (smart quotes, collapsed newlines from PDF extraction) without opening a loophole. Fuzzy matching at a *high* threshold (≈0.90) tolerates minor reflow but rejects fabrication. Keep normalization aligned between `segment` (offsets) and `verify` so matched offsets map back to the original for UI highlighting.
- **Tested as a unit (`tests/test_grounding.py`).** Minimum two cases the rubric cares about: (1) a real verbatim snippet passes; (2) a fabricated/hallucinated snippet is downgraded to `unsupported` and its value suppressed. This test *is* the proof of the reliability claim.
- **No DB, no embeddings, no vector store needed.** Grounding is string matching against the source text we already hold in memory. Resist the urge to add a vector store — `PROJECT.md` explicitly scopes it out.

---

## SSE Streaming Design (FastAPI → Next.js)

### Event envelope (the contract for the stream)

Every event on every stream uses one shape (`CLAUDE.md §11`, `PROJECT.md`):

```
data: {"type": "<event-type>", "payload": { ... }}\n\n
```

`type` values are a small fixed vocabulary, mirrored to TS as a union:

| `type` | When | `payload` |
|--------|------|-----------|
| `stage` | A graph node starts/finishes | `{ node: "extract", status: "start"\|"done" }` |
| `token` | LLM token delta (optional, nice for demo) | `{ text: "..." }` |
| `evidence` | A field's grounding result | `{ field, verified, method, flag }` |
| `result` | Final validated object | the full `ExtractionResult` / `ComparisonResult` |
| `error` | Something failed | `{ message, where }` |
| `done` | Stream complete | `{}` |

### FastAPI side

```python
# api/sse.py
def sse_event(type: str, payload: dict) -> str:
    return f"data: {json.dumps({'type': type, 'payload': payload})}\n\n"

# api/routers/extract.py  (design)
@router.post("/extract")
async def extract(req: ExtractRequest):
    async def gen():
        graph = build_extraction_graph()
        async for mode, chunk in graph.astream(
            {"source": req.text, "rfq": req.rfq},
            stream_mode=["updates", "messages", "custom"],
        ):
            # map LangGraph stream chunks -> {type,payload} envelope
            ...
            yield sse_event("stage", {...})
        yield sse_event("done", {})
    return StreamingResponse(gen(), media_type="text/event-stream")
```

- **Use LangGraph's native streaming, then re-shape.** Compiled graphs expose `.astream(..., stream_mode=[...])`: `"updates"` gives per-node output (→ `stage`/`result` events), `"messages"` gives LLM token deltas (→ `token`), `"custom"` lets a node emit grounding results (→ `evidence`). The router's only job is to translate those chunks into the `{type,payload}` envelope. **Never buffer-and-return** (`CLAUDE.md §15`).
- **FastAPI ≥0.122 ships a native `EventSourceResponse`** (`fastapi.sse`) that works over POST and handles SSE encoding. Either it or a plain `StreamingResponse(media_type="text/event-stream")` is fine; confirm the installed FastAPI version before choosing — pin it in `pyproject.toml`. POST is preferred over GET because vendor text bodies are large.
- **CORS must allow the Vercel origin.** Add `CORSMiddleware` with the web app's origin; SSE is cross-origin in prod (web on Vercel, AI on Render/Railway). Disable proxy buffering if Render/Railway interpose one (`X-Accel-Buffering: no` header) so events flush in real time.

### Next.js side

```typescript
// web/lib/sse.ts  (design)
export async function openStream(
  url: string, body: unknown, onEvent: (e: SSEEvent) => void
) {
  const res = await fetch(url, { method: "POST", body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" } });
  const reader = res.body!.getReader();
  // parse "data: {...}\n\n" frames, JSON.parse payload, dispatch onEvent
}
```

- **`fetch` + `ReadableStream`, not the `EventSource` browser API**, because the native `EventSource` only does GET and can't send a request body. Vendor text needs a POST body, so consume the stream manually. `SSEEvent` is imported from `@aerchain/shared-types`.

---

## The pydantic → shared-types Contract

### Direction of truth

```
services/ai/schemas/*.py  (pydantic — SOURCE OF TRUTH)
        │  scripts/export_schema.py
        │    model.model_json_schema()  ->  JSON Schema
        │    json-schema-to-typescript   ->  .ts
        ▼
packages/shared-types/src/index.ts  (GENERATED — do not hand-edit)
        │  imported as @aerchain/shared-types
        ▼
apps/web  (typed components consume ExtractionResult, ComparisonResult, SSEEvent, RFQ ...)
```

- **Pydantic is canonical; TS is generated.** A small script (`scripts/export_schema.py`) dumps each model's JSON Schema and runs `json-schema-to-typescript` (or `datamodel-codegen` in reverse / `quicktype`) to produce `packages/shared-types/src/index.ts`. Mark the file generated; never hand-edit.
- **Wire it into the workflow, not just the README.** Add a `pnpm`/`turbo` task (e.g. `gen:types`) that runs the export. Run it whenever a schema changes; ideally a pre-commit or a `turbo` pipeline step so drift can't ship. This operationalizes `CLAUDE.md §15`'s "change one → change both."
- **Change protocol (from `CLAUDE.md §2`/`§15`):** change a schema → regenerate types → **list every affected screen and agent** and confirm each still works. The contract is the one place where UI/AI silently drift if discipline lapses.
- **For a 5-day prototype, generation > runtime validation on the TS side.** Don't build a TS-side runtime validator; the pydantic layer already validated the data before it left Python. The TS types are for editor safety and to keep the screens honest about flag states (`missing`/`unclear`/`conflicting`/`unsupported`).

---

## Data Flow

### End-to-end buyer flow

```
[Buyer: Generate RFQ]
   POST /rfq/generate  ──SSE──▶  rfq_gen graph  ──▶  RFQ (pydantic)  ──▶  RFQ Overview screen

[Buyer: provide vendor responses]  (paste or upload PDF/Word/Excel/PPT → best-effort text)
   POST /extract {text, rfq}  ──SSE──▶  extraction graph
        segment → extract(LLM) → GROUND(code) → finalize
   ──▶  ExtractionResult (only code-verified facts shown)  ──▶  Extraction Review screen
        (evidence snippets, missing/unclear/conflicting/unsupported flags)

[Buyer: compare]
   POST /compare {extractions: ExtractionResult[]}  ──SSE──▶  comparison graph
        comparability_gate → dimension_compare → attention_points
   ──▶  ComparisonResult  ──▶  Vendor Comparison screen
        (who is comparable, where they differ, clarification questions)

[Buyer: inspect prompts]
   GET /prompts , GET /traces  ──▶  Prompt Trace screen  (NOT streamed — static fetch)
```

### Key data flows

1. **Source text is carried alongside extraction** so the Extraction Review screen can highlight the evidence span (the `matched_offset` from grounding). The web app never re-derives facts; it only renders what the validated `ExtractionResult` contains.
2. **Comparison input is `ExtractionResult[]`, never raw text** — the grounding boundary established in extraction is preserved transitively into comparison.
3. **Streams are progress + final-object**, not buffered. Screens can show node-by-node progress (`stage`), live tokens (`token`), per-field verification (`evidence`), then render the final `result`.

---

## Architectural Patterns

### Pattern 1: LLM-proposes / code-disposes grounding gate

**What:** The model proposes facts + evidence snippets + tentative flags; a pure-code node verifies each snippet against the source and has final authority over the flag and whether the value is shown.
**When to use:** Any time hallucination control is graded/critical — exactly this assignment.
**Trade-offs:** Slightly more code than trusting the model; vastly more defensible. The high-threshold fuzzy match must be tuned so PDF-extraction reflow doesn't cause false downgrades.

### Pattern 2: Comparability gate before comparison

**What:** A first node decides *whether* vendors can be compared per dimension and surfaces "not yet comparable" with reasons, before any side-by-side is built.
**When to use:** Comparing heterogeneous inputs where a naive grid would mislead (bundled vs. itemized pricing, partial scope).
**Trade-offs:** The buyer sometimes sees "can't compare yet" instead of a tidy table — which is the *correct*, rubric-rewarded behavior (avoid misleading comparisons, `assignment §24`).

### Pattern 3: Graph-internal state ≠ API contract

**What:** The `TypedDict` threaded between LangGraph nodes is separate from the pydantic models that cross the HTTP boundary; a `finalize` node assembles the contract object.
**When to use:** Always, when a graph's working state is richer/messier than what the client should see.
**Trade-offs:** A small mapping step at the end; buys decoupling of UI from orchestration internals.

### Pattern 4: One envelope, one emitter, one consumer

**What:** A single `{type, payload}` SSE shape, one `sse_event()` helper server-side, one `openStream()` consumer client-side, shared `SSEEvent` type.
**When to use:** Multiple streaming endpoints feeding multiple screens (here: extract + compare + generate).
**Trade-offs:** Slight upfront abstraction; eliminates per-route event-format drift.

---

## Anti-Patterns

### Anti-Pattern 1: Asking the model to certify its own grounding

**What people do:** Add a `"grounded": true` field to the schema and trust it.
**Why it's wrong:** An LLM will happily emit `true` for fabricated facts (`CLAUDE.md §2`).
**Do this instead:** Verify the evidence span in code; let code set the flag.

### Anti-Pattern 2: Feeding raw vendor text into the comparison agent

**What people do:** Re-read the proposals during comparison "for richer context."
**Why it's wrong:** Reopens the hallucination surface extraction already closed; comparison claims become ungrounded.
**Do this instead:** Comparison consumes only `ExtractionResult[]`.

### Anti-Pattern 3: Buffer-and-return long agent runs

**What people do:** `await graph.ainvoke(...)` then return one big JSON.
**Why it's wrong:** Bad demo UX, looks like a hang, violates `CLAUDE.md §15`.
**Do this instead:** Stream `stage`/`token`/`evidence`/`result` over SSE.

### Anti-Pattern 4: Hand-editing `packages/shared-types`

**What people do:** Tweak the TS type directly when the UI needs a field.
**Why it's wrong:** Silent drift from the pydantic source of truth.
**Do this instead:** Change the pydantic schema, regenerate, list affected screens/agents.

### Anti-Pattern 5: Normalizing messy vendor data away

**What people do:** Coerce all pricing into one canonical structure to make the grid clean.
**Why it's wrong:** `assignment §24` explicitly warns against heavy normalization; the *differences* are the product.
**Do this instead:** Surface differences and flag non-comparability; normalize only enough to match evidence spans.

---

## Build Order / Component Dependencies

The dependency chain forces a clear order. **Schema/contract first, grounding early, UI last** — because everything downstream is typed by the schemas, and the comparison agent literally cannot exist before extraction produces its input.

```
1. schemas/  (pydantic source of truth)            ── nothing works without the contract
        │
2. shared-types export pipeline + llm/ client       ── lock contract direction + model access early
        │
3. grounding/ (pure code) + tests                    ── independent of LLM; build & unit-test in isolation
        │
4. prompts/ registry + extraction & vendor_gen prompts  (highest-weighted artifact, in parallel with 3)
        │
5. extraction agent graph  (segment→extract→ground→finalize)  ── needs schemas(1)+grounding(3)+prompts(4)
        │
6. api/ SSE plumbing  (sse.py + /extract route)      ── needs a graph(5) to stream
        │
7. comparison agent graph + /compare route           ── needs ExtractionResult[](5) as input; STRICT order
        │
8. rfq_gen / vendor_gen agents + their routes         ── needed for sample data + RFQ Overview screen
        │
9. apps/web screens + sse.ts consumer                 ── needs shared-types(2) + live SSE routes(6,7,8)
```

**Hard ordering constraints (the ones a roadmap must respect):**

- **Schemas before everything.** They drive OpenAI structured output, the TS contract, and every agent's I/O. (Phase 1.)
- **Grounding before extraction's `ground` node is meaningful** — but grounding is LLM-free, so it can be built and fully tested *before* any agent works. Front-load it. (Early phase, parallelizable with prompts.)
- **Extraction before comparison — non-negotiable.** Comparison consumes `ExtractionResult[]`; it cannot be built or tested without extraction output.
- **SSE plumbing needs at least one working graph** to have something to stream; don't build the SSE layer in a vacuum.
- **UI last.** It's a thin client (10% of grade); it needs the contract types and live streaming endpoints to be real, not mocked. Build it against working routes so the demo is dynamic, not hardcoded (`assignment §24`).
- **`rfq_gen`/`vendor_gen` can slot in parallel** with extraction once schemas exist, since they also need sample data committed (`PROJECT.md` decision: commit samples AND support live generation).

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI (GPT-5.4 / 5.4-mini) | LangChain `ChatOpenAI(...).with_structured_output(Model)`; SSE token streaming via graph `stream_mode="messages"` | Env-configured model IDs; never GPT-5.5; tier per node |
| File text extraction | Best-effort in `segment` (or a small util): PDF/Word/Excel/PPT → text | No production OCR (`assignment §11`, `PROJECT.md` out-of-scope); keep offsets for grounding |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| web ↔ ai service | HTTP POST + SSE (`text/event-stream`, `{type,payload}`) | CORS for Vercel↔Render origin; disable proxy buffering |
| api ↔ agents | Direct python call; route owns SSE re-shaping of `graph.astream` | Routers stay thin; no business logic in routers |
| agents ↔ grounding | Direct python call from the `ground` node | Pure code; the trust boundary — no LLM here |
| agents/api ↔ schemas | Import pydantic models | Leaf dependency; nothing in schemas imports agents |
| schemas ↔ shared-types | Build-time generation (JSON Schema → TS) | One-directional; TS is generated, never hand-edited |
| extraction ↔ comparison | `ExtractionResult[]` passed as comparison input | Comparison never touches raw vendor text |

---

## Sources

- LangGraph docs — `StateGraph(TypedDict)`, node functions, `.astream(stream_mode=...)`, pydantic output mapping in streaming (Context7 `/langchain-ai/langgraph`). Confidence: HIGH.
- FastAPI docs — `StreamingResponse(media_type="text/event-stream")`, native `EventSourceResponse`/`ServerSentEvent` (FastAPI ≥0.122, works over POST), `CORSMiddleware` (Context7 `/fastapi/fastapi`). Confidence: HIGH.
- Project sources of truth: `CLAUDE.md` (§5 architecture, §8 reliability, §11 testing, §15 gotchas), `docs/assignment.md` (§11–§13, §17, §24), `.planning/PROJECT.md`. Confidence: HIGH.
- Fuzzy span matching (`rapidfuzz partial_ratio`) for evidence verification — standard library pattern; threshold tuning is a project decision, not a verified external claim. Confidence: MEDIUM.

---
*Architecture research for: prompt-driven procurement extraction & comparison AI prototype*
*Researched: 2026-06-27*
