# Phase 3: Extraction Agent - Pattern Map

**Mapped:** 2026-06-27
**Files analyzed:** 6 new/modified files
**Analogs found:** 6 / 6

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `services/ai/schemas/domain.py` (ExtractionResult) | model | CRUD | `services/ai/schemas/domain.py` (RFQ / VendorResponse existing models) | exact |
| `services/ai/agents/extraction.py` | service | streaming + request-response | `services/ai/agents/_demo.py` + `services/ai/agents/rfq_gen.py` | exact (graph spine) + role-match (chain pattern) |
| `services/ai/prompts/extraction.v1.md` | config | — | `services/ai/prompts/extraction.v1.md` (stub frontmatter already correct) | exact (frontmatter shape) |
| `services/ai/api/app.py` (new `/extract/vendor` route) | controller | request-response + streaming | `services/ai/api/app.py` (`/stream/demo` + `/data/vendor-gen`) | exact |
| `services/ai/tests/test_extraction_agent.py` | test | — | `services/ai/tests/test_grounding_gate.py` + `services/ai/tests/test_sse_demo.py` | role-match |
| `docs/traces/` (JSON + Markdown trace files) | config/artifact | — | none (new artifact type) | no analog |

---

## Pattern Assignments

### `services/ai/schemas/domain.py` — ExtractionResult (model, CRUD)

**Analog:** `services/ai/schemas/domain.py` — `RFQ`, `VendorResponse`, `LineItem` (lines 33–121)
**Also reference:** `services/ai/schemas/envelope.py` — `Field[T]`, `Evidence`, `ConflictingValue` (full file)

**Imports pattern** (domain.py lines 1–28):
```python
from __future__ import annotations
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as pydantic_Field
from schemas.envelope import Field
```

**Model config pattern** (every model in domain.py):
```python
model_config = ConfigDict(extra="forbid")
```

**Field[T] usage pattern** (envelope.py lines 86–103):
```python
class Field(BaseModel, Generic[T]):  # noqa: UP046
    status: FlagStatus
    value: T | None = None
    evidence: list[Evidence] = pydantic_Field(default_factory=list)
    values: list[ConflictingValue[T]] | None = None
```
Every extracted fact uses `Field[T]`. Plain `str` for `vendor_name` (D-05 — provenance, not extracted claim). The `# noqa: UP046` comment is required on every `Generic[T]` class for pydantic2ts compat.

**Nested model pattern** (domain.py `LineItem`, lines 48–78):
```python
class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    # ... plain fields for RFQ-owned data
```
For `ExtractionResult`, the per-line-item container (`LineItemExtraction`) follows this same pattern but uses `Field[T]` fields internally. Multi-claim categories (`list[Field[T]]` or `list[SomeBaseModel]`) follow D-03/D-04 — no `dict[str, Field]` shapes anywhere.

**D-05 fix pattern** (domain.py line 133 — must change):
```python
# BEFORE (wrong stub):
vendor_name: Field[str] = Field[str](status="missing")  # type: ignore[call-arg]

# AFTER (correct per D-05):
vendor_name: str  # provenance metadata — NOT a grounded Field
```

**model_validator pattern** (domain.py lines 65–78 for LineItem):
```python
@model_validator(mode="after")
def _validate_budget_range(self) -> "LineItem":
    if self.budget_range_usd is not None:
        if len(self.budget_range_usd) != 2:
            raise ValueError(...)
    return self
```
Use `mode="after"` for validators that check field combinations. Keep validators on the model class, not on individual fields.

**After every ExtractionResult change:** run `uv run python scripts/codegen.py` and commit `packages/shared-types/index.d.ts`. The drift-check test (`test_codegen_drift.py`) enforces this.

---

### `services/ai/agents/extraction.py` (service, streaming + request-response)

**Primary analog:** `services/ai/agents/_demo.py` (full file — LangGraph StateGraph + get_stream_writer + astream spine)
**Secondary analog:** `services/ai/agents/rfq_gen.py` (lines 23–44 — prompt-load + with_structured_output chain)
**Also reference:** `services/ai/agents/vendor_gen.py` (lines 193–243 — invoke with template vars)

**Imports pattern** (_demo.py lines 19–27 + rfq_gen.py lines 13–20, merged for extraction):
```python
from __future__ import annotations
from typing import Any
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from openai import LengthFinishReasonError
from schemas.events import EVENT_TYPES, ErrorPayload
from schemas.events import EventEnvelope  # used in route, not graph module
from schemas.domain import ExtractionResult, RFQ, VendorResponse
from grounding.gate import ground_model
from grounding.report import DowngradeReport
from llm.factory import get_llm
from prompts.registry import load
```

