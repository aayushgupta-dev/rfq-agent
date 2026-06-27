# Phase 3: Extraction Agent — Research

**Researched:** 2026-06-27
**Domain:** LangGraph structured-output extraction + grounding gate integration + SSE streaming
**Confidence:** HIGH (all critical questions resolved against codebase + Context7 + official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01** RFQ-aware hybrid extraction: per-line-item `Field[T]` (pricing + scope-coverage) + document-level cross-cutting categories. Missing line-item bids surface as `missing` at extraction time.
- **D-02** Bundled/cross-item pricing: document-level `pricing_structure` Field + per-item `unclear`; never force a per-item split.
- **D-03** Per-claim grounding: multi-claim categories are `list[Field[T]]`; narrative categories are single `Field[str]`.
- **D-04** No `dict[str, Field]` shapes — only `list[BaseModel]` / `list[Field]` (closes IN-04 walker gap by design).
- **D-05** `vendor_name` is plain `str` (provenance metadata), NOT a grounded `Field`.
- **D-06** Single structured-output call per vendor; sectioned 2-call only if truncation is observed (YAGNI).
- **D-07** Grounding runs server-side BEFORE SSE boundary; only grounded data crosses; progress via `status` events.
- **D-08** Truncation (`finish_reason: length`) → `error` `{code, message, recoverable: true}`; `refusal` → `error` `{recoverable: false}`; never parse either.
- **D-09** Humility-biased prompt posture; model uses only 4 states (`present | missing | unclear | conflicting`); `unsupported` is gate-only, prompt never mentions it.
- **D-10** Model supplies verbatim snippet + `source_id` only; gate computes offsets; lean model-facing schema mapped into canonical `ExtractionResult` during grounding.
- **D-11** Extraction only flags; no clarification question generation (Phase 4).
- **D-12** 3–5 traces, one per sample vendor, plus 1–2 showcasing a real `unsupported` downgrade.
- **D-13** Traces committed as JSON (source) + rendered Markdown under `docs/traces/`.
- **D-14** Each trace captures: (1) input, (2) resolved prompt, (3) raw model output, (4) grounding step + downgrade report, (5) final grounded `ExtractionResult`.
- **D-15** ≥1 trace MUST show a genuine downgrade from real runs on committed messy samples.

### Claude's Discretion

- Exact `ExtractionResult` / `LineItemExtraction` field names and the model-facing → canonical schema mapping (within D-01..D-05 + D-04 no-dict constraint).
- The extraction `StateGraph` node structure and function signatures.
- Whether a stated grand `total_price` is its own doc-level grounded `Field[Decimal]`.
- Prompt few-shot example selection and exactly how RFQ line items are injected.
- Code-level test structure.

### Deferred Ideas (OUT OF SCOPE)

- Sectioned multi-call extraction — contingency only if truncation is observed.
- Clarification question generation — Phase 4.
- `not-comparable` representation — Phase 4.
- Extraction Review screen / in-app trace viewer / file upload — Phase 5.
- Streaming token-level partial fields — rejected on reliability grounds (D-07).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXTRACT-01 | Extraction agent produces structured per-vendor object covering scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, and risks. | Schema design (§Standard Stack), D-01..D-05 field mapping, model-facing + canonical schema split. |
| EXTRACT-02 | Every extracted fact carries an evidence snippet drawn from the vendor's response. | `Field[T]` envelope enforces evidence at model-validator level; gate verifies it; verbatim-snippet prompt instruction (D-10). |
| EXTRACT-03 | Missing / unclear / conflicting / unsupported flagged explicitly; agent never fills missing information. | Humility-biased prompt (D-09), `FlagStatus` enum, model-validator rules in envelope.py. |
| EXTRACT-05 | Structured output under strict mode treats `finish_reason: length` and `refusal` as hard errors, never parsed. | Detection via `include_raw=True` + `response_metadata["finish_reason"]` / `additional_kwargs["refusal"]` — see Integration Points section. |
| PROMPT-03 | ≥1 complete prompt trace captured and reproducible. | D-12..D-15 trace spec; 3–5 JSON + Markdown traces under `docs/traces/`. |
</phase_requirements>

---

## Summary

Phase 3 builds the first real LangGraph `StateGraph` in this codebase. It reads a
`VendorResponse.raw_text` + the RFQ's 8 line items, calls `gpt-5.4` with strict structured output,
runs `ground_model()` on the result, and streams five event types over SSE before the grounded
`ExtractionResult` reaches any client.

The codebase is 100% ready to plug into. All primitives — `Field[T]`, `FlagStatus`,
`ground_model()`, `DowngradeReport`, `EventEnvelope`, `get_stream_writer()`,
`EventSourceResponse`, `get_llm("reasoning").with_structured_output(...)`, `load("extraction")` —
are implemented and tested. Phase 3 wires them together in a graph, authors the full extraction
prompt, and commits 3–5 traces proving the reliability contract.

The two highest-novelty questions the roadmap flagged are now resolved:

1. **Truncation/refusal detection through LangChain's `.with_structured_output()`**: use
   `include_raw=True` to get the raw `AIMessage`; inspect
   `response_metadata["finish_reason"]` for `"length"` and `additional_kwargs.get("refusal")`
   for model refusals. **Do NOT use `include_raw` as the structured result** — it wraps output in
   `{"raw", "parsed", "parsing_error"}` and `LengthFinishReasonError` propagates uncaught through
   this wrapper (confirmed bug, Issue #29700). The correct pattern is a `try/except
   openai.LengthFinishReasonError` around the `.invoke()` call plus a check of
   `response_metadata["finish_reason"]` on the raw response.
2. **LangGraph `stream_mode="custom"` → SSE**: confirmed working and already proven by `_demo.py`.
   `get_stream_writer()` inside any node emits dicts directly; `astream({}, stream_mode="custom")`
   yields them as chunks; each chunk is validated through `EventEnvelope(**chunk)` before
   serialization. The async path in `app.py` is the exact pattern to follow.

**Primary recommendation:** Follow `_demo.py` + `app.py` exactly for the graph/SSE spine; layer
in a `try/except` around the model call to catch `LengthFinishReasonError`; inspect
`response_metadata` for the `"length"` finish reason as the secondary detection path.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Structured fact extraction from vendor text | API / Backend (extraction agent) | — | LLM call, schema validation, and grounding are all server-side (D-07) |
| Evidence grounding / offset recomputation | API / Backend (gate.py) | — | Code-enforced, LLM-free; runs before any data crosses the SSE boundary |
| Flag state assignment (`present/missing/unclear/conflicting`) | API / Backend (prompt + pydantic envelope) | — | Model assigns 4 states; `model_validator` enforces semantics in code |
| `unsupported` downgrade | API / Backend (gate.py only) | — | Gate-only verdict; never the model's word (CLAUDE.md §2/§8) |
| SSE event serialization | API / Backend (FastAPI route) | — | `EventSourceResponse` + `EventEnvelope` validation before yield |
| Trace capture (JSON + Markdown) | API / Backend (extraction agent) | `docs/traces/` (file) | Agent collects raw + grounded diff; traces written to filesystem |
| Shared-types contract sync | Backend (codegen script) | Frontend (shared-types/) | Any schema change triggers pydantic2ts regeneration (PLAT-02) |

---

## Standard Stack

### Core (already installed — no new deps needed for Phase 3)

| Library | Version (installed) | Purpose | Why Standard |
|---------|---------------------|---------|--------------|
| `langchain-openai` | `>=1.3.3` | `init_chat_model`, `with_structured_output` | Project-standard LLM client (factory.py) |
| `langgraph` | `>=1.2.6` | `StateGraph`, `get_stream_writer`, `astream` | Project-standard graph orchestration |
| `langchain-core` | (via langchain) | `ChatPromptTemplate` | Prompt assembly pattern (rfq_gen.py) |
| `fastapi` + `sse-starlette` | `>=0.138.1` / `>=3.4.5` | SSE route via `EventSourceResponse` | Project-standard (app.py) |
| `pydantic` | `>=2.13.4` | Schema definition, `model_copy`, `model_fields` | Contract source of truth |
| `rapidfuzz` | `>=3.14.5` | Fuzzy snippet matching in gate.py | Already installed, calibrated to FUZZY_THRESHOLD=90.0 |
| `openai` | `>=2.44.0` | `LengthFinishReasonError` exception type | Installed as transitive dep; needed for except-clause |

**No new packages required for Phase 3.** [VERIFIED: codebase pyproject.toml]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-frontmatter` | `>=1.3.0` | `load("extraction")` prompt loading | Extraction prompt authoring via registry.py |
| `pytest` | `>=9.1.1` | Unit tests | test_extraction_agent.py |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `try/except LengthFinishReasonError` | `include_raw=True` dict path | `include_raw` wraps result in `{raw, parsed, parsing_error}` dict and does NOT catch `LengthFinishReasonError` (confirmed bug #29700) — direct except is simpler and correct |
| Single-call extraction (D-06) | Sectioned 2-call | Sectioned adds complexity + requires merging; only build if truncation is observed in testing |

**Installation:** None — all dependencies already present in `pyproject.toml`.

---

## Package Legitimacy Audit

> No new packages are introduced in Phase 3. All dependencies are already installed and were audited in prior phases. This section is N/A.

**Packages removed:** none
**Packages flagged:** none

---

## Architecture Patterns

### System Architecture Diagram

```
VendorResponse.raw_text + RFQ.line_items
         │
         ▼
POST /extract/vendor   ← FastAPI SSE route (app.py pattern)
         │
         ▼
extraction_graph.astream({}, stream_mode="custom")
         │
    ┌────┴─────────────────────────────────┐
    │  Node: prepare                        │
    │  Build model-facing prompt context    │
    │  w({"type":"status", ...})            │  ──► SSE: status
    └────┬─────────────────────────────────┘
         │
    ┌────┴─────────────────────────────────┐
    │  Node: call_model                     │
    │  get_llm("reasoning")                 │
    │    .with_structured_output(           │
    │       ExtractionModelOutput,          │  (model-facing schema, lean)
    │       method="json_schema")           │
    │  try/except LengthFinishReasonError   │  ──► SSE: error {recoverable:true}
    │  check refusal in additional_kwargs   │  ──► SSE: error {recoverable:false}
    │  w({"type":"status", ...})            │  ──► SSE: status
    └────┬─────────────────────────────────┘
         │  raw ExtractionModelOutput (model-facing)
         ▼
    ┌────┴─────────────────────────────────┐
    │  Node: ground                         │
    │  map model-facing → ExtractionResult  │
    │  ground_model(result,                 │
    │    {vendor.source_id: vendor.raw_text})│
    │  → (grounded_result, DowngradeReport) │
    │  w({"type":"status", ...})            │  ──► SSE: status
    └────┬─────────────────────────────────┘
         │  grounded ExtractionResult + DowngradeReport
         ▼
    ┌────┴─────────────────────────────────┐
    │  Node: emit_result                    │
    │  Capture trace (raw vs grounded diff) │
    │  w({"type":"result", "payload": {     │
    │     "extraction": grounded.dict(),    │
    │     "downgrade_report": report.dict()}│  ──► SSE: result
    │  })                                   │
    └──────────────────────────────────────┘
         │
         ▼  [graph END]
    route appends:  {"type":"done","payload":{}}  ──► SSE: done
```

### Recommended Project Structure

```
services/ai/
├─ agents/
│  ├─ _demo.py          # existing — SSE/graph pattern to follow
│  ├─ rfq_gen.py        # existing — prompt-load pattern to follow
│  ├─ vendor_gen.py     # existing
│  └─ extraction.py     # NEW — StateGraph + generate_extraction()
├─ schemas/
│  └─ domain.py         # MODIFY — flesh out ExtractionResult (D-01..D-05)
├─ prompts/
│  └─ extraction.v1.md  # MODIFY — author full prompt from TODO stub
├─ api/
│  └─ app.py            # MODIFY — add POST /extract/vendor SSE route
├─ tests/
│  └─ test_extraction_agent.py  # NEW
docs/
└─ traces/              # NEW dir — 3-5 JSON + Markdown traces (D-12..D-15)
```

### Pattern 1: LangGraph Node with SSE Custom Events (confirmed from _demo.py + Context7)

**What:** A node calls `get_stream_writer()` and emits `{type, payload}` dicts; the route
uses `astream(stream_mode="custom")` and validates each chunk through `EventEnvelope`.

**When to use:** Every agent in this codebase that streams progress events.

```python
# Source: services/ai/agents/_demo.py (confirmed working) + Context7
from langgraph.config import get_stream_writer

def extraction_node(state: dict) -> dict:
    w = get_stream_writer()
    w({"type": "status", "payload": {"message": "calling model", "phase": "model"}})
    # ... model call ...
    w({"type": "status", "payload": {"message": "grounding", "phase": "grounding"}})
    # ... ground_model() ...
    w({"type": "result", "payload": {"extraction": ..., "downgrade_report": ...}})
    return {}

# Route (follows app.py pattern):
async def _generate():
    async for chunk in extraction_graph.astream(inputs, stream_mode="custom"):
        yield {"data": EventEnvelope(**chunk).model_dump_json()}
    yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}
return EventSourceResponse(_generate())
```

[VERIFIED: codebase _demo.py + app.py]

### Pattern 2: Truncation and Refusal Detection (EXTRACT-05 — highest-novelty)

**What:** Catching `finish_reason: length` and `refusal` through LangChain's
`with_structured_output`. Two detection paths are needed because the behaviors differ.

**Critical finding:** `LengthFinishReasonError` is raised by the OpenAI Python client (not by
LangChain's parser) when `finish_reason == "length"` on a structured-output call. It propagates
UNCAUGHT through `with_structured_output(include_raw=True)` — the `include_raw` wrapper does not
trap it (confirmed bug langchain-ai/langchain#29700). The correct pattern is a bare
`try/except openai.LengthFinishReasonError`. [CITED: github.com/langchain-ai/langchain/issues/29700]

Refusals surface differently: the model returns `finish_reason: "stop"` but the message carries
a `refusal` field (non-None string) in `additional_kwargs`. When using a Pydantic schema with
`method="json_schema"`, this surfaces correctly. [CITED: github.com/langchain-ai/langchain/issues/25510]

```python
# Source: pattern derived from langchain-ai/langchain#29700 + #25510 + OpenAI docs
from openai import LengthFinishReasonError

llm = get_llm("reasoning").with_structured_output(
    ExtractionModelOutput, method="json_schema"
)

try:
    raw_result = llm.invoke(messages)
    # Check for refusal (present when model declines for safety reasons)
    # raw_result is an ExtractionModelOutput pydantic instance on success
except LengthFinishReasonError:
    # finish_reason == "length": JSON truncated, do NOT attempt to parse
    # Emit error event: {code: "truncation", message: "...", recoverable: True}
    # If D-06 fallback exists: auto-retry with sectioned call (researched contingency)
    raise  # re-raise to let the node handle it

# Refusal detection path (when using with_structured_output + Pydantic schema):
# LangChain raises an exception or returns a wrapped result containing a refusal field.
# With method="json_schema" + Pydantic, a refused response raises or returns None parsed.
# The safest detection: invoke with include_raw=True for the refusal check only,
# inspect raw.additional_kwargs.get("refusal") before trusting the parsed value.
```

**Practical implementation for D-08:**

```python
# ponytail: two-path detection because truncation and refusal surface differently
# in the OpenAI/LangChain stack. Truncation raises; refusal silently populates a field.
try:
    result = chain.invoke(messages)
except LengthFinishReasonError:
    w({"type": "error", "payload": ErrorPayload(
        code="extraction_truncated",
        message="Model output was truncated (finish_reason=length). Schema may need sectioning.",
        recoverable=True,
    ).model_dump()})
    return {"error": "truncated"}

# Refusal: use include_raw to inspect additional_kwargs
# (refusal is only in additional_kwargs, not raised as an exception)
```

[CITED: github.com/langchain-ai/langchain/issues/29700]
[CITED: github.com/langchain-ai/langchain/issues/25510]
[CITED: platform.openai.com/docs/guides/structured-outputs]

### Pattern 3: Model-facing Schema → Canonical ExtractionResult Mapping (D-10)

**What:** The model produces a lean schema (snippet + source_id, no char offsets). After
`ground_model()` recomputes offsets and writes them into new `Evidence` objects, the canonical
`ExtractionResult` has fully-populated `Evidence` fields. The mapping happens inside the
`ground` node, not before.

**Key insight from gate.py:** `ground_model()` already creates new `Evidence` objects with
correct `char_start`/`char_end` from the source text search. The model-facing schema needs
only `snippet` + `source_id` per evidence item; the gate fills the rest. This means the
model-facing `Evidence`-equivalent can be a simpler internal schema.

**Implementation:** Define a `ModelEvidence` internal class with `snippet: str` and
`source_id: str` only; after grounding, the canonical `Evidence` objects carry real offsets.
Alternatively, let the model output canonical `Evidence` shape but with dummy offsets (the gate
overwrites them anyway per D-01 / gate.py D-01). Dummy offsets are acceptable since the
`Evidence.model_validator` only checks `char_start >= 0` and `char_end > char_start` — so
supply `char_start=0, char_end=1` as placeholders; the gate overwrites on hit. [VERIFIED: codebase
gate.py D-01, envelope.py model_validator]

The simpler approach is the placeholder offset approach: the model-facing schema IS the canonical
`ExtractionResult` schema with instructions to use `char_start=0, char_end=1` as placeholder offsets.
Gate replaces them. Eliminates a mapping step. [ASSUMED — tradeoff to confirm during implementation]

### Pattern 4: Walker Shape Coverage Verification (IN-04 carried concern)

**What:** `_walk_and_ground` in gate.py traverses `Field[T]`, `BaseModel`, and `list` (of either).
D-04 mandates no `dict[str, Field]` shapes in `ExtractionResult`, so the walker covers everything
by design.

**Verification mandate:** After `ExtractionResult` is finalized, the planner MUST include a
verification task that enumerates every field in the schema and asserts the walker hits it. A
cheap assert loop in the test does this. [VERIFIED: codebase gate.py lines 320-366]

Shapes the walker handles:
- Direct `Field[T]` attribute → `ground_field()` called
- Nested `BaseModel` → recursive `_walk_and_ground()`
- `list[Field[T]]` → each item grounded
- `list[BaseModel]` → each item recursively walked

Shapes the walker does NOT handle (per gate.py ponytail comment, line 364):
- `dict[str, Field[T]]` — NOT traversed. D-04 prevents this by forbidding dict-valued Field containers in the schema.

### Anti-Patterns to Avoid

- **Parsing a truncated response:** `LengthFinishReasonError` means the JSON is incomplete. Pydantic
  validation on a partial object will either fail (and raise a confusing error) or pass with
  silently default fields. Always raise an `error` event before attempting any parse.
- **Streaming ungrounded facts as `partial` events:** D-07 explicitly rejects this. No `partial`
  fact events — only `status` progress events and a final grounded `result`.
- **Trusting the model's `char_start`/`char_end` in the canonical schema:** gate.py's D-01 ignores
  and overwrites them. The implementation must not expose these model-supplied offsets to the UI
  before grounding.
- **Using `dict[str, Field[T]]` anywhere in `ExtractionResult`:** breaks the walker silently.
  D-04 is a hard constraint.
- **Adding `unsupported` to the prompt:** D-09. The model never decides `unsupported`; the gate does.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Evidence offset verification | Custom string search | `gate.py ground_model()` | Already implemented with NFKC normalization, fuzzy fallback, offset-map recomputation |
| SSE streaming | Custom async generator | `EventSourceResponse` + `_demo.py` pattern | Already proven end-to-end; EventEnvelope validates taxonomy |
| Prompt loading | Inline strings | `registry.load("extraction")` | Versioning, frontmatter, drift-check already implemented |
| Structured output | Manual JSON parsing | `get_llm("reasoning").with_structured_output(Schema, method="json_schema")` | Returns validated pydantic instance; enforces schema at API level |
| LLM tier selection | Hardcoded model ID | `get_llm("reasoning")` | Factory reads env vars, never-5.5 discipline enforced in one place |
| Downgrade reporting | Custom dict | `DowngradeReport` / `DowngradeEntry` | Already defined; consumed by tests; Phase 5 trace viewer expects this shape |

**Key insight:** Phase 3 is an integration phase — every reliability primitive exists. The work is
wiring, schema design, prompt authoring, and trace capture.

---

## Runtime State Inventory

> SKIPPED — Phase 3 is a new-feature phase (no rename/refactor/migration). No runtime state affected.

---

## Common Pitfalls

### Pitfall 1: `LengthFinishReasonError` Leaks Through `include_raw`

**What goes wrong:** Developer uses `include_raw=True` expecting to catch truncation in
`parsing_error` field. Instead, `LengthFinishReasonError` propagates uncaught and crashes the
request handler.

**Why it happens:** The `include_raw` wrapper only catches `OutputParserException`; the OpenAI SDK
raises `LengthFinishReasonError` before LangChain's parser runs. [CITED: langchain-ai/langchain#29700]

**How to avoid:** Wrap the `.invoke()` call in `try/except openai.LengthFinishReasonError` directly.

**Warning signs:** An unhandled 500 error from the extraction route where the error message
mentions `LengthFinishReasonError`.

### Pitfall 2: Refusal Detection Varies by Schema Type

**What goes wrong:** Refusal is detected when using a plain `dict` schema but not with a pydantic
schema (or vice versa). The `additional_kwargs["refusal"]` field may be missing.

**Why it happens:** LangChain's `with_structured_output` uses different internal parsers depending
on the schema type; refusal propagation is inconsistent. [CITED: langchain-ai/langchain#25510]

**How to avoid:** Always use a pydantic schema (not a plain dict) as the target for
`with_structured_output`. Validate the refusal detection path against a mocked refusal response
in tests.

**Warning signs:** A vendor response that should trigger a refusal instead raises a pydantic
`ValidationError` (empty/null parsed result failing envelope constraints).

### Pitfall 3: Walker Silently Skips Nested List Items That Are Not `BaseModel` or `Field[T]`

**What goes wrong:** A `list[str]` or `list[SomePlainType]` field in `ExtractionResult` passes
through the walker unchanged — correct behavior, but if a developer wraps a list element as a
`dict` containing `Field[T]` values, grounding is silently skipped.

**Why it happens:** The walker's list branch checks `isinstance(item, EnvelopeField)` then
`isinstance(item, BaseModel)`. A plain dict is neither. [VERIFIED: gate.py lines 346-360]

**How to avoid:** D-04: all multi-value structures use `list[BaseModel]` containing `Field[T]`
attributes, never `list[dict]` or `dict[str, Field[T]]`.

### Pitfall 4: `ExtractionResult` Schema Change Without Regenerating `shared-types`

**What goes wrong:** The TS types drift from the pydantic schema; the Phase 5 UI component fails
to compile or renders wrong shapes.

**Why it happens:** `pydantic2ts` codegen is a manual step; it's easy to forget after a schema edit.

**How to avoid:** The `test_codegen_drift.py` test catches this — run `uv run pytest
tests/test_codegen_drift.py -x` after every schema change. Plan must include a drift-check task
after ExtractionResult is finalized.

### Pitfall 5: `vendor_name: Field[str]` in the Current Stub

**What goes wrong:** The current `ExtractionResult` stub has `vendor_name: Field[str]` — this is
wrong per D-05 and will cause a grounding attempt on a known metadata field.

**Why it happens:** The stub was a placeholder; D-05 post-dates it.

**How to avoid:** The first task must change `vendor_name: Field[str]` → `vendor_name: str` in
domain.py. The stub is at line 133. [VERIFIED: codebase domain.py line 133]

### Pitfall 6: Short Evidence Snippets from the Model Triggering `MIN_SNIPPET_LEN` Downgrade

**What goes wrong:** The model quotes a very short verbatim phrase (e.g. "Q3" or "TBD") as
evidence. Gate's `MIN_SNIPPET_LEN=15` guard downgrades the field to `unsupported` even though the
snippet exists in the source.

**Why it happens:** Short snippets score near-100 via `partial_ratio` against any text, so the gate
rejects them as unreliably grounded. [VERIFIED: gate.py line 37, ponytail comment]

**How to avoid:** Prompt instruction must ask for evidence snippets of ≥3 words / ≥20 chars of
context. Include this in the extraction prompt's evidence-formatting instructions. The threshold
is exposed as `MIN_SNIPPET_LEN` in gate.py if calibration is needed.

### Pitfall 7: `stream_mode="custom"` chunks are the raw dicts, not wrapped in a `type` key at the LangGraph level

**What goes wrong:** Developer expects chunks from `astream(stream_mode="custom")` to be
`{"type": "custom", "data": {...}}` and tries to unwrap them.

**Why it happens:** Context7 shows that in some LangGraph versions, `stream_mode=["updates", "custom"]`
returns `{"type": "updates"|"custom", "data": {...}}` wrappers. But `stream_mode="custom"` alone
yields the raw dict the node passed to `w()` directly. [VERIFIED: codebase _demo.py — chunks are
used as `EventEnvelope(**chunk)` directly, no unwrapping]

**How to avoid:** Follow `_demo.py` exactly. The node emits `{"type": ..., "payload": ...}`;
`astream` yields that dict directly; `EventEnvelope(**chunk)` validates it. No unwrapping needed.

---

## Code Examples

### Extraction Graph Skeleton

```python
# Source: services/ai/agents/_demo.py (proven pattern) [VERIFIED: codebase]
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from grounding.gate import ground_model
from grounding.report import DowngradeReport
from llm.factory import get_llm
from schemas.events import ErrorPayload
from schemas.domain import ExtractionResult, VendorResponse, RFQ
from openai import LengthFinishReasonError

def _build_extraction_graph():
    builder = StateGraph(dict)
    builder.add_node("extract", _extraction_node)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", END)
    return builder.compile()

def _extraction_node(state: dict) -> dict:
    w = get_stream_writer()
    vendor: VendorResponse = state["vendor"]
    rfq: RFQ = state["rfq"]

    w({"type": "status", "payload": {"message": "calling model", "phase": "model"}})

    chain = _build_chain(rfq)  # prompt + llm
    try:
        raw = chain.invoke({"vendor_text": vendor.raw_text})
    except LengthFinishReasonError:
        w({"type": "error", "payload": ErrorPayload(
            code="extraction_truncated",
            message="Output truncated — schema may need sectioning.",
            recoverable=True,
        ).model_dump()})
        return {"error": "truncated"}

    # Refusal check (raw is pydantic instance on success, None on refusal path)
    # Additional_kwargs carries refusal string if model refused
    # ponytail: refusal surfaces via exception or ValidationError from the chain;
    # explicit check here is defensive for the case where LangChain swallows it.

    w({"type": "status", "payload": {"message": "grounding evidence", "phase": "grounding"}})
    grounded, report = ground_model(raw, {vendor.source_id: vendor.raw_text})

    w({"type": "result", "payload": {
        "extraction": grounded.model_dump(mode="json"),
        "downgrade_report": report.model_dump(mode="json"),
    }})
    return {"result": grounded, "report": report}

extraction_graph = _build_extraction_graph()
```

### SSE Route for Extraction

```python
# Source: services/ai/api/app.py pattern [VERIFIED: codebase]
from collections.abc import AsyncGenerator
from sse_starlette import EventSourceResponse
from schemas.events import EventEnvelope

@app.post("/extract/vendor")
async def extract_vendor(req: ExtractionRequest) -> EventSourceResponse:
    async def _generate() -> AsyncGenerator[dict, None]:
        async for chunk in extraction_graph.astream(
            {"vendor": req.vendor, "rfq": req.rfq},
            stream_mode="custom",
        ):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}
    return EventSourceResponse(_generate())
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON parsing of LLM output | `with_structured_output(Schema, method="json_schema")` | OpenAI structured outputs GA (2024) | Returns validated pydantic instance; schema enforced at API level |
| Buffered LLM responses | SSE streaming via `EventSourceResponse` + `astream` | LangGraph streaming APIs stabilized | Progress visible to buyer without waiting for full extraction |
| Trusting model-supplied evidence offsets | Gate recomputes offsets via source text search | Phase 2 | Code-enforced grounding; no fabricated position references |

**Deprecated/outdated:**
- `stream_mode="custom"` with `version="v2"` kwarg: Context7 examples show `version="v2"` in some
  forms but the demo.py in the codebase does NOT pass `version` and works fine. Follow the
  codebase, not the docs on this parameter.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Placeholder offset approach (`char_start=0, char_end=1`) in the model-facing schema is the simplest implementation of D-10 | Architecture Patterns §Pattern 3 | If `Evidence` validator tightens to require `char_end > 1`, or if grounding on dummy offsets causes confusion, a separate `ModelEvidence` inner schema is needed |
| A2 | `additional_kwargs.get("refusal")` correctly surfaces refusals when using a pydantic schema with `method="json_schema"` | Pattern 2, Pitfall 2 | LangChain bug #25510 is unresolved — if pydantic schema path also loses refusal, a different detection path (raw message inspection) is needed |
| A3 | `stream_mode="custom"` yields raw dicts (not `{type, data}` wrapped) when called without a version kwarg | Pattern 1, Pitfall 7 | If a LangGraph version upgrade changes this behavior, the `EventEnvelope(**chunk)` line in the route breaks with a key error |

---

## Open Questions (RESOLVED)

1. **Refusal detection reliability with pydantic schema** — *resolved in planning (Plan 03-01 + 03-03).*
   - What we know: With a dict schema, refusals are not in `additional_kwargs` (bug #25510). With pydantic schema, it reportedly works.
   - What's unclear: Whether langchain-openai `>=1.3.3` (the installed version) has backported a fix.
   - Recommendation: Add a targeted unit test that mocks a refused response and verifies the detection path. If it fails, fall back to `include_raw=True` for refusal inspection + `try/except` for truncation.
   - **Resolution:** Plan 03-01 Task 1 adds a `test_refusal_raises_error_event` RED stub (mocks a refused response, asserts an `error` event `{recoverable: false}` and that no `ExtractionResult` is parsed). Plan 03-03 Task 1 implements detection via `additional_kwargs.get("refusal")` on the raw message (`include_raw=True` for the refusal-check path) — NOT keyed off `str(ValidationError)` — and turns that stub GREEN. The mock test pins the behavior regardless of whether the installed langchain-openai backported a fix.

2. **Truncation risk for the single-call schema** — *resolved as a runtime contingency (D-06; Plan 03-03 + 03-04).*
   - What we know: 8 line items × (pricing + scope coverage + evidence) + 6 doc-level categories, each as `Field[T]` with evidence, is the schema. Vendor fixture sizes are 13–27KB of raw text.
   - What's unclear: Whether gpt-5.4's output token limit will be hit in practice with a verbosity-moderate extraction prompt.
   - Recommendation: Run the extraction on all 3 committed vendor fixtures before finalizing the single-call approach. If any fixture triggers `LengthFinishReasonError`, implement the D-06 sectioned fallback at that point.
   - **Resolution:** Single-call is planned first (D-06, YAGNI). Plan 03-03 Task 1 wraps the model call in `try/except openai.LengthFinishReasonError` → `error` event `{recoverable: true}`, never parsing truncated output (`test_truncation_raises_error_event`). Plan 03-04 Task 2 captures traces on all 3 committed fixtures — the empirical check the recommendation calls for. The D-06 sectioned 2-call split stays a researched contingency, built only if a fixture actually triggers truncation during that run.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | `services/ai` | ✓ | 3.12 | — |
| OpenAI API key + gpt-5.4 access | Model calls | ✓ | verified Phase 1 | — |
| `langgraph>=1.2.6` | StateGraph, stream_writer | ✓ | pinned pyproject.toml | — |
| `langchain-openai>=1.3.3` | `with_structured_output` | ✓ | pinned pyproject.toml | — |
| `rapidfuzz>=3.14.5` | gate.py grounding | ✓ | pinned pyproject.toml | — |
| `data/vendor_*.json` | Trace capture (D-12..D-15) | ✓ | 3 committed fixtures | — |
| `pytest>=9.1.1` | Test suite | ✓ | dev dep | — |

**Missing dependencies with no fallback:** none.

---

## Validation Architecture

> `nyquist_validation` is `true` in config.json — section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 |
| Config file | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_extraction_agent.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXTRACT-01 | `ExtractionResult` covers all 8 categories; `vendor_name` is plain `str` | unit | `uv run pytest tests/test_extraction_agent.py::test_schema_shape -x` | ❌ Wave 0 |
| EXTRACT-02 | Every `present`/`unclear` field has non-empty evidence; evidence passes grounding | unit | `uv run pytest tests/test_extraction_agent.py::test_evidence_required -x` | ❌ Wave 0 |
| EXTRACT-03 | `missing`/`unclear`/`conflicting` fields are never `None`-collapsed; model never fills missing | unit (envelope contract) | `uv run pytest tests/test_field_envelope.py -x` | ✅ (existing) |
| EXTRACT-05 | `LengthFinishReasonError` → `error` event `{recoverable: true}`, no parse; refusal → `{recoverable: false}` | unit (mocked) | `uv run pytest tests/test_extraction_agent.py::test_truncation_raises_error_event -x` | ❌ Wave 0 |
| EXTRACT-05 | `unsupported` fields carry no value/evidence (envelope model_validator) | unit | `uv run pytest tests/test_field_envelope.py -x` | ✅ (existing) |
| PROMPT-03 | ≥3 trace JSON files exist under `docs/traces/`; each has raw + grounded diff | filesystem check | `uv run pytest tests/test_extraction_agent.py::test_traces_committed -x` | ❌ Wave 0 |
| walker coverage | Every `Field[T]` in `ExtractionResult` is reached by `_walk_and_ground` | unit | `uv run pytest tests/test_extraction_agent.py::test_walker_covers_all_fields -x` | ❌ Wave 0 |
| grounding gate | fabricated span → `unsupported`; genuine span survives | unit | `uv run pytest tests/test_grounding_gate.py -x` | ✅ (existing) |
| SSE taxonomy | all emitted event types in `EVENT_TYPES` | unit | `uv run pytest tests/test_sse_demo.py -x` (analogously for extraction route) | ✅ (existing pattern) |
| codegen drift | `ExtractionResult` change regenerates `shared-types` | unit | `uv run pytest tests/test_codegen_drift.py -x` | ✅ (existing) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_extraction_agent.py tests/test_grounding_gate.py tests/test_field_envelope.py -x`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work 3`

### Wave 0 Gaps

- [ ] `tests/test_extraction_agent.py` — covers EXTRACT-01/02/03/05, walker coverage, trace files check
- [ ] `docs/traces/` directory — for D-13 committed traces (created during trace-capture task)

*(Existing infrastructure: pytest, conftest, grounding gate tests, SSE demo tests, field envelope tests, codegen drift test — all cover their domains and are reused.)*

---

## Security Domain

> `security_enforcement` is not explicitly set to `false` in config — section included.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — single-buyer prototype |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | `VendorResponse.raw_text` is user-supplied; pydantic validates shape; max_length on API request body (per VendorGenRequest pattern in app.py) |
| V6 Cryptography | no | No crypto operations |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via vendor `raw_text` | Tampering / Spoofing | Vendor text injected as data context only (not system prompt); pydantic validates shape; grounding gate rejects snippets not in source (code-enforced, not model-trusting) |
| Model fabricating grounded claims | Information Disclosure | gate.py `ground_model()` code-enforced; no LLM-supplied `verified` flag trusted (CLAUDE.md §2/§8) |
| Oversized vendor text causing DoS | Denial of Service | Apply `max_length` on `raw_text` field in API request body (follow VendorGenRequest pattern, line 61 app.py) |
| Sensitive data in error events streamed to client | Information Disclosure | `ErrorPayload` carries only `code + message + recoverable`; API key never in any log or message (factory.py T-03-01 mitigation) |

---

## Sources

### Primary (HIGH confidence)

- Codebase: `services/ai/agents/_demo.py` — confirmed `get_stream_writer()` + `astream(stream_mode="custom")` pattern [VERIFIED]
- Codebase: `services/ai/api/app.py` — confirmed `EventSourceResponse` + `EventEnvelope(**chunk)` pattern [VERIFIED]
- Codebase: `services/ai/grounding/gate.py` — walker coverage (lines 320-366), `_walk_and_ground` shapes, D-04 dict comment [VERIFIED]
- Codebase: `services/ai/schemas/envelope.py` — `Field[T]` model_validator rules, `FlagStatus` states [VERIFIED]
- Codebase: `services/ai/schemas/domain.py` — current `ExtractionResult` stub; `vendor_name: Field[str]` Pitfall 5 confirmed at line 133 [VERIFIED]
- Codebase: `services/ai/pyproject.toml` — no new packages needed; all deps present [VERIFIED]
- Context7 `/websites/langchain_oss_python_langgraph` — `get_stream_writer()` + `astream(stream_mode="custom")` confirmed API [VERIFIED: Context7]

### Secondary (MEDIUM confidence)

- [langchain-ai/langchain #29700](https://github.com/langchain-ai/langchain/issues/29700) — `LengthFinishReasonError` propagates uncaught through `include_raw=True`; use direct `try/except` [CITED]
- [langchain-ai/langchain #25510](https://github.com/langchain-ai/langchain/issues/25510) — Refusal surfaces in `additional_kwargs["refusal"]` when using pydantic schema; dict schema loses it [CITED]
- [openai/openai-python #2406](https://github.com/openai/openai-python/issues/2406) — `LengthFinishReasonError` carries partial completion; not parseable [CITED]

### Tertiary (LOW confidence)

- Context7 `/websites/langchain_oss_python_langgraph` — `version="v2"` kwarg on `stream` in some examples; not used in codebase demo — follow codebase [LOW — may be version-specific]

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all packages installed and in use; no new deps
- Architecture: HIGH — all primitives verified in codebase; integration pattern proven by _demo.py
- Truncation/refusal detection: MEDIUM — primary source is GitHub issues (open bugs); workaround pattern derived from issue discussion; requires validation test
- Pitfalls: HIGH — grounded in actual code (gate.py, envelope.py, domain.py)
- Prompt design: HIGH — D-09/D-10 decisions are locked; gaps are prompt content (discretion area)
- Trace format: HIGH — D-12..D-15 fully specified in CONTEXT.md

**Research date:** 2026-06-27
**Valid until:** 2026-07-27 (stable stack; 30-day window)

**Graph note:** Graph is 4 commits behind current HEAD (built at `665afff`, current `bba7456`).
Semantic relationships treated as approximate for the 4 new commits (Phase 2 completion commits).
Core nodes verified by direct file reads.
