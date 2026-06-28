# Phase 4: Comparison Agent - Pattern Map

**Mapped:** 2026-06-28
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `services/ai/schemas/domain.py` (modify) | model | CRUD | `services/ai/schemas/domain.py` itself (ExtractionResult section) | exact |
| `services/ai/agents/comparison.py` | agent/service | request-response + streaming | `services/ai/agents/extraction.py` | exact |
| `services/ai/api/app.py` (modify) | route/controller | request-response + SSE | `services/ai/api/app.py` itself (`/extract/vendor` route) | exact |
| `services/ai/prompts/comparison.v1.md` (replace stub) | prompt | request-response | `services/ai/prompts/extraction.v1.md` | exact (same pack structure) |
| `services/ai/prompts/clarification.v1.md` (replace stub) | prompt | request-response | `services/ai/prompts/extraction.v1.md` (frontmatter + intent) | role-match |
| `services/ai/tests/test_comparison_agent.py` | test | - | `services/ai/tests/test_extraction_agent.py` | exact |
| `services/ai/scripts/capture_comparison_trace.py` | script/utility | batch | `services/ai/scripts/capture_traces.py` | exact |
| `docs/traces/comparison_trace_*.json` + `*.md` | artifact | - | `docs/traces/trace_*.json` + `*.md` | exact |

---

## Pattern Assignments

### `services/ai/schemas/domain.py` — ComparisonResult redesign

**Analog:** `services/ai/schemas/domain.py` (ExtractionResult + LineItemExtraction sections, lines 116–175)

**Imports pattern** (lines 1–23 of domain.py — reuse verbatim):
```python
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as pydantic_Field
from schemas.envelope import Field
```

**Core schema pattern** — every sub-model follows this shape (lines 26–35 for MessSpecItem as the simplest example; lines 116–131 for LineItemExtraction as the list-of-BaseModel example):
```python
class SomeName(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # plain str fields for provenance (not Field[T])
    # Field[T] only for extracted/grounded facts
    # list[BaseModel] never dict[str, BaseModel] (pydantic2ts requirement)
```

**New StrEnum pattern** — copy the FlagStatus pattern from `services/ai/schemas/envelope.py` lines 27–37:
```python
from enum import StrEnum

class ComparabilityVerdict(StrEnum):
    """Comparison-level verdict — NOT a field-level FlagStatus (D-02).
    Lives in domain.py, never in envelope.py.
    """
    comparable = "comparable"
    partially = "partially"
    not_comparable = "not_comparable"
```

**`extra="forbid"` everywhere** — every model in this file uses it (lines 34, 49, 82, 124, 145). No exceptions.

**`list[BaseModel]` not `dict[str, Model]`** — the established pattern from ExtractionResult (lines 148–159):
```python
# CORRECT (pydantic2ts-compatible, matches existing ExtractionResult pattern):
dimensions: list[DimensionComparison]        # not dict[str, DimensionComparison]
line_item_offers: list[LineItemOffer]        # not dict[str, LineItemOffer]
vendor_readiness: list[VendorReadiness]      # not dict[str, VendorReadiness]
```

**Stub to replace** (lines 163–175 of domain.py — delete these two fields, replace with full schema):
```python
# DELETE:
vendor_count: Field[int] = Field[int](status="missing")  # type: ignore[call-arg]
comparable: Field[str] = Field[str](status="missing")    # type: ignore[call-arg]
```

**ComparisonResult must NOT contain `Field[T]` wrappers** — comparability verdicts are plain `str`/`ComparabilityVerdict`, not grounded extracted facts. Only `ExtractionResult` fields use the `Field[T]` envelope. The comparison result is computed by code + model, not grounded against raw text.

**`clamp_report` placement** — include as a field ON `ComparisonResult` directly (RESEARCH.md Pitfall 5 recommendation: simpler than the sibling-spread + collision-assert approach used for `downgrade_report` in extraction):
```python
class ComparisonResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_names: list[str]                            # input order preserved, never sorted
    dimensions: list[DimensionComparison]              # 6 entries
    line_item_offers: list[LineItemOffer]              # 8 × N vendors
    vendor_readiness: list[VendorReadiness]            # N entries, input order preserved
    attention_points: list[AttentionPoint]
    clarification_questions: list[ClarificationQuestion]
    clamp_report: ClampReport                          # rides the result payload; Phase 5 trace viewer gets it free
```

---