**StateGraph build pattern** (_demo.py lines 51–57):
```python
_builder = StateGraph(dict)
_builder.add_node("demo", _demo_node)
_builder.add_edge(START, "demo")
_builder.add_edge("demo", END)
demo_graph = _builder.compile()
```
Extraction uses `StateGraph(dict)` with named nodes for each pipeline stage: `prepare` → `call_model` → `ground` → `emit_result` (or collapsed into fewer nodes — discretion area per CONTEXT.md). Compiled graph is a module-level singleton.

**get_stream_writer + emit pattern** (_demo.py lines 30–47):
```python
def _demo_node(state: dict[str, Any]) -> dict[str, Any]:
    w = get_stream_writer()
    assert {"status", "partial", "result"} <= set(EVENT_TYPES)  # taxonomy drift guard
    w({"type": "status", "payload": {"message": "Demo graph running", "phase": "demo"}})
    w({"type": "result", "payload": {"demo": True, "summary": "SSE spine proof complete"}})
    return {}
```
Every node gets `w = get_stream_writer()`. Emit `status` events for phase progress. Emit `result` only once after grounding. Never emit ungrounded facts (D-07). Keep the `assert ... <= set(EVENT_TYPES)` taxonomy drift guard.

**Prompt-load + chain pattern** (rfq_gen.py lines 32–43):
```python
post = load("rfq-gen")
prompt = ChatPromptTemplate.from_messages([
    ("system", post.content),
    ("human", "Generate the RFQ now."),
])
llm = get_llm("reasoning").with_structured_output(RFQ, method="json_schema")
chain = prompt | llm
result = chain.invoke({})
assert isinstance(result, RFQ), f"Expected RFQ, got {type(result)}"
```
Extraction uses `load("extraction")` and `with_structured_output(ExtractionModelOutput, method="json_schema")`. The human message injects `vendor_text` and `rfq_line_items` as template vars. `isinstance` assert confirms the pydantic instance.

**Truncation + refusal error pattern** (RESEARCH.md Pattern 2 — no direct analog, but ErrorPayload is in events.py lines 23–36):
```python
try:
    raw = chain.invoke({"vendor_text": vendor.raw_text, ...})
except LengthFinishReasonError:
    w({"type": "error", "payload": ErrorPayload(
        code="extraction_truncated",
        message="Model output was truncated (finish_reason=length).",
        recoverable=True,
    ).model_dump()})
    return {"error": "truncated"}
# Refusal: chain raises ValidationError or returns None parsed;
# detect via try/except around invoke or post-call check
```
`LengthFinishReasonError` is from `openai` (transitive dep, already installed). Never parse a truncated result. Emit `error` event with `ErrorPayload`. `recoverable=True` for truncation, `recoverable=False` for refusal.

**ground_model call pattern** (gate.py lines 369–380):
```python
def ground_model(obj: BaseModel, sources: dict[str, str]) -> tuple[BaseModel, DowngradeReport]:
    new_obj, entries = _walk_and_ground(obj, sources)
    return new_obj, DowngradeReport(entries=entries)
```
Extraction calls: `grounded, report = ground_model(raw_result, {vendor.source_id: vendor.raw_text})`. The `sources` dict is keyed by `Evidence.source_id`. Returns `(grounded_ExtractionResult, DowngradeReport)`.

**Result emit pattern** (follows _demo.py result emit):
```python
w({"type": "result", "payload": {
    "extraction": grounded.model_dump(mode="json"),
    "downgrade_report": report.model_dump(mode="json"),
}})
return {"result": grounded, "report": report}
```
Use `model_dump(mode="json")` for Decimal serialization. Include `downgrade_report` in the result payload so the SSE client receives the raw-vs-grounded diff in one event.

---

### `services/ai/prompts/extraction.v1.md` (config, prompt)

**Analog:** `services/ai/prompts/extraction.v1.md` — existing stub (frontmatter already correct, lines 1–20)

**Frontmatter pattern** (extraction.v1.md lines 1–20 — keep as-is, add body):
```yaml
---
id: extraction
version: 1
intent: >
  Read a single vendor response and produce a structured ExtractionResult: ...
model_tier: reasoning
failure_handling: >
  Never fill missing info. If a field cannot be traced to a verbatim snippet ...
---
```
The frontmatter shape is correct. Replace the `TODO P3 / EXTRACT-01: ...` body with the full prompt. The registry's `load("extraction")` resolves `extraction.v1.md` automatically.

**Prompt registry load pattern** (registry.py lines 50–68):
```python
post = load("extraction")
print(post.metadata["intent"])   # frontmatter dict
print(post.content)              # body after ---
```
`post.content` is the raw prompt body string. `post.metadata` is the parsed frontmatter dict. The `id` and `version` fields in frontmatter are documentation/traceability, not programmatically read by the registry.

