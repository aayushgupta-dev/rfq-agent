# Phase 4: Comparison Agent - Research

**Researched:** 2026-06-28
**Domain:** LangGraph comparison agent, verdict clamping, pydantic schema design, SSE streaming
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01** — Hybrid comparability signal: badge matrix (vendor × 6 dimensions, each cell = `comparable | partially | not_comparable` + one-line reason) as headline; per-dimension narrative on drill-down; buyer attention-points panel.

**D-02** — `not-comparable` lives at comparison level only (new `ComparabilityVerdict` type), never bolted onto `FlagStatus` in `envelope.py`.

**D-03** — Model judges, code guards (clamp-to-ceiling). Model proposes per-dimension verdict + reason; code computes ceiling from `ExtractionResult` flag states and can ONLY downgrade.

**D-04** — Ceiling rule: `missing | unsupported` on any contributing field → caps at `not_comparable`; `unclear | conflicting` → caps at `partially`; all contributing fields `present` → allows `comparable`. Verdict = `min(model_verdict, code_ceiling)`.

**D-05** — Surface as-is, ZERO reconciliation. No currency conversion, no bundle splitting, no unit reconciliation. Flag non-equivalence ("bundled — not separable", "quoted EUR vs USD"). Honors §24 (no heavy normalization).

**D-06** — Two output surfaces: (1) 6-dimension comparability matrix; (2) 8-line-item × vendor offer table showing verbatim pricing/scope-coverage per item with missing/unclear/bundled badges.

**D-07** — Per-vendor readiness: qualitative descriptor + X/N dimension count. Framed as data-readiness indicator, equal weights, vendors NEVER sorted by readiness.

**D-08** — Attention triggers detected by code; model phrases the buyer-facing text only.

**D-09** — Clarification questions: separate gpt-5.4-mini call, code-seeded from flagged fields. Code collects flags deterministically; model phrases questions only.

**D-10** — One grounded question per flagged field, comparability-blockers first, grouped by vendor. No arbitrary cap. Generic questions rejected.

**D-11** — ≥1 comparison trace capturing the verdict-clamp diff (JSON + rendered MD under `docs/traces/`).

### Claude's Discretion

- **Call strategy**: single structured-output comparison call over all vendors at once; sectioned/per-dimension split is researched contingency for observed truncation only (YAGNI).
- **Dimension derivation**: mapping 6 dimensions to `ExtractionResult` fields.
- **Streaming**: reuse P3 SSE spine; `status` events (`align → comparability → compare → clarify → done`) + final grounded `result` event. Never stream pre-clamp verdict as final.
- **Exact `ComparisonResult` / sub-model field names**, field→dimension contribution map, and attention-trigger detection thresholds — within D-01..D-11.
- **Number of comparison traces** (≥1 required; more if richer set tells the story better).
- **Code-level test structure** — must assert: clamp only downgrades; no aggregation over missing; clarification set derived from code-collected flags; attention points trace to real trigger; vendors never reordered by readiness.

### Deferred Ideas (OUT OF SCOPE)

- Sectioned/per-dimension call — contingency only, not a separate scope item.
- Vendor Comparison screen / line-item table UI / in-app trace viewer — Phase 5.
- Weighted/numeric scoring, should-cost engine, currency reconciliation — permanently excluded (REQUIREMENTS Out of Scope; §24).
- Stateful clarification → re-extraction feedback loop — v2 (FLOW-01/FLOW-02).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMPARE-01 | Comparison agent compares vendors across 6 dimensions consuming only code-validated `ExtractionResult[]`, never raw vendor text. | `ExtractionResult` shape fully verified in codebase; grounding boundary enforced transitively by consuming only code-grounded objects. |
| COMPARE-02 | Comparability gate emits `comparable | partially | not_comparable` per dimension/line-item with reasons, before any scoring; never aggregates over a missing field. | D-03/D-04 clamp pattern verified against extraction.py analogue; pydantic `ComparabilityVerdict` StrEnum pattern confirmed. |
| COMPARE-03 | Comparison surfaces buyer attention points and generates clarification questions for flagged fields. | D-08/D-09 code-seeded trigger pattern; gpt-5.4-mini `clarification.v1.md` separate call pattern confirmed in factory.py. |
| COMPARE-04 | Light alignment of vendor offers to 8 RFQ line items; surfaces differences, no heavy normalization. | D-05/D-06; `line_item_id` already pinned at extraction time (LineItemExtraction); verbatim offer table pattern confirmed. |
| COMPARE-05 | Qualitative comparability/readiness signal per dimension, not a numeric leaderboard. | D-01/D-06/D-07; X/N count framed as data-readiness with explicit no-sort guard confirmed in D-07 guardrail. |
</phase_requirements>

---

## Summary