### `services/ai/agents/comparison.py` — LangGraph comparison agent

**Analog:** `services/ai/agents/extraction.py` (entire file, lines 1–396)

**Module docstring pattern** (lines 1–23 of extraction.py — mirror the structure):
```python
"""
comparison.py — Comparison agent: LangGraph StateGraph that aligns inputs,
computes comparability ceilings, calls the model, applies the verdict clamp,
and emits SSE events (Phase 4, COMPARE-01..05).

# ponytail: <explain the two-path model-failure detection inherited from extraction.py>
"""
```

**Imports pattern** (lines 25–43 of extraction.py — adapt for comparison):
```python
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from openai import LengthFinishReasonError

from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import ComparisonResult, ExtractionResult, RFQ
from schemas.envelope import FlagStatus
from schemas.events import EVENT_TYPES, ErrorPayload
```

**Module-level chain pattern** (lines 48–65 of extraction.py — one chain per model tier):
```python
_comparison_post = load("comparison")
_clarification_post = load("clarification")

# ponytail: SystemMessage (not tuple) prevents {braces} in examples being parsed as template vars
_comparison_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=_comparison_post.content),
    ("human", "{input}"),
])
_clarification_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=_clarification_post.content),
    ("human", "{flagged_fields}"),
])

# include_raw=True: inspect additional_kwargs["refusal"] and parsed/parsing_error — same as extraction
_comparison_chain = get_llm("reasoning").with_structured_output(
    ComparisonResult, method="json_schema", include_raw=True
)
_clarification_chain = get_llm("cheap").with_structured_output(
    ClarificationSet, method="json_schema", include_raw=True
)
```

**Node / impl split pattern** (lines 88–260 of extraction.py — the `_run_*_impl` / `_*_node` split for testability):
```python
def _run_compare_impl(state: dict[str, Any], emit: Callable[[dict], None]) -> dict[str, Any]:
    """Core comparison logic — separated so tests can inject emit collector.
    # ponytail: split from _compare_node so tests can patch _comparison_chain and
    # capture emitted events without needing a running LangGraph event loop.
    """
    assert {"status", "result", "error"} <= set(EVENT_TYPES)  # taxonomy guard — mirrors extraction.py line 103
    # ...
    emit({"type": "status", "payload": {"message": "...", "phase": "..."}})
    # ...

def _compare_node(state: dict[str, Any]) -> dict[str, Any]:
    w = get_stream_writer()
    return _run_compare_impl(state, w)
```

**Full error handling pattern** (lines 116–249 of extraction.py — apply verbatim to the model call node, adapting error codes):
```python
try:
    try:
        raw_output = _comparison_chain.invoke({"input": ...})
    except LengthFinishReasonError:
        emit({"type": "error", "payload": ErrorPayload(
            code="comparison_truncated",
            message="Model output was truncated (finish_reason=length).",
            recoverable=True,
        ).model_dump()})
        return {"error": "truncated"}

    raw_msg = raw_output["raw"]
    if raw_msg.additional_kwargs.get("refusal"):
        emit({"type": "error", "payload": ErrorPayload(
            code="comparison_refused",
            message="Model refused to process the comparison request.",
            recoverable=False,
        ).model_dump()})
        return {"error": "refusal"}

    parsed = raw_output.get("parsed")
    parsing_error = raw_output.get("parsing_error")
    if parsed is None or parsing_error is not None:
        emit({"type": "error", "payload": ErrorPayload(
            code="comparison_parse_error",
            message=f"Structured output parse failed: {parsing_error!r}",
            recoverable=True,
        ).model_dump()})
        return {"error": "parse_error"}

    if not isinstance(parsed, ComparisonResult):
        emit({"type": "error", "payload": ErrorPayload(
            code="comparison_unexpected_type",
            message=f"Expected ComparisonResult, got {type(parsed).__name__}",
            recoverable=False,
        ).model_dump()})
        return {"error": "unexpected_type"}

    # --- SUCCESS PATH (CR-01: inside the try) ---
    # Apply verdict clamp BEFORE emitting result (D-03 / RESEARCH.md Pitfall 1)
    clamped, clamp_report = _apply_verdict_clamp(parsed, state["ceilings"])
    result_with_clamp = clamped.model_copy(update={"clamp_report": clamp_report})
    emit({"type": "result", "payload": result_with_clamp.model_dump(mode="json")})
    return {"result": result_with_clamp}

except Exception as exc:
    emit({"type": "error", "payload": ErrorPayload(
        code="comparison_error", message=str(exc), recoverable=False,
    ).model_dump()})
    return {"error": "comparison_error"}
```