**Prompt body requirements** (from CONTEXT.md D-09/D-10/D-11):
- Model uses ONLY 4 states: `present | missing | unclear | conflicting`. Never mention `unsupported` (gate-only).
- Verbatim evidence instruction: quote ≥3 words / ≥20 chars of context; never paraphrase.
- `source_id` field in evidence: must match `VendorResponse.source_id` passed in the prompt context.
- Humility bias: prefer `unclear` over confident `present` on fuzzy values; prefer `missing` over inventing.
- RFQ line items injected as structured titles+descriptions (not full doc).

---

### `services/ai/api/app.py` — new `/extract/vendor` SSE route (controller, streaming)

**Analog:** `services/ai/api/app.py` — `/stream/demo` route (lines 99–122) + `VendorGenRequest` + `/data/vendor-gen` (lines 57–96)

**Request body pattern** (app.py lines 57–61):
```python
class VendorGenRequest(BaseModel):
    persona: str = pydantic_Field(max_length=64)
    rfq_text: str | None = pydantic_Field(default=None, max_length=200_000)
```
New `ExtractionRequest` follows same pattern: `VendorResponse` + `RFQ` fields, with `max_length` on `raw_text` (security: T-02-11 / V5 input validation per RESEARCH.md).

**SSE route pattern** (app.py lines 99–122):
```python
@app.get("/stream/demo")
async def stream_demo() -> EventSourceResponse:
    async def _generate() -> AsyncGenerator[dict, None]:
        async for chunk in demo_graph.astream({}, stream_mode="custom"):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}
    return EventSourceResponse(_generate())
```
Extraction route is `@app.post("/extract/vendor")`. Passes `{"vendor": req.vendor, "rfq": req.rfq}` as the graph input dict. `EventEnvelope(**chunk)` validates every chunk before serialization — a malformed emit fails here, never reaches the client. `done` appended by the route after the graph completes, not by the graph itself.

**Import addition pattern** (app.py lines 35–39):
```python
from agents._demo import demo_graph
from agents.rfq_gen import generate_rfq, render_rfq_md
from agents.vendor_gen import MESS_SPECS, generate_vendor_response
```
Add: `from agents.extraction import extraction_graph` alongside existing agent imports.

**Security pattern** (app.py line 60–61, RESEARCH.md security §V5):
```python
raw_text: str | None = pydantic_Field(default=None, max_length=200_000)
```
Apply same `max_length` guard to `ExtractionRequest.vendor.raw_text` — vendor text is user-supplied and must be bounded.

---

### `services/ai/tests/test_extraction_agent.py` (test)

**Primary analog:** `services/ai/tests/test_grounding_gate.py` (full file — class-based pytest, inline pydantic models, real objects not mocks)
**Secondary analog:** `services/ai/tests/test_sse_demo.py` (full file — TestClient without lifespan, SSE parse helper, taxonomy assertions)
**Also reference:** `services/ai/tests/test_field_envelope.py` (lines 1–50 — imports, standalone function tests alongside class tests)

**Imports pattern** (test_grounding_gate.py lines 1–27):
```python
from __future__ import annotations
import pytest
from pydantic import BaseModel, ConfigDict
from schemas.envelope import ConflictingValue, Evidence, Field, FlagStatus
from grounding.gate import ground_field, ground_model
from grounding.report import DowngradeEntry, DowngradeReport
```
Extraction test imports: `from agents.extraction import extraction_graph, generate_extraction` (or whatever the public API is), plus schema imports.

**TestClient without lifespan pattern** (test_sse_demo.py lines 43–44):
```python
client = TestClient(app, raise_server_exceptions=True)
```
No context manager — skips lifespan (startup OpenAI access check). Required for all unit tests; live model calls tested separately.

**SSE parse helper pattern** (test_sse_demo.py lines 143–160):
```python
def _parse_sse_events(body: str) -> list[dict]:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            payload_str = line[len("data: "):]
            if payload_str:
                try:
                    event = json.loads(payload_str)
                    events.append(event)
                except json.JSONDecodeError as exc:
                    pytest.fail(f"SSE event is not valid JSON: {payload_str!r} — {exc}")
    return events
```
Reuse this exact helper (or import from test_sse_demo if visible to pytest) — do not reimplement.

**Inline pydantic model pattern for unit tests** (test_grounding_gate.py lines 255–275):
```python
class _TestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    genuine_field: Field[str]
    fabricated_field: Field[str]
```
Define inline test models in test functions/classes when the real schema isn't needed. Keeps tests self-contained.