Phase 4 builds the comparison agent as a LangGraph `StateGraph` that consumes an array of code-validated `ExtractionResult` objects plus the original `RFQ`, and produces a `ComparisonResult`. The phase has three reliability keystones: (1) the verdict clamp (code computes a ceiling from `FlagStatus` values and can only downgrade the model's proposed comparability verdict, never upgrade it), (2) the attention-trigger detection (code decides what matters, model phrases it), and (3) the clarification seeding (code collects flagged fields, model phrases questions). These three patterns directly mirror the Phase 3 grounding gate discipline: code disproves/constrains the model, not the other way around.

The implementation has zero new external dependencies — every required capability is already in the installed package set (`langgraph`, `langchain`, `langchain-openai`, `pydantic`, `fastapi`, `sse-starlette`). The comparison graph mirrors the extraction graph's structure (`StateGraph(dict)`, `get_stream_writer()`, `astream(stream_mode="custom")`) and is consumed by the same SSE route pattern already established in `api/app.py`.

The biggest novel complexity relative to Phase 3 is the `ComparisonResult` schema design: the stub (2 fields) must be replaced with a full schema covering the badge matrix, the line-item offer table, per-vendor readiness, attention points, and clarification questions. This schema is the contract boundary for Phase 5; getting its shape right (field names, sub-model nesting, pydantic2ts compatibility) is the primary design decision the planner must nail in Wave 0.

**Primary recommendation:** Implement in 4 waves — (1) RED test stubs + `ComparisonResult` schema design, (2) schema flesh-out + codegen drift check, (3) comparison agent + comparability guard + POST `/compare/vendors` SSE route, (4) full prompts authored + comparison trace captured + clarification call wired.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Comparability verdict computation | API/Backend (Python) | — | Code-enforced ceiling rule; must never delegate verdict authority to the model or to the frontend |
| Model-proposed comparison call | API/Backend (Python) | — | Single structured-output call in a LangGraph node; stays server-side before SSE boundary |
| Clarification question generation | API/Backend (Python) | — | Separate gpt-5.4-mini call seeded by code-collected flags; server-side |
| Attention trigger detection | API/Backend (Python) | — | Pure code logic over flag states; no LLM involvement |
| `ComparisonResult` schema & TS contract | API/Backend → Shared Types | Frontend (consumer) | Pydantic source of truth; pydantic2ts generates TS; frontend reads only |
| SSE streaming of comparison progress | API/Backend (FastAPI) | Frontend (consumer) | `EventSourceResponse` route pattern mirrors `/extract/vendor` |
| Comparison trace capture | API/Backend (Python script) | docs/traces/ | Mirrors P3 `capture_traces.py` pattern; output committed to `docs/traces/` |
| Render comparability badge matrix | Frontend (Phase 5) | — | Phase 5 responsibility; Phase 4 only produces the data |
| Line-item offer table rendering | Frontend (Phase 5) | — | Phase 5 responsibility |

---

## Standard Stack

### Core (all already installed — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `langgraph` | ≥1.2.6 (pinned in pyproject.toml) | `StateGraph` for comparison graph | Same as extraction agent; `get_stream_writer()` + `astream(stream_mode="custom")` already proven |
| `langchain` | ≥0.3.0 | `ChatPromptTemplate`, `SystemMessage` | Same as extraction agent |
| `langchain-openai` | ≥1.3.3 | `init_chat_model` + `.with_structured_output(method="json_schema", include_raw=True)` | Same factory pattern |
| `pydantic` | ≥2.13.4 | `ComparisonResult` schema + sub-models + `model_copy` immutability | Already established contract; `extra="forbid"` on all models |
| `fastapi` + `sse-starlette` | Already pinned | `POST /compare/vendors` SSE route | `EventSourceResponse` pattern from `/extract/vendor` |

[VERIFIED: project pyproject.toml] — all packages confirmed in `services/ai/pyproject.toml`, no new dependencies required.

### Supporting (already available)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `rapidfuzz` | ≥3.14.5 | Not used directly in comparison | Only needed if comparison-level evidence re-grounding were added (it is not — grounding boundary held transitively) |
| `python-frontmatter` | ≥1.3.0 | `load("comparison")` / `load("clarification")` via prompt registry | Already used in extraction; same `registry.load()` call |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single all-vendor call | Per-dimension split calls | Split = lower truncation risk but loses cross-vendor reasoning in one context; start single, split only if truncation observed (D-DISCRETION) |
| `dict` state in `StateGraph(dict)` | `TypedDict` state class | TypedDict adds type safety but is more boilerplate; extraction graph uses `dict` with no problems; keep consistent |

**Installation:** None required. Zero new packages.

---

## Package Legitimacy Audit

> No new external packages are introduced in this phase. All dependencies are already pinned in `services/ai/pyproject.toml` and were verified during Phase 1–3.

| Package | Registry | Note |
|---------|----------|------|
| All dependencies | PyPI | Already installed and verified in prior phases |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
POST /compare/vendors
  (ExtractionResult[], RFQ)
          │
          ▼
  ┌──────────────────────────────────────────────────────┐
  │  comparison_graph (LangGraph StateGraph)              │
  │                                                       │
  │  ┌──────────┐    ┌────────────┐    ┌─────────────┐   │
  │  │  align   │───▶│ comparability│──▶│   compare   │   │
  │  │  node    │    │   node     │    │    node     │   │
  │  └──────────┘    └────────────┘    └─────────────┘   │
  │      │                │                  │            │
  │  emit status:      emit status:       emit status:    │
  │  "aligning"       "comparability"    "comparing"     │
  │                       │                  │            │
  │              code ceiling             code guards     │
  │              computed here            applied here    │
  │                                          │            │
  │                                   ┌──────────────┐   │
  │                                   │   clarify    │   │
  │                                   │    node      │   │
  │                                   └──────────────┘   │
  │                                          │            │
  │                                   emit status:        │
  │                                   "clarifying"        │
  │                                          │            │
  │                                   emit result:        │
  │                                   ComparisonResult    │
  │                                   + clamp_report      │
  └──────────────────────────────────────────────────────┘
          │
          ▼
   SSE stream to client
   (status → status → status → status → result → done)
```

**Data flow:**
- `align` node: validates inputs (all `ExtractionResult[]` are `ExtractionResult` instances, not raw text); emits `status` event.
- `comparability` node: walks all `ExtractionResult` fields per dimension, computes code ceiling per vendor per dimension using `FlagStatus` values; stores ceilings in state.
- `compare` node: invokes `get_llm("reasoning").with_structured_output(ComparisonResult, method="json_schema", include_raw=True)` with all extractions + RFQ in context; applies clamp (`min(model_verdict, code_ceiling)`) per dimension per vendor; builds `clamp_report`; emits `result`.
- `clarify` node: code collects all flagged fields from `ExtractionResult[]` deterministically; invokes `get_llm("cheap").with_structured_output(ClarificationSet, method="json_schema")` with code-seeded list; appends clarifications to result payload.

**Guard order:** Comparability ceiling computed BEFORE model call (so it is available instantly for clamping). Clamp applied BEFORE result event emitted. Clarification seeding collected from the already-grounded `ExtractionResult[]` — never from the model's comparison output.

### Recommended Project Structure

```
services/ai/
├── agents/
│   └── comparison.py          # ComparisonGraph (mirrors extraction.py pattern)
├── schemas/
│   └── domain.py              # ComparisonResult fleshed out (stub → real)
├── prompts/
│   ├── comparison.v1.md       # TODO stub → full comparison prompt (gpt-5.4)
│   └── clarification.v1.md   # TODO stub → full clarification prompt (gpt-5.4-mini)
├── api/
│   └── app.py                 # POST /compare/vendors SSE route added
├── tests/
│   └── test_comparison_agent.py   # RED stubs → GREEN
└── scripts/
    └── capture_comparison_trace.py  # mirrors capture_traces.py from P3
docs/traces/
    comparison_trace_1.json        # ≥1 trace with clamp diff
    comparison_trace_1.md          # rendered markdown
```

### Pattern 1: Verdict Clamp (the headline reliability move)

**What:** Code computes a deterministic ceiling from `FlagStatus` values in `ExtractionResult` fields; the model's proposed verdict is `min(model_verdict, code_ceiling)`. Code can only downgrade, never upgrade.

**When to use:** Applied per dimension per vendor, immediately after the model returns its structured output, before the result SSE event is emitted.

**Ceiling computation (D-04):**

```python
# Source: codebase — gate.py FlagStatus + D-04 decision
from schemas.envelope import FlagStatus

_VERDICT_ORDER = {"comparable": 2, "partially": 1, "not_comparable": 0}

def _ceiling_for_flags(flag_statuses: list[FlagStatus]) -> str:
    """Compute comparability ceiling from the FlagStatus values of contributing fields.

    missing | unsupported on ANY field → not_comparable
    unclear | conflicting on ANY field → at most partially
    all present → comparable allowed
    """
    for s in flag_statuses:
        if s in (FlagStatus.missing, FlagStatus.unsupported):
            return "not_comparable"
    for s in flag_statuses:
        if s in (FlagStatus.unclear, FlagStatus.conflicting):
            return "partially"
    return "comparable"

def clamp_verdict(model_verdict: str, code_ceiling: str) -> str:
    """Return min(model_verdict, code_ceiling) in the ordering comparable > partially > not_comparable."""
    return model_verdict if _VERDICT_ORDER[model_verdict] <= _VERDICT_ORDER[code_ceiling] else code_ceiling
```

[ASSUMED] — exact function signatures are Claude's Discretion; the logic is derived from D-04.

### Pattern 2: Attention Trigger Detection (D-08)

**What:** Code scans `ExtractionResult[]` for trigger conditions; model phrases the buyer-facing text for each triggered condition.

**Trigger types to implement:**
- Comparability blocker: any dimension with `not_comparable` for ≥1 vendor
- Missing critical pricing: any vendor has `pricing.status in (missing, unsupported)` for ≥1 line item
- Cross-vendor conflict: same field `conflicting` across vendors (e.g. two vendors have conflicting timelines)
- Weak/absent compliance: all vendor `compliance_points` lists empty or all `missing`

```python
# Source: derived from D-08 + ExtractionResult field shapes [ASSUMED]
def detect_attention_triggers(extractions: list[ExtractionResult], matrix: ComparabilityMatrix) -> list[AttentionTrigger]:
    triggers = []
    # comparability blockers
    for dim, vendor_verdicts in matrix.items():
        if any(v.verdict == "not_comparable" for v in vendor_verdicts.values()):
            triggers.append(AttentionTrigger(type="comparability_blocker", dimension=dim, ...))
    # missing critical pricing
    for ext in extractions:
        for li in ext.line_items:
            if li.pricing.status in (FlagStatus.missing, FlagStatus.unsupported):
                triggers.append(AttentionTrigger(type="missing_pricing", vendor=ext.vendor_name, line_item=li.line_item_id, ...))
    return triggers
```

### Pattern 3: Clarification Seeding (D-09)

**What:** Code deterministically collects all `(vendor_name, field_path, flag_status)` tuples for fields where `status in (missing, unclear, conflicting, unsupported)`; passes this list to the gpt-5.4-mini clarification prompt as structured input.

**Key constraint:** The model receives ONLY the code-collected list. It cannot add new items to the clarification set — it can only phrase questions for the items it received.

```python
# Source: derived from D-09 + ExtractionResult field shapes [ASSUMED]
def collect_flagged_fields(extractions: list[ExtractionResult]) -> list[FlaggedField]:
    """Walk every Field[T] in every ExtractionResult; collect non-present statuses."""
    flagged = []
    for ext in extractions:
        # Reuse the _walk_and_ground pattern (gate.py) structurally — but read-only here
        _collect_flags_recursive(ext, ext.vendor_name, "", flagged)
    # Order: comparability-blockers first (missing/unsupported), then unclear/conflicting
    return sorted(flagged, key=lambda f: (0 if f.status in ("missing", "unsupported") else 1))
```

### Pattern 4: `ComparisonResult` Schema — New Types

**What:** Three new comparison-level types that must NOT appear in `envelope.py` (D-02).

```python
# Source: derived from D-01..D-07 decisions [ASSUMED - exact field names are Claude's Discretion]
from enum import StrEnum

class ComparabilityVerdict(StrEnum):
    """Comparison-level verdict — NOT a field-level FlagStatus (D-02)."""
    comparable = "comparable"
    partially = "partially"
    not_comparable = "not_comparable"

class DimensionVerdict(BaseModel):
    """Per-vendor per-dimension verdict cell (badge matrix cell, D-01)."""
    model_config = ConfigDict(extra="forbid")
    vendor_name: str
    verdict: ComparabilityVerdict    # clamped verdict (model → code ceiling)
    reason: str                      # one-line reason (model-authored, code-permitted)
    model_proposed: ComparabilityVerdict  # pre-clamp verdict (for trace diff, D-11)

class DimensionComparison(BaseModel):
    """One row of the badge matrix (D-01/D-06)."""
    model_config = ConfigDict(extra="forbid")
    dimension: str                   # "technical" | "commercial" | "scope" | "timeline" | "compliance" | "risk"
    verdicts: list[DimensionVerdict] # one per vendor
    narrative: str                   # per-dimension synthesis (model-authored, drill-down)

class LineItemOffer(BaseModel):
    """One cell of the 8×vendor offer table (D-06)."""
    model_config = ConfigDict(extra="forbid")
    line_item_id: str
    line_item_name: str
    vendor_name: str
    pricing_verbatim: str | None     # value from ExtractionResult.line_items[*].pricing.value
    pricing_status: str              # FlagStatus value string
    scope_verbatim: str | None       # value from ExtractionResult.line_items[*].scope_coverage.value
    scope_status: str                # FlagStatus value string
    non_equivalence_flag: str | None # "bundled — not separable", "quoted EUR vs USD", etc.

class VendorReadiness(BaseModel):
    """Per-vendor qualitative readiness descriptor (D-07)."""
    model_config = ConfigDict(extra="forbid")
    vendor_name: str
    comparable_count: int            # X of N dimensions currently comparable
    total_dimensions: int            # N (always 6)
    descriptor: str                  # qualitative text e.g. "4 of 6 dimensions comparable; blocked on commercial, compliance"
    # ponytail: no sort key, no rank, no score — D-07 guardrail

class AttentionPoint(BaseModel):
    """One buyer attention point (D-08): code-triggered, model-phrased."""
    model_config = ConfigDict(extra="forbid")
    trigger_type: str                # "comparability_blocker" | "missing_pricing" | "cross_vendor_conflict" | "compliance_gap"
    summary: str                     # buyer-facing phrasing (model-authored)
    vendors_affected: list[str]
    dimension_or_field: str | None

class ClarificationQuestion(BaseModel):
    """One clarification question per flagged field (D-09/D-10)."""
    model_config = ConfigDict(extra="forbid")
    vendor_name: str
    field_path: str                  # e.g. "line_items[2].pricing"
    flag_status: str                 # the triggering status
    question: str                    # model-phrased, specific, non-generic
    why_needed: str                  # rationale for the buyer

class ClampReport(BaseModel):
    """Records every verdict downgrade for the D-11 trace diff."""
    model_config = ConfigDict(extra="forbid")
    entries: list[ClampEntry]

class ClampEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_name: str
    dimension: str
    model_proposed: str
    code_ceiling: str
    clamped_to: str
    ceiling_reason: str              # which field statuses triggered the ceiling

class ComparisonResult(BaseModel):
    """Full comparison output (Phase 4 — replaces 2-field stub)."""
    model_config = ConfigDict(extra="forbid")
    vendor_names: list[str]          # input order preserved, never sorted
    dimensions: list[DimensionComparison]     # 6 entries
    line_item_offers: list[LineItemOffer]     # 8 × N vendors entries
    vendor_readiness: list[VendorReadiness]   # N entries, input order preserved
    attention_points: list[AttentionPoint]
    clarification_questions: list[ClarificationQuestion]
```

[ASSUMED] — exact field names are Claude's Discretion per CONTEXT.md. The shapes above satisfy all D-01..D-11 constraints and the pydantic2ts compatibility requirement (no `dict[str, Field]`, Generic types with `# noqa: UP046` if needed, `extra="forbid"` everywhere).

**pydantic2ts compatibility note:** `ComparisonResult` uses only `list[BaseModel]` and `list[str]` — no `Generic[T]` — so `# noqa: UP046` is not needed here. If any sub-model becomes Generic, add it.

### Pattern 5: SSE Node Structure (mirrors extraction.py exactly)

**What:** Multi-node graph with one SSE writer per node; all nodes use the same `_run_*_impl(state, emit)` split for testability.

```python
# Source: services/ai/agents/extraction.py [VERIFIED: codebase]
def _align_node(state: dict) -> dict:
    w = get_stream_writer()
    return _run_align_impl(state, w)

def _comparability_node(state: dict) -> dict:
    w = get_stream_writer()
    return _run_comparability_impl(state, w)

# ... compare_node, clarify_node same pattern
```

**SSE event sequence for comparison:**
```
status: {"message": "validating inputs", "phase": "align"}
status: {"message": "computing comparability ceilings", "phase": "comparability"}
status: {"message": "calling comparison model", "phase": "compare"}
status: {"message": "generating clarification questions", "phase": "clarify"}
result: {**comparison_result.model_dump(), "clamp_report": ..., "clarification_questions": ...}
done: {}
```

**Guard:** Never emit a `result` event before the clamp has run. The `compare` node runs the model call, applies the clamp, and emits the result in that order — within the same `try/except` block (same `CR-01` discipline as extraction).

### Pattern 6: Comparison Prompt Design (the 30%-grade artifact)

**What:** `comparison.v1.md` must follow the extraction prompt's structure — frontmatter + explicit contract sections + few-shot examples — adapted for multi-vendor side-by-side reasoning.

**Structural requirements derived from extraction.v1.md template:**
1. **Role framing**: "You are a procurement comparison agent" + evidence contract (you cite only ExtractionResult facts, never add new claims).
2. **Verdict definitions**: explicitly define `comparable | partially | not_comparable` with the same precision as the four flag states in extraction.
3. **Comparability-first instruction**: establish comparability per dimension BEFORE any narrative. State: "If any vendor has status=missing or status=unsupported on a contributing field, that dimension is NOT COMPARABLE for that vendor — state this explicitly."
4. **No-normalization instruction**: "Do NOT convert currencies, split bundles, or infer per-item prices from bundled totals. Quote verbatim. Flag non-equivalence."
5. **Humility instruction** (mirrors extraction): "A `not_comparable` that prevents a misleading comparison is better than a `comparable` built on incomplete data."
6. **Attention points section**: instruct model to draft buyer-facing text ONLY for trigger conditions provided in the input (code-supplied list).
7. **Output format**: `ComparisonResult` JSON schema, same JSON-only instruction.
8. **Few-shot examples**: ≥3 examples covering comparable case, partially case (missing field → downgraded), not_comparable case (bundled pricing prevents comparison).

**Clarification prompt (`clarification.v1.md`) design:**
- Input: code-supplied list of `{vendor_name, field_path, flag_status, field_context}` items.
- Instruction: one question per item, exactly. No invented items. Name the vendor, line item, and exact ambiguity.
- Reject generic questions ("Please clarify pricing") — require specificity ("Vendor X's TVC Production pricing is listed as 'included in bundle' — please provide the standalone cost for this service").
- Order: comparability-blockers first (missing/unsupported), then unclear/conflicting.

### Anti-Patterns to Avoid

- **Streaming pre-clamp verdicts as final:** never emit a `result` event before the clamp has been applied. The model's raw verdict is internal state only until clamped. [Violates D-03 and evidence-over-assertion]
- **Using `dict[str, X]` shapes in `ComparisonResult`:** pydantic2ts cannot generate accurate TS types for `dict[str, Model]`. Use `list[Model]` with a `vendor_name` key field instead. [Violates PLAT-02 contract discipline]
- **Sorting vendors by readiness:** `vendor_readiness` list must preserve input order. Any sort key on `VendorReadiness` is the leaderboard §24 forbids. [Violates D-07]
- **Model-inventing the clarification set:** the model receives ONLY the code-collected flagged fields. If the prompt allows the model to generate questions for fields not in the input list, that is the equivalent of the grounding gate allowing the model to self-attest evidence. [Violates D-09]
- **Aggregating over missing fields:** never compute a dimension verdict of `comparable` or `partially` when any contributing field is `missing` — the ceiling rule enforces `not_comparable`. Test must prove a fabricated `comparable` verdict over a missing field becomes `not_comparable` after clamping. [Violates COMPARE-02]
- **Adding `not_comparable` to `FlagStatus` in `envelope.py`:** this is WR-01 resolved by D-02. `ComparabilityVerdict` is a new separate StrEnum in `domain.py`. [Violates D-02]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured output parsing | Custom JSON parser | `.with_structured_output(ComparisonResult, method="json_schema", include_raw=True)` | Handles schema coercion, validation errors, refusal detection — same as extraction |
| Truncation detection | Custom finish_reason check | `LengthFinishReasonError` catch (same as extraction.py) | LangChain raises this reliably; include_raw=True covers the parsing_error path |
| SSE streaming | Custom asyncio writer | `get_stream_writer()` + `astream(stream_mode="custom")` + `EventSourceResponse` | Already proven in extraction; do not reinvent |
| Model access | Direct OpenAI client | `get_llm("reasoning")` / `get_llm("cheap")` from `factory.py` | Tier discipline (never gpt-5.5), env-var model IDs, single point of control |
| Field flag walking | Custom reflection | `_walk_and_ground` pattern from `gate.py` (read-only variant for flag collection) | Already traverses all `Field[T]` shapes in `ExtractionResult`; adapt for flag collection |
| TS type generation | Manual type mirroring | `pydantic2ts` + drift-check test (PLAT-02) | One-command regeneration; drift-check test catches schema/TS divergence |

**Key insight:** Every hard problem in this phase (structured output, SSE, grounding discipline, pydantic→TS) was already solved in Phases 1–3. The comparison agent is a configuration of proven primitives, not new infrastructure.

---

## Common Pitfalls

### Pitfall 1: Streaming a Pre-Clamp Result

**What goes wrong:** The `compare` node emits a `result` event with model-proposed verdicts before the clamp runs, then emits a second event with clamped verdicts — or the clamp runs in a separate node after the `result` event.

**Why it happens:** Treating the clamp as a post-processing step rather than part of the same success path in the `compare` node.

**How to avoid:** The `compare` node's success path, inside the same `try/except` block, runs: (1) model call, (2) clamp, (3) emit result. No result event leaves the node until (2) is complete. Mirrors `CR-01` from extraction.py — everything on the success path is inside the try.

**Warning signs:** The `clamp_report` has entries but the `result` payload's verdicts don't reflect the clamps. Test: inject a model response with `comparable` verdict over a vendor with `missing` pricing; assert emitted result has `not_comparable`.

### Pitfall 2: `ComparisonResult` Schema Using `dict[str, Model]`

**What goes wrong:** Designing the schema as `dimensions: dict[str, DimensionComparison]` (keyed by dimension name) or `vendor_results: dict[str, VendorResult]`. pydantic2ts generates `Record<string, DimensionComparison>` for these, which loses type safety in the UI and can cause TS drift.

**How to avoid:** Use `list[DimensionComparison]` with `dimension: str` as a field on each model. Same pattern as `list[LineItemExtraction]` in `ExtractionResult`. The drift-check test (test_codegen_drift.py) will catch this if it generates a `Record<>` type when a typed array was expected — but prevention is cheaper.

**Warning signs:** pydantic2ts generates `Record<string, ...>` in `packages/shared-types/`. The Phase 5 UI developer has no strong typing for dimension lookup.

### Pitfall 3: Clarification Prompt Allows Model to Invent Flagged Fields

**What goes wrong:** The `clarification.v1.md` prompt is underspecified and the model generates questions for fields it "noticed" in the comparison output, beyond the code-supplied flagged field list.

**Why it happens:** The prompt says "generate clarification questions for any unclear information" rather than "generate questions ONLY for the items in the provided list."

**How to avoid:** The prompt must state explicitly: "You are given a list of `N` flagged fields. Generate exactly one question per item. Do not add questions for fields not in this list. The list is exhaustive." Test: inject a 2-item flagged field list; assert the clarification output has exactly 2 questions.

### Pitfall 4: LangGraph `include_raw=True` and the Refusal Path

**What goes wrong:** Refusals don't raise an exception; they populate `additional_kwargs["refusal"]` on the raw `AIMessage`. If the `compare` node doesn't check this, a refusal silently becomes `parsed=None` → `parsing_error` detection path → wrong error code.

**How to avoid:** Same pattern as extraction.py: check `raw_msg.additional_kwargs.get("refusal")` first, before checking `parsed is None`. The refusal check must precede the `parsing_error` check.

**Warning signs:** Refusal tests report `extraction_parse_error` instead of `comparison_refused`. Mirror test 5 from `test_extraction_agent.py` for comparison.

### Pitfall 5: `ComparisonResult` Naming Collisions in Result Payload

**What goes wrong:** `ComparisonResult.model_dump()` contains a key named `clamp_report` or `clarification_questions`, and the code tries to spread it + add those keys as siblings (like extraction.py's `downgrade_report` assertion).

**How to avoid:** Either (a) include `clamp_report` as a field ON `ComparisonResult` itself (simpler — no spread needed), or (b) use the same assertion guard extraction.py uses: `assert "clamp_report" not in grounded_payload`. Option (a) is cleaner for comparison because the clamp report is part of the comparison result semantics, not a separate grounding artifact.

**Recommendation:** Include `clamp_report: ClampReport` as a field on `ComparisonResult` directly. Then the result SSE payload is simply `comparison_result.model_dump()` with no spread needed.

### Pitfall 6: `VendorReadiness` Sorted by `comparable_count`

**What goes wrong:** A downstream serializer or the template sorts `vendor_readiness` by `comparable_count` descending — producing an implicit ranking. This is the leaderboard §24 forbids.

**How to avoid:** The `vendor_readiness` list is built in input order (same order as `extractions` argument). Tests assert that after round-tripping through JSON serialization and the SSE boundary, order is preserved. Never add a `rank` or `score` field.

### Pitfall 7: Multi-Vendor Context Window Truncation

**What goes wrong:** With 3+ detailed `ExtractionResult` objects + the RFQ in a single call, the input can exceed the model's context budget, triggering `LengthFinishReasonError` on the INPUT side (not just output truncation).

**How to avoid:** The comparison prompt's human turn should include only the fields actually needed for comparison (not the raw_text, which is never in `ExtractionResult` anyway). `ExtractionResult` already strips raw text — only structured fields are sent. For 3 vendors with 8 line items each, the JSON payload is manageable (~8-15K tokens). If truncation is observed on live runs, implement the sectioned/per-dimension contingency (D-DISCRETION).

**Warning signs:** `LengthFinishReasonError` on the `compare` node's model call even with short vendor responses. Check prompt human-turn size.

---

## Code Examples

### LangGraph Multi-Node Graph (extraction.py pattern — apply verbatim)

```python
# Source: services/ai/agents/extraction.py [VERIFIED: codebase]
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
```

### SSE Route Pattern (app.py — apply verbatim)

```python
# Source: services/ai/api/app.py [VERIFIED: codebase]
class ComparisonRequest(BaseModel):
    extractions: list[ExtractionResult]
    rfq: RFQ

@app.post("/compare/vendors")
async def compare_vendors(req: ComparisonRequest) -> EventSourceResponse:
    async def _generate():
        async for chunk in comparison_graph.astream(
            {"extractions": req.extractions, "rfq": req.rfq},
            stream_mode="custom",
        ):
            yield {"data": EventEnvelope(**chunk).model_dump_json()}
        yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}
    return EventSourceResponse(_generate())
```

### Structured Output with include_raw=True (extraction.py pattern)

```python
# Source: services/ai/agents/extraction.py [VERIFIED: codebase]
_llm_with_raw = get_llm("reasoning").with_structured_output(
    ComparisonResult, method="json_schema", include_raw=True
)
```

### Prompt Loading (registry.py pattern)

```python
# Source: services/ai/prompts/registry.py [VERIFIED: codebase]
from prompts.registry import load

_comparison_post = load("comparison")
_clarification_post = load("clarification")
_comparison_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=_comparison_post.content),
    ("human", "{input}"),
])
```

### pydantic2ts Drift Check (test_codegen_drift.py — same test catches new schema)

```python
# Source: services/ai/tests/test_codegen_drift.py [VERIFIED: codebase — test already exists]
# After ComparisonResult is fleshed out, running `pydantic2ts` and checking git diff
# on packages/shared-types/ must show the new ComparisonResult TS type.
# The existing drift-check test covers PLAT-02 automatically.
```

---

## Field → Dimension Contribution Map

The 6 comparison dimensions and their contributing `ExtractionResult` fields (Claude's Discretion to specify precisely; this is the research recommendation):

| Dimension | Contributing ExtractionResult Fields | Ceiling Trigger Fields |
|-----------|--------------------------------------|------------------------|
| **technical** | `scope_summary`, `line_items[*].scope_coverage` | Any scope field `missing/unsupported` for a vendor |
| **commercial** | `pricing_structure`, `total_price`, `commercial_terms`, `line_items[*].pricing` | Any pricing field `missing/unsupported` |
| **scope** | `line_items[*].scope_coverage` (per-item completeness) | ≥1 line item `scope_coverage.status = missing` |
| **timeline** | `timeline` | `timeline.status in (missing, unsupported)` |
| **compliance** | `compliance_points` (list) | `compliance_points` is empty list OR all entries `missing` |
| **risk** | `risks` (list) | No hard ceiling — empty list = no risks claimed (note: not necessarily a problem, depends on RFQ) |

**Note on risk dimension:** An empty `risks[]` list is not automatically a ceiling blocker (a vendor may genuinely have no risk disclosures). The model judges risk comparability; code only caps if there is direct evidence of non-equivalence (e.g., one vendor has 5 risk entries, another has 0 — flag as `partially`, not `not_comparable`, unless a specific required compliance risk is missing).

[ASSUMED] — exact field→dimension mapping is Claude's Discretion per CONTEXT.md. The above is the research recommendation; planner may adjust.

---

## Light Alignment vs. Heavy Normalization — The Concrete Boundary (D-05)

**ALLOWED (light alignment, D-05):**
- Show each vendor's verbatim `line_items[*].pricing.value` and `scope_coverage.value` side by side in the offer table, keyed by `line_item_id` (already pinned at extraction time by Phase 3).
- Show the `pricing_status` and `scope_status` badges (present/missing/unclear/conflicting) per cell.
- Flag non-equivalence in a `non_equivalence_flag` field: "bundled — not separable", "quoted EUR vs USD", "TBC pending scope confirmation".
- Quote the vendor's verbatim `pricing_structure` statement ("All services quoted as a single retainer of AUD 2.1M") next to the line-item table so the buyer sees why per-item cells are `unclear`.

**FORBIDDEN (heavy normalization, §24):**
- Splitting a bundled price ("AUD 2.1M for all services") into per-item amounts (that is fabrication).
- Converting currency ("EUR 500,000 → USD 545,000") — the exchange rate is not in the vendor's response.
- Computing unit prices ("USD 110,000 for 8 weeks = USD 13,750/week") — not stated by the vendor.
- Summing per-item prices to verify or challenge a grand total.
- Assigning a line item price from a "similar" vendor's price when a vendor is silent.

**The test for the boundary:** Can the buyer trace the value in the comparison directly to a verbatim quote in the vendor's proposal? If yes → light alignment. If the buyer cannot find the exact value in the vendor text → forbidden normalization.

---

## Trace Design (D-11)

The comparison trace must capture the verdict-clamp diff — this is the literal "code disproves the model" proof for the comparison level.

**Required trace structure (mirrors P3 trace JSON shape):**

```json
{
  "input": {
    "vendor_names": ["thorough-but-pricey", "cheap-but-incomplete", "polished-fluff"],
    "rfq_title": "...",
    "extraction_summaries": [{"vendor_name": "...", "flag_counts": {"present": N, "missing": N, ...}}]
  },
  "resolved_prompt": {
    "id": "comparison",
    "version": 1,
    "system_message": "...",
    "human_message_preview": "..."
  },
  "raw_model_output": {
    "dimensions": [
      {
        "dimension": "commercial",
        "verdicts": [
          {"vendor_name": "cheap-but-incomplete", "verdict": "comparable", "reason": "..."}
        ]
      }
    ]
  },
  "clamp_step": {
    "entries": [
      {
        "vendor_name": "cheap-but-incomplete",
        "dimension": "commercial",
        "model_proposed": "comparable",
        "code_ceiling": "not_comparable",
        "clamped_to": "not_comparable",
        "ceiling_reason": "line_items[2].pricing.status = missing"
      }
    ]
  },
  "clarification_step": {
    "flagged_fields_input": [...],
    "resolved_clarification_prompt": {...},
    "raw_clarification_output": [...]
  },
  "final_result": {
    "dimensions": [...],
    "vendor_readiness": [...],
    "attention_points": [...],
    "clarification_questions": [...]
  }
}
```

**Compelling trace guidance (carry-forward from P3 UAT):** The trace must show at least one meaningful downgrade — where the model proposed `comparable` or `partially` and code clamped it to `not_comparable`. Use the `cheap-but-incomplete` vendor (known to have missing pricing on several line items from P2 mess spec) as the primary subject of the clamp demonstration. The `clamp_step.entries` section IS the rubric story for the comparison agent.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Numeric vendor scoring | Qualitative comparability signal + X/N count | §21 + §24 of assignment | Avoids misleading buyers with fabricated precision |
| Heavy normalization (currency conversion, bundle splitting) | Surface verbatim + flag non-equivalence | §24 | Prevents fabricated values; differentiator on rubric |
| Model-authored comparability verdicts | Model proposes, code clamps | P2 grounding gate discipline → P4 | Code authority over reliability-critical decisions |
| SSE buffer-and-return | Streaming progress events | Phase 1 PLAT-04 | Required; never buffer-and-return long agent work |

**Deprecated/outdated:**
- `ComparisonResult` stub (2 fields: `vendor_count`, `comparable`) — replaced entirely in this phase; the existing stub is a placeholder that must be removed.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact `ComparisonResult` sub-model field names (e.g. `DimensionVerdict`, `DimensionComparison`) | Code Examples / Pattern 4 | Schema regeneration needed + Phase 5 TS contract changes; low risk since Phase 5 hasn't started |
| A2 | `risk` dimension has no hard ceiling trigger (empty `risks[]` not auto-blocking) | Field → Dimension Map | Could miss a real comparability gap; planner can tighten to `partially` if empty risks is considered non-comparable |
| A3 | Single all-vendor call is sufficient without truncation for 3 vendors | Standard Stack | If truncation observed, implement sectioned contingency (D-DISCRETION); not a blocker — the fallback is defined |
| A4 | `clamp_report` included as a field ON `ComparisonResult` (not spread alongside it) | Pitfall 5 | If placed outside `ComparisonResult`, it needs the same collision assertion extraction.py uses; either approach works |
| A5 | The existing `test_codegen_drift.py` will catch `ComparisonResult` TS drift automatically | Don't Hand-Roll | True only if the test runs codegen against the full `schemas/__init__.py` — verified in Phase 1 that it does (PLAT-02) |

**If this table is empty:** Not empty — the schema field names are Claude's Discretion and marked [ASSUMED].

---

## Open Questions

1. **Should `ClampReport` be a field inside `ComparisonResult` or a sibling key in the result payload?**
   - What we know: extraction.py uses a sibling key pattern (`downgrade_report` spread alongside `ExtractionResult.model_dump()`) with an assertion guard for collision.
   - What's unclear: for comparison, the clamp report is more semantically part of the comparison result than the grounding report is part of the extraction result. Including it as a field simplifies serialization.
   - Recommendation: include as a field on `ComparisonResult`. Simpler. The Phase 5 trace viewer gets it for free.

2. **Should `ComparisonRequest` have payload size validation like `ExtractionRequest`?**
   - What we know: `ExtractionRequest` validates `raw_text` ≤ 200K chars and total ≤ 500K. `ExtractionResult` contains no raw text — it is already structured.
   - Recommendation: add a simpler guard (e.g. max 5 vendors, `extractions` list length checked) but no character count needed since `ExtractionResult` is already bounded.

---

## Environment Availability

> Step 2.6: SKIPPED for new packages. All external dependencies are already installed and verified in Phases 1–3. The OpenAI API key and model access (gpt-5.4 / gpt-5.4-mini) were confirmed live in Phase 1 (PLAT-03). The `verify_access()` startup gate in `app.py` will confirm access again at server start.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `langgraph` | Comparison graph | ✓ | ≥1.2.6 (pinned) | — |
| `langchain-openai` | Structured output | ✓ | ≥1.3.3 (pinned) | — |
| `pydantic` | Schema | ✓ | ≥2.13.4 (pinned) | — |
| `fastapi` + `sse-starlette` | SSE route | ✓ | Pinned | — |
| OpenAI gpt-5.4 / gpt-5.4-mini | Model calls | ✓ | Confirmed Phase 1 | — |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥9.1.1 |
| Config file | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_comparison_agent.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMPARE-01 | Comparison consumes only `ExtractionResult[]`, never raw text | unit | `uv run pytest tests/test_comparison_agent.py::test_input_validation -x` | ❌ Wave 0 |
| COMPARE-02 (clamp) | Model `comparable` over missing field → clamped to `not_comparable` | unit | `uv run pytest tests/test_comparison_agent.py::test_clamp_only_downgrades -x` | ❌ Wave 0 |
| COMPARE-02 (no-agg) | Agent never aggregates over a field a vendor is missing | unit | `uv run pytest tests/test_comparison_agent.py::test_no_aggregation_over_missing -x` | ❌ Wave 0 |
| COMPARE-03 (attn) | Attention points trace to a real trigger (no fabricated triggers) | unit | `uv run pytest tests/test_comparison_agent.py::test_attention_points_are_triggered -x` | ❌ Wave 0 |
| COMPARE-03 (clarif) | Clarification set derived from code-collected flags, not model-invented | unit | `uv run pytest tests/test_comparison_agent.py::test_clarification_seeded_by_code -x` | ❌ Wave 0 |
| COMPARE-04 | Line-item offer table shows verbatim values; non-equivalence flagged | unit | `uv run pytest tests/test_comparison_agent.py::test_offer_table_verbatim -x` | ❌ Wave 0 |
| COMPARE-05 | Vendors never sorted by readiness; `vendor_readiness` preserves input order | unit | `uv run pytest tests/test_comparison_agent.py::test_vendor_order_preserved -x` | ❌ Wave 0 |
| COMPARE-05 | No numeric score or rank field on `ComparisonResult` | unit (schema) | `uv run pytest tests/test_comparison_agent.py::test_no_numeric_score -x` | ❌ Wave 0 |
| PLAT-02 | `ComparisonResult` TS types regenerate cleanly (no drift) | integration | `uv run pytest tests/test_codegen_drift.py -x` | ✅ (exists, will catch new schema) |
| PROMPT-03 | ≥1 comparison trace committed under `docs/traces/` with clamp diff | file assertion | `uv run pytest tests/test_comparison_agent.py::test_comparison_traces_committed -x` | ❌ Wave 0 |
| SSE taxonomy | All SSE event types from `/compare/vendors` are in `EVENT_TYPES` | integration | `uv run pytest tests/test_comparison_agent.py::test_comparison_sse_taxonomy -x` | ❌ Wave 0 |
| EXTRACT-05 analog | Truncation → safe error event; refusal → safe error event | unit | `uv run pytest tests/test_comparison_agent.py::test_truncation_error_event tests/test_comparison_agent.py::test_refusal_error_event -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_comparison_agent.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `services/ai/tests/test_comparison_agent.py` — covers all COMPARE-01..05 + SSE + trace assertions (RED stubs)
- [ ] `services/ai/tests/conftest_comparison.py` (optional) — shared builders for `ComparisonResult` / `ExtractionResult` test fixtures if needed

*(Existing test infrastructure: pytest configured, `conftest_extraction.py` helper pattern established, `test_codegen_drift.py` already covers PLAT-02 for any schema change.)*

---

## Security Domain

> `security_enforcement` is not explicitly set to `false` in config.json — treating as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in prototype (single-buyer, per REQUIREMENTS Out of Scope) |
| V3 Session Management | No | Stateless API |
| V4 Access Control | No | Single-buyer prototype |
| V5 Input Validation | Yes | `ComparisonRequest` validated by pydantic (`extra="forbid"`); vendor list length guard; `ExtractionResult` already passed the grounding gate |
| V6 Cryptography | No | No secrets in comparison payloads |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Model-fabricated verdicts elevated to `comparable` | Tampering | Verdict clamp (D-03/D-04) — code ceiling, not LLM self-attestation |
| Model-invented clarification questions (fields not flagged by code) | Tampering | Code-seeded input list to clarification prompt (D-09); count assertion in tests |
| Oversized `ExtractionResult[]` payload causing server OOM | Denial of Service | `ComparisonRequest` vendor count guard + pydantic `extra="forbid"` |
| Path traversal via `vendor_name` or `source_id` values | Tampering | No file-system operations in comparison agent; vendor names are display-only strings |

---

## Sources

### Primary (HIGH confidence)

- `services/ai/schemas/domain.py` — exact `ExtractionResult` shape, `LineItemExtraction` fields, `ComparisonResult` stub [VERIFIED: codebase]
- `services/ai/schemas/envelope.py` — `FlagStatus` 5-state enum values, `Field[T]` structure, `Evidence` shape [VERIFIED: codebase]
- `services/ai/agents/extraction.py` — full `StateGraph` + `get_stream_writer()` + `_run_impl(state, emit)` + error handling patterns [VERIFIED: codebase]
- `services/ai/api/app.py` — `EventSourceResponse` route pattern, `ExtractionRequest` validation shape [VERIFIED: codebase]
- `services/ai/grounding/gate.py` — `_walk_and_ground` field traversal pattern for flag collection [VERIFIED: codebase]
- `services/ai/prompts/extraction.v1.md` — structural template for comparison.v1.md (role, contract, flag definitions, humility, few-shot, output format) [VERIFIED: codebase]
- `services/ai/pyproject.toml` — all installed dependencies confirmed [VERIFIED: codebase]
- `.planning/phases/04-comparison-agent/04-CONTEXT.md` — all 11 locked decisions [VERIFIED: planning artifact]
- Context7 LangGraph docs — `get_stream_writer()`, `astream(stream_mode="custom")`, multi-node StateGraph [VERIFIED: Context7 /websites/langchain_oss_python_langgraph]

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — COMPARE-01..05 definitions, Out of Scope table [VERIFIED: planning artifact]
- `docs/traces/trace_vendor_thorough.json` — P3 trace JSON structure confirmed as template for D-11 comparison trace [VERIFIED: codebase]
- `services/ai/tests/test_extraction_agent.py` — test pattern for comparison test stubs (clamp test mirrors truncation/refusal tests) [VERIFIED: codebase]

### Tertiary (LOW confidence)

- Field → dimension contribution map (research recommendation; exact mapping is Claude's Discretion, may be adjusted by planner) [ASSUMED]
- `ComparisonResult` sub-model field names [ASSUMED — Claude's Discretion per CONTEXT.md]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in pyproject.toml; no new dependencies
- Architecture: HIGH — all patterns verified against extraction.py, app.py, gate.py
- ComparisonResult schema design: MEDIUM — shapes satisfy all D-01..D-11 constraints but exact field names are Claude's Discretion
- Field → dimension map: MEDIUM — derived from D-04 ceiling rules + ExtractionResult fields; planner may refine
- Pitfalls: HIGH — all derived from extraction.py pitfalls that directly apply + new comparison-specific ones

**Research date:** 2026-06-28
**Valid until:** 2026-07-28 (30 days — stable; all dependencies pinned; schema is internal)