**Graph build pattern** (lines 268–276 of extraction.py — multi-node version):
```python
def _build_comparison_graph():
    builder = StateGraph(dict)
    builder.add_node("align", _align_node)
    builder.add_node("comparability", _comparability_node)
    builder.add_node("compare", _compare_node)
    builder.add_node("clarify", _clarify_node)
    builder.add_edge(START, "align")
    builder.add_edge("align", "comparability")
    builder.add_edge("comparability", "compare")
    builder.add_edge("compare", "clarify")
    builder.add_edge("clarify", END)
    return builder.compile()

comparison_graph = _build_comparison_graph()
```

**Testable sync wrapper pattern** (lines 284–322 of extraction.py):
```python
def run_comparison(extractions: list[ExtractionResult], rfq: RFQ) -> dict[str, Any]:
    """Synchronous testable wrapper — bypasses LangGraph runtime for test use.
    # ponytail: direct node invocation for testability — does NOT exercise the
    # LangGraph SSE streaming path. Production path uses comparison_graph.astream.
    """
    events: list[dict] = []
    def _collect(event: dict) -> None:
        events.append(event)
    # ... drive each impl function directly
```

**Verdict clamp module** — add to `services/ai/agents/comparison.py` (or a sibling `services/ai/grounding/verdict_clamp.py`). Pattern mirrors `gate.py`'s downgrade logic (lines 236–316 of gate.py): code computes a ceiling, returns a report of every downgrade. Key shape:
```python
# ponytail: _VERDICT_ORDER exists so min(model, ceiling) is an index comparison,
# not string comparison — same intent as FlagStatus ordering in gate.py.
_VERDICT_ORDER: dict[str, int] = {"comparable": 2, "partially": 1, "not_comparable": 0}

def _ceiling_for_flags(flag_statuses: list[FlagStatus]) -> str:
    for s in flag_statuses:
        if s in (FlagStatus.missing, FlagStatus.unsupported):
            return "not_comparable"
    for s in flag_statuses:
        if s in (FlagStatus.unclear, FlagStatus.conflicting):
            return "partially"
    return "comparable"

def clamp_verdict(model_verdict: str, code_ceiling: str) -> str:
    return model_verdict if _VERDICT_ORDER[model_verdict] <= _VERDICT_ORDER[code_ceiling] else code_ceiling
```

The `ClampReport` / `ClampEntry` pair mirrors `DowngradeReport` / `DowngradeEntry` from `services/ai/grounding/report.py` (lines 17–47):
```python
# report.py pattern — apply verbatim for ClampEntry / ClampReport:
class ClampEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_name: str
    dimension: str
    model_proposed: str        # mirrors DowngradeEntry.original_status
    code_ceiling: str
    clamped_to: str
    ceiling_reason: str        # mirrors DowngradeEntry.reason

class ClampReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entries: list[ClampEntry] = pydantic_Field(default_factory=list)

    @property
    def has_downgrades(self) -> bool:   # mirrors DowngradeReport.has_downgrades
        return len(self.entries) > 0
```

**Flag walking for clarification seeding** — adapt `_walk_and_ground` from gate.py (lines 320–366) as a read-only collector:
```python
# gate.py _walk_and_ground pattern (lines 320–366) — read-only variant:
# Instead of grounding each Field[T], collect (field_path, status) for non-present statuses.
# Same recursion: isinstance(value, EnvelopeField) → check status; isinstance(value, BaseModel)
# → recurse; isinstance(value, list) → iterate with [i] indexing.
def _collect_flagged_fields(obj: BaseModel, vendor_name: str, path: str = "") -> list[FlaggedField]:
    flagged = []
    for field_name in type(obj).model_fields:
        value = getattr(obj, field_name)
        field_path = f"{path}.{field_name}" if path else field_name
        if isinstance(value, EnvelopeField):
            if value.status != FlagStatus.present:
                flagged.append(FlaggedField(
                    vendor_name=vendor_name,
                    field_path=field_path,
                    flag_status=value.status.value,
                ))
        elif isinstance(value, BaseModel):
            flagged.extend(_collect_flagged_fields(value, vendor_name, field_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, EnvelopeField):
                    if item.status != FlagStatus.present:
                        flagged.append(FlaggedField(...))
                elif isinstance(item, BaseModel):
                    flagged.extend(_collect_flagged_fields(item, vendor_name, f"{field_path}[{i}]"))
    return flagged
```