**Class grouping pattern** (test_grounding_gate.py):
```python
class TestFabricatedSpanDowngrade:
    def test_fabricated_span_is_downgraded(self) -> None: ...

class TestGenuineSpanPasses:
    def test_genuine_span_passes_grounding(self) -> None: ...
```
Group by behavior/scenario, not by function. One class per logical concern.

**Mocked model call pattern** (no existing analog — use `unittest.mock.patch`):
```python
# For truncation/refusal tests — mock the chain.invoke to raise LengthFinishReasonError
from unittest.mock import patch, MagicMock
from openai import LengthFinishReasonError

def test_truncation_raises_error_event():
    with patch("agents.extraction._build_chain") as mock_chain:
        mock_chain.return_value.invoke.side_effect = LengthFinishReasonError(...)
        # drive the graph synchronously or inspect state dict
```
Tests that cover EXTRACT-05 (truncation/refusal) must mock at the chain level to avoid live API calls.

**Trace file existence check pattern** (filesystem, no analog — use pathlib):
```python
import pathlib
def test_traces_committed():
    traces_dir = pathlib.Path(__file__).parents[3] / "docs" / "traces"
    json_traces = list(traces_dir.glob("*.json"))
    assert len(json_traces) >= 3, f"Expected ≥3 JSON traces, found {len(json_traces)}"
```

---

### `docs/traces/` directory (artifact)

**No analog.** New artifact type. From CONTEXT.md D-13/D-14:
- Each trace: one JSON file + one Markdown file per vendor.
- JSON filename convention: `trace_{vendor_name}_{timestamp_or_index}.json`
- JSON shape (D-14): `{"input": {...}, "resolved_prompt": {...}, "raw_model_output": {...}, "grounding_step": {...}, "final_result": {...}}`
- Markdown: human-readable rendering of the JSON trace for the submission/demo.

---

## Shared Patterns

### FlagStatus / Field[T] envelope
**Source:** `services/ai/schemas/envelope.py` (full file, lines 1–177)
**Apply to:** `ExtractionResult` schema and all sub-models (`LineItemExtraction`, etc.)

The `model_validator` on `Field[T]` (lines 105–175) enforces all semantic rules at construction time. The extraction agent never needs to check flag semantics manually — the schema does it. Key rules:
- `present` → `value` not None, `evidence` non-empty
- `missing` / `unsupported` → `value` None, `evidence` empty
- `conflicting` → `values[]` non-empty, each `ConflictingValue` has `evidence`
- `unclear` with `value` → `evidence` required

### Prompt registry load
**Source:** `services/ai/prompts/registry.py` (lines 50–68)
**Apply to:** `extraction.py` agent

```python
post = load("extraction")   # resolves extraction.v1.md
prompt_body = post.content  # string body after frontmatter
```

### EventEnvelope validation before SSE emit
**Source:** `services/ai/api/app.py` (lines 117–118)
**Apply to:** `/extract/vendor` route generator
```python
yield {"data": EventEnvelope(**chunk).model_dump_json()}
```
Every chunk from `astream` is validated through `EventEnvelope` before serialization. A node emitting an unknown `type` fails loudly here, not silently downstream.

### model_dump(mode="json") for Decimal
**Source:** `services/ai/api/app.py` lines 72 and 95 (`rfq.model_dump(mode="json")`)
**Apply to:** `emit_result` node in extraction graph

`mode="json"` serializes `Decimal` as a JSON-compatible string. Required whenever `ExtractionResult` (which contains `Field[Decimal]` for pricing) is serialized into an SSE payload.

### get_llm factory
**Source:** `services/ai/agents/rfq_gen.py` line 39
**Apply to:** `extraction.py` model call node
```python
llm = get_llm("reasoning").with_structured_output(Schema, method="json_schema")
```
`get_llm("reasoning")` maps to gpt-5.4 via the factory. Never hardcode model IDs. `method="json_schema"` uses the OpenAI structured-output API path (schema enforced at API level).

### model_copy immutability
**Source:** `services/ai/grounding/gate.py` lines 291, 317, 366
**Apply to:** any schema manipulation in extraction nodes
```python
return field.model_copy(update={"evidence": new_evidence}), []
return obj.model_copy(update=updates), report
```
Never mutate pydantic model instances in place. Always return new objects via `model_copy(update=...)`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `docs/traces/` (JSON + Markdown) | artifact | — | No existing trace artifact format in the codebase; D-13/D-14 define the shape from scratch |

---

## Metadata

**Analog search scope:** `services/ai/agents/`, `services/ai/schemas/`, `services/ai/api/`, `services/ai/grounding/`, `services/ai/tests/`, `services/ai/prompts/`
**Files read:** 13 source files
**Pattern extraction date:** 2026-06-27