---

### `services/ai/api/app.py` — `/compare/vendors` SSE route

**Analog:** `services/ai/api/app.py` — `/extract/vendor` route (lines 101–182)

**Request body pattern** (lines 101–136 — adapt for comparison):
```python
class ComparisonRequest(BaseModel):
    """Request body for POST /compare/vendors.
    # ponytail: max_length guard — no raw_text in ExtractionResult, so no char cap needed;
    # a vendor count guard is sufficient (RESEARCH.md Open Question 2).
    """
    extractions: list[ExtractionResult]
    rfq: RFQ

    _MAX_VENDORS = 5

    @model_validator(mode="after")
    def _check_vendor_count(self) -> "ComparisonRequest":
        if len(self.extractions) > self._MAX_VENDORS:
            raise ValueError(
                f"extractions list exceeds {self._MAX_VENDORS} vendors "
                f"(got {len(self.extractions)})"
            )
        return self
```

**SSE route pattern** (lines 165–182 of app.py — copy verbatim, adapt graph + state key):
```python
@app.post("/compare/vendors")
async def compare_vendors(req: ComparisonRequest) -> EventSourceResponse:
    """Stream vendor comparison as SSE events (COMPARE-01).

    Accepts ExtractionResult[] + RFQ, runs the comparison graph, streams
    status → status → status → status → result → done events.
    Clamp runs server-side before the result event (D-03).
    """
    async def _generate() -> AsyncGenerator[dict, None]:
        async for chunk in comparison_graph.astream(
            {"extractions": req.extractions, "rfq": req.rfq},
            stream_mode="custom",
        ):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}

    return EventSourceResponse(_generate())
```

**Import additions** needed at top of app.py (following the existing import block structure, lines 35–41):
```python
from agents.comparison import comparison_graph
from schemas.domain import ComparisonResult  # already imported if domain exports it
```

---

### `services/ai/prompts/comparison.v1.md` — full comparison prompt

**Analog:** `services/ai/prompts/extraction.v1.md` (entire file, lines 1–291)

**Frontmatter pattern** (lines 1–20 of extraction.v1.md — the stub already has correct frontmatter; flesh out `failure_handling`):
```yaml
---
id: comparison
version: 1
intent: >
  Compare a set of ExtractionResult objects (one per vendor) across six dimensions:
  technical, commercial, scope, timeline, compliance, risk. Establishes comparability
  before any ranking. Produces a badge matrix, line-item offer table, per-vendor readiness
  descriptor, buyer attention points, and clarification questions. Never ranks, never
  normalizes, never invents claims beyond extraction data.
model_tier: reasoning
failure_handling: >
  If vendor data is insufficient to compare on a dimension, output not_comparable with a
  reason — never force comparable on incomplete data. Quote only verbatim values from the
  ExtractionResult. Do not convert currencies, split bundles, or infer per-item prices.
  Flag non-equivalence ("bundled — not separable", "quoted EUR vs USD"). A not_comparable
  that prevents a misleading comparison is better than a comparable built on incomplete data.
---
```

**Role framing section** — mirrors extraction.v1.md lines 22–29 (the "evidence contract" opening):
```markdown
You are a **procurement comparison agent**. Your job is to compare vendor proposals
side by side, based solely on structured extraction data already extracted from each vendor.

You operate under a strict **evidence contract**: every fact you cite in your comparison
must appear in the ExtractionResult data you receive. You never introduce new claims, infer
numbers not stated, or paraphrase facts beyond what extraction produced.
```

**Verdict definitions section** — mirrors "THE FOUR FLAG STATES" section (extraction.v1.md lines 31–63), but for ComparabilityVerdict:
```markdown
## THE THREE COMPARABILITY VERDICTS

Every dimension cell uses one of exactly three verdict values:

### comparable
All vendors addressed this dimension with present or unclear (but meaningful) data.
A side-by-side comparison on this dimension is valid.

### partially
At least one vendor has unclear or conflicting data on a contributing field.
A partial comparison is possible but the buyer should be aware of the gaps.

### not_comparable
At least one vendor has missing or unsupported data on a contributing field.
A comparison on this dimension would be misleading — surface the gap, not a forced ranking.
**Do NOT output comparable or partially when contributing fields are missing.**
```

**Humility instruction** — mirrors extraction.v1.md lines 150–155:
```markdown
## HUMILITY INSTRUCTION

A `not_comparable` that prevents a misleading comparison is better than a `comparable`
built on incomplete data. The buyer would rather see an honest gap than a forced ranking.
When in doubt, use `partially` over `comparable`, and `not_comparable` over `partially`.
```

**Output format / few-shot section** — mirrors extraction.v1.md lines 166–276. Provide ≥3 examples: (1) all-present → comparable, (2) unclear field → partially, (3) missing field → not_comparable.

---

### `services/ai/prompts/clarification.v1.md` — full clarification prompt

**Analog:** `services/ai/prompts/extraction.v1.md` (frontmatter + role-framing + humility sections)

**Frontmatter** — the stub (lines 1–18) already has the correct structure; flesh out the body. The stub's `failure_handling` is already well-specified.

**Role framing** (adapt the extraction contract opening):
```markdown
You are a **clarification question drafter**. You receive a list of flagged fields from vendor
extractions. For each item in the list, you draft one specific, professional question the buyer
can send to the vendor to resolve the gap.

**Strict constraint:** You draft questions ONLY for the items in the list provided. You do not
add questions for fields not in this list. The list is exhaustive — `N` items → exactly `N`
questions. Do not invent additional gaps.
```

**Humility / specificity instruction**:
```markdown
Generic questions ("Please clarify your pricing") are rejected. Each question must:
1. Name the vendor.
2. Name the exact line item or field.
3. Describe the exact nature of the ambiguity (missing, unclear value, conflicting statements).

Example of a REJECTED question: "Can you clarify your compliance approach?"
Example of an ACCEPTED question: "Vendor X's kids advertising & claims compliance section
lists no specific regulatory standards. Which standards (e.g. ACCC, ARPA) does your compliance
review cover for TVC content targeting children?"
```

---

### `services/ai/tests/test_comparison_agent.py` — test file

**Analog:** `services/ai/tests/test_extraction_agent.py` (entire file, lines 1–563)

**File structure pattern** (lines 1–44 of test_extraction_agent.py):
```python
"""
test_comparison_agent.py — Phase 4 comparison agent verification gates.

One-to-one mapping with 04-VALIDATION.md Per-Task Verification Map:
  test_schema_shape               → COMPARE-01 / schema structure
  test_clamp_only_downgrades      → COMPARE-02 (clamp)
  test_no_aggregation_over_missing → COMPARE-02 (no-agg)
  test_attention_points_are_triggered → COMPARE-03 (attn)
  test_clarification_seeded_by_code   → COMPARE-03 (clarif)
  test_offer_table_verbatim       → COMPARE-04
  test_vendor_order_preserved     → COMPARE-05
  test_no_numeric_score           → COMPARE-05 (schema)
  test_comparison_sse_taxonomy    → SSE taxonomy
  test_truncation_error_event     → EXTRACT-05 analog (truncation)
  test_refusal_error_event        → EXTRACT-05 analog (refusal)
  test_comparison_traces_committed → PROMPT-03 / D-11
"""
from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from schemas.domain import ComparisonResult
from schemas.envelope import FlagStatus
from schemas.events import EVENT_TYPES
```

**Truncation test pattern** (lines 206–233 of test_extraction_agent.py — mirror with `agents.comparison._comparison_chain` and `run_comparison`):
```python
def test_truncation_error_event() -> None:
    from agents.comparison import run_comparison
    with patch("agents.comparison._comparison_chain") as mock_chain:
        mock_chain.invoke.side_effect = LengthFinishReasonError(completion=MagicMock())
        state = run_comparison(extractions=[...], rfq=MagicMock())
    assert state.get("error") == "truncated"
    last_event = state.get("last_sse_event")
    assert last_event["type"] == "error"
    assert last_event["payload"]["recoverable"] is True
```

**Refusal test pattern** (lines 240–267 of test_extraction_agent.py):
```python
def test_refusal_error_event() -> None:
    from agents.comparison import run_comparison
    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {"refusal": "I cannot process this request."}
    with patch("agents.comparison._comparison_chain") as mock_chain:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": None}
        state = run_comparison(extractions=[...], rfq=MagicMock())
    assert state.get("error") == "refusal"
    assert state["last_sse_event"]["payload"]["recoverable"] is False
```

**SSE taxonomy test** (lines 337–407 of test_extraction_agent.py — mirror for `/compare/vendors`):
```python
def test_comparison_sse_taxonomy() -> None:
    from api.app import app
    from fastapi.testclient import TestClient
    # ... patch _comparison_chain with canned ComparisonResult
    # ... POST to /compare/vendors with minimal ExtractionResult[] + RFQ body
    # ... assert all event["type"] in EVENT_TYPES
```

**Traces committed test** (lines 415–529 of test_extraction_agent.py — mirror for comparison traces):
```python
def test_comparison_traces_committed() -> None:
    traces_dir = pathlib.Path(__file__).parents[3] / "docs" / "traces"
    # >=1 comparison JSON trace with keys: input, resolved_prompt, raw_model_output,
    # clamp_step, clarification_step, final_result
    json_traces = [p for p in traces_dir.glob("comparison_*.json")]
    assert len(json_traces) >= 1
    required_keys = {"input", "resolved_prompt", "raw_model_output", "clamp_step", "final_result"}
    for trace_path in json_traces:
        trace = json.loads(trace_path.read_text())
        assert not (required_keys - set(trace.keys()))
        # Assert clamp_step has at least one entry (the rubric story)
        assert len(trace["clamp_step"]["entries"]) >= 1, (
            "comparison trace must show >=1 verdict downgrade for the D-11 rubric story"
        )
```

**Conftest helper pattern** — create `conftest_comparison.py` following `conftest_extraction.py` (lines 1–67):
```python
# conftest_comparison.py — shared builders for comparison tests
from schemas.envelope import Field, FlagStatus

def missing_extraction_result(vendor_name: str) -> ExtractionResult:
    """Minimal ExtractionResult where all Field[T] attributes are missing."""
    ...

def present_extraction_result(vendor_name: str) -> ExtractionResult:
    """ExtractionResult with present fields for clamp test baseline."""
    ...
```

---

### `services/ai/scripts/capture_comparison_trace.py` — trace capture script

**Analog:** `services/ai/scripts/capture_traces.py` (entire file, lines 1–269)

**Structure pattern** (lines 25–101 of capture_traces.py — apply verbatim, adapting for comparison):
```python
REPO_ROOT = pathlib.Path(__file__).parents[3]
DATA_DIR = REPO_ROOT / "data"
TRACES_DIR = REPO_ROOT / "docs" / "traces"

from agents.comparison import generate_comparison_with_trace  # the authorized trace-capture surface
from prompts.registry import load
from schemas.domain import ExtractionResult, RFQ

def _build_comparison_trace(
    extractions: list[ExtractionResult],
    rfq: RFQ,
) -> dict | None:
    try:
        raw_result, clamped_result, clamp_report, clarification_result = generate_comparison_with_trace(
            extractions, rfq
        )
    except ValueError as exc:
        print(f"  ERROR: {exc}", file=sys.stderr)
        return None

    trace: dict = {
        "input": {
            "vendor_names": [e.vendor_name for e in extractions],
            "rfq_title": rfq.title,
            "extraction_summaries": [...],  # flag counts per vendor
        },
        "resolved_prompt": {
            "id": prompt_id, "version": prompt_version,
            "system_message": prompt_post.content,
            "human_message_preview": "..."[:500],
        },
        "raw_model_output": raw_result.model_dump(mode="json"),
        "clamp_step": clamp_report.model_dump(mode="json"),     # the verdict-clamp diff
        "clarification_step": {
            "flagged_fields_input": [...],
            "resolved_clarification_prompt": {...},
            "raw_clarification_output": [...],
        },
        "final_result": clamped_result.model_dump(mode="json"),
    }
    return trace
```

**`_write_markdown` pattern** (lines 108–164 of capture_traces.py — adapt for comparison trace sections: badge matrix, clamp diff table, line-item table):
```python
def _write_comparison_markdown(trace: dict, path: pathlib.Path) -> None:
    # Section: Input (vendor names, RFQ title, flag counts)
    # Section: Resolved Prompt (id, version)
    # Section: Clamp Step — THE RUBRIC TABLE
    #   | vendor | dimension | model_proposed | code_ceiling | clamped_to | ceiling_reason |
    # Section: Final Result (dimension matrix, vendor readiness, attention points)
    ...
```

**`main()` pattern** (lines 168–268 of capture_traces.py — load 3 committed vendor extractions + drive the trace):
```python
def main() -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    rfq = _load_rfq()
    extractions = [_load_extraction(f) for f in ["extraction_cheap.json", ...]]
    trace = _build_comparison_trace(extractions, rfq)
    if trace is None:
        sys.exit(1)
    # Validate the clamp_step has entries — the rubric requires >=1 downgrade
    if not trace["clamp_step"]["entries"]:
        print("WARNING: 0 verdict downgrades — trace won't demonstrate D-03 for the rubric",
              file=sys.stderr)
    _write_json(trace, TRACES_DIR / "comparison_trace_1.json")
    _write_markdown(trace, TRACES_DIR / "comparison_trace_1.md")
```

---

## Shared Patterns

### StrEnum definition
**Source:** `services/ai/schemas/envelope.py` lines 27–37 (`FlagStatus`)
**Apply to:** `ComparabilityVerdict` in `domain.py`
```python
from enum import StrEnum

class FlagStatus(StrEnum):
    present = "present"
    missing = "missing"
    # ...
```
Mirror exactly for `ComparabilityVerdict`.

### Pydantic model config
**Source:** `services/ai/schemas/domain.py` lines 34, 49, 82, 124 — every model in the file
**Apply to:** All new sub-models in `ComparisonResult` family
```python
model_config = ConfigDict(extra="forbid")
```

### SSE event validation before serialization
**Source:** `services/ai/api/app.py` lines 157–158
**Apply to:** All SSE emit calls in `comparison.py`
```python
# Validate every chunk through EventEnvelope before serializing —
# a malformed emit fails loudly here rather than streaming unchecked.
yield {"data": EventEnvelope(**chunk).model_dump_json()}
```

### Event taxonomy guard
**Source:** `services/ai/agents/extraction.py` line 103
**Apply to:** Every `_run_*_impl` function in `comparison.py`
```python
assert {"status", "result", "error"} <= set(EVENT_TYPES)
```

### `model_copy(update=...)` for immutability
**Source:** `services/ai/agents/extraction.py` line 202
**Apply to:** All places in `comparison.py` that need to update a pydantic object
```python
# W-R4: use model_copy(update=...) not attribute mutation
result = parsed.model_copy(update={"clamp_report": clamp_report})
```

### `default_factory=list` for list fields
**Source:** `services/ai/schemas/domain.py` lines 149, 157–160; `services/ai/grounding/report.py` line 42
**Apply to:** All `list[...]` fields in new sub-models
```python
attention_points: list[AttentionPoint] = pydantic_Field(default_factory=list)
```

### `# ponytail:` comment discipline
**Source:** Throughout `extraction.py`, `gate.py`, `domain.py`
**Apply to:** Any deliberate complexity kept in `comparison.py` or `domain.py`
```python
# ponytail: <why this complexity must exist despite ponytail's ladder>
```

### `# noqa: UP046` on Generic pydantic models
**Source:** `services/ai/schemas/envelope.py` lines 72, 86
**Apply to:** Any Generic BaseModel subclass added to `domain.py`
```python
class ClampEntry(BaseModel, Generic[T]):  # noqa: UP046
```
Note: `ComparisonResult` and its sub-models are NOT Generic (no `Field[T]` wrappers), so `# noqa: UP046` is not needed there.

---

## No Analog Found

All Phase 4 files have close analogs. No files require falling back to RESEARCH.md patterns only.

| File | Role | Closest Analog | Gap |
|---|---|---|---|
| `services/ai/agents/comparison.py` (verdict clamp logic) | utility | `services/ai/grounding/gate.py` | The gate traverses fields; the clamp takes computed ceilings and applies `min()`. Same structural shape (code decides, model proposes), different inputs. |
| `docs/traces/comparison_trace_*.json` | artifact | `docs/traces/trace_vendor_*.json` | Shape is close but adds `clamp_step` section; fully specified in RESEARCH.md Trace Design. |

---

## Metadata

**Analog search scope:**
- `services/ai/agents/` — extraction.py, _demo.py
- `services/ai/schemas/` — domain.py, envelope.py, events.py
- `services/ai/grounding/` — gate.py, report.py
- `services/ai/api/` — app.py
- `services/ai/prompts/` — extraction.v1.md, comparison.v1.md (stub), clarification.v1.md (stub)
- `services/ai/tests/` — test_extraction_agent.py, conftest_extraction.py
- `services/ai/scripts/` — capture_traces.py
- `services/ai/llm/` — factory.py

**Files scanned:** 15
**Pattern extraction date:** 2026-06-28
