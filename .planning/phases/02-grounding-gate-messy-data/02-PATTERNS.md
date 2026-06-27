# Phase 2: Grounding Gate & Messy Data — Pattern Map

**Mapped:** 2026-06-27
**Files analyzed:** 12 new/modified files
**Analogs found:** 12 / 12 (all have direct codebase analogs)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `services/ai/grounding/__init__.py` | module init | — | `services/ai/agents/__init__.py` | exact |
| `services/ai/grounding/gate.py` | utility (pure) | transform | `services/ai/schemas/envelope.py` | role-match (pydantic objects + model_validator) |
| `services/ai/grounding/report.py` | model | — | `services/ai/schemas/events.py` | role-match (dataclass/pydantic schema) |
| `services/ai/schemas/domain.py` | model | CRUD | `services/ai/schemas/envelope.py` | exact (same file — modify in place) |
| `services/ai/agents/rfq_gen.py` | agent/service | request-response | `services/ai/agents/_demo.py` + `services/ai/llm/factory.py` | role-match |
| `services/ai/agents/vendor_gen.py` | agent/service | request-response | `services/ai/agents/_demo.py` + `services/ai/llm/factory.py` | role-match |
| `services/ai/scripts/generate_samples.py` | utility/CLI | batch | `services/ai/scripts/codegen.py` | role-match |
| `services/ai/prompts/rfq-gen.v1.md` | prompt | — | `services/ai/prompts/vendor-gen.v1.md` | exact (same format) |
| `services/ai/prompts/vendor-gen.v1.md` | prompt | — | `services/ai/prompts/rfq-gen.v1.md` | exact (same format) |
| `services/ai/prompts/messy-data-gen.v1.md` | prompt | — | `services/ai/prompts/rfq-gen.v1.md` | exact (same format) |
| `services/ai/tests/test_grounding_gate.py` | test | — | `services/ai/tests/test_field_envelope.py` | exact |
| `services/ai/tests/test_sample_fixtures.py` | test | — | `services/ai/tests/test_codegen_drift.py` + `test_field_envelope.py` | role-match |
| `services/ai/api/app.py` | route | request-response | `services/ai/api/app.py` | exact (modify in place) |

---

## Pattern Assignments

---

### `services/ai/grounding/__init__.py` (module init)

**Analog:** `services/ai/agents/__init__.py` (confirmed empty — a bare `__init__.py` that marks the directory as a Python package)

**Pattern:** Create as an empty file or with a minimal docstring + re-exports of the public API.

**Re-export pattern** (mirror `prompts/__init__.py` if it exposes things, else bare):
```python
# grounding/__init__.py
# Re-exports the public grounding API so callers use:
#   from grounding import ground_model, ground_field, DowngradeReport
from grounding.gate import ground_field, ground_model
from grounding.report import DowngradeEntry, DowngradeReport

__all__ = ["ground_field", "ground_model", "DowngradeEntry", "DowngradeReport"]
```

---

### `services/ai/grounding/gate.py` (utility, transform — pure, LLM-free)

**Primary analog:** `services/ai/schemas/envelope.py` (same pydantic object manipulation, model_copy pattern, `# noqa: UP046`, alias import guard)

**Secondary analog:** `services/ai/agents/_demo.py` (module-level docstring style, `from __future__ import annotations`)

**Imports pattern** (lines 1-17 of `envelope.py` → adapted):
```python
"""
gate.py — Grounding gate: verify and recompute evidence spans (EXTRACT-04).

Pure, LLM-free. Ignores model-supplied char_start/char_end (D-01); searches
source text for the snippet, recomputes REAL offsets on a hit, and downgrades
unlocatable facts to unsupported (D-06). Sources are dict[str, str] keyed by
Evidence.source_id (D-07).

# ponytail: class named Field shadows pydantic.Field — use EnvelopeField alias
# (same guard as envelope.py line 24).
"""
from __future__ import annotations

import unicodedata

from rapidfuzz.fuzz import partial_ratio_alignment

from schemas.envelope import Evidence, Field as EnvelopeField, FlagStatus
from grounding.report import DowngradeEntry, DowngradeReport
```

**`# noqa: UP046` pattern** — not needed in gate.py (gate.py itself is not a `Generic[T]` class). The `Generic[T]` pattern lives in `envelope.py`. Gate operates on already-instantiated `Field[T]` objects.

**Module-level constants** (copy the `_TIER_ENV` style from `factory.py` lines 37-40):
```python
FUZZY_THRESHOLD: float = 90.0
# ponytail: 15-char minimum guards against trivially-short snippets scoring high
# via partial_ratio (Pitfall 3). Revisit in P3 once extraction agent output is known.
MIN_SNIPPET_LEN: int = 15
```

**Core pure function pattern** (modelled on `envelope.py`'s `model_validator` → return `self` / raise):
```python
def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Two-stage normalization: NFKC+casefold, then whitespace collapse (D-02/D-04)."""
    # Stage 1 builds stage1_to_orig[]
    # Stage 2 builds surviving_positions[] → compose maps
    ...

def _match_exact(norm_snippet: str, norm_source: str, orig_indices: list[int]) -> tuple[int, int] | None:
    ...

def _match_fuzzy(norm_snippet: str, norm_source: str, threshold: float, orig_indices: list[int]) -> tuple[int, int] | None:
    ...

def ground_field(
    field: EnvelopeField,   # NOT pydantic.Field — alias guards the collision
    sources: dict[str, str],
    field_path: str = "",
) -> tuple[EnvelopeField, list[DowngradeEntry]]:
    ...

def ground_model(
    obj: BaseModel,
    sources: dict[str, str],
) -> tuple[BaseModel, DowngradeReport]:
    ...
```

**Pydantic `model_copy(update=...)` pattern** (from `envelope.py` / RESEARCH.md Pattern 4):
```python
# Produce new object — NEVER mutate in place (D-06).
# model_copy is the pydantic v2 way; .copy() is deprecated.
return field.model_copy(update={"evidence": new_evidence}), []
```

**Downgrade to unsupported** — the envelope's `model_validator` enforces the contract; just construct the unsupported state:
```python
# envelope.py model_validator: unsupported must have value=None and evidence=[].
# Gate only needs to set status; the validator does the rest.
return EnvelopeField(status=FlagStatus.unsupported), downgrade_entries
```

**Conflicting field branch** (Pitfall 5 from RESEARCH.md — must iterate `field.values`):
```python
if field.status == FlagStatus.conflicting:
    # evidence is inside each ConflictingValue, not at top level (envelope invariant)
    new_values = []
    for cv in (field.values or []):
        grounded_evidence, entries = _ground_evidence_list(cv.evidence, sources, field_path)
        downgrade_entries.extend(entries)
        new_values.append(cv.model_copy(update={"evidence": grounded_evidence}))
    ...
```

**Alias import guard** (copy verbatim from `envelope.py` line 24):
```python
# ponytail: class named Field shadows pydantic.Field — alias import avoids collision
# without renaming the contract class (the pydantic.Field function is imported as
# pydantic_Field).
from schemas.envelope import Field as EnvelopeField
from pydantic import Field as pydantic_Field  # only if gate.py defines pydantic models
```

---

### `services/ai/grounding/report.py` (model — downgrade report dataclasses)

**Analog:** `services/ai/schemas/events.py` (pydantic `BaseModel` with `ConfigDict(extra="forbid")`)

**Imports pattern** (lines 1-17 of `events.py`):
```python
"""
report.py — Downgrade report types for the grounding gate (EXTRACT-04).

DowngradeEntry: one failed grounding attempt (field path, evidence, reason).
DowngradeReport: the full collection returned alongside the re-grounded object.

Consumed by tests now; passed to the SSE trace in P3.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic import Field as pydantic_Field

from schemas.envelope import Evidence
```

**Model pattern** (copy `ConfigDict(extra="forbid")` from `events.py` lines 23-29):
```python
class DowngradeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str
    original_status: str        # FlagStatus.value — str avoids circular import
    failed_evidence: Evidence
    reason: str


class DowngradeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[DowngradeEntry] = pydantic_Field(default_factory=list)

    @property
    def has_downgrades(self) -> bool:
        return len(self.entries) > 0
```

---

### `services/ai/schemas/domain.py` — **modify in place** (schema fleshing)

**Analog:** `services/ai/schemas/envelope.py` (same file patterns — `ConfigDict(extra="forbid")`, `# noqa: UP046` on `Generic[T]` classes, `# ponytail:` comments, `pydantic_Field`)

**Current stub pattern** (lines 30-55 of `domain.py`) — replace `RFQ` and `VendorResponse` stubs:

**`# noqa: UP046` rule** — required on any `class Foo(BaseModel, Generic[T])` (see `envelope.py` lines 72, 86). The new `RFQ` and `VendorResponse` are NOT generic, so `# noqa: UP046` is NOT needed on them. It IS needed if any helper class extends `Generic[T]`.

**`ConfigDict(extra="forbid")` rule** (copy from every model in `envelope.py`):
```python
class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ...

class RFQ(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ...
```

**Field naming convention** (from `envelope.py` lines 83, 101-103):
```python
from pydantic import BaseModel, ConfigDict
from pydantic import Field as pydantic_Field  # alias — guards collision with envelope.Field

# For list fields with defaults:
questionnaire: list[str] = pydantic_Field(default_factory=list)
compliance_requirements: list[str] = pydantic_Field(default_factory=list)
```

**`# ponytail:` comment style for kept stubs** (from `domain.py` lines 11-19):
```python
# ponytail: ExtractionResult/ComparisonResult stay P3/P4 stubs — contract
# placeholder precedes the agents that fill it.
```

**No `Field[T]` wrapper on RFQ** — RFQ is our own clean artifact (CONTEXT.md D-11/D-12). Use plain Python types, not the absence-envelope `Field[T]`. Only `VendorResponse` provenance metadata fields are plain types too.

**Codegen impact note** — after touching `domain.py`, the plan step must run:
```bash
cd services/ai && uv run python scripts/codegen.py
# then commit packages/shared-types/index.d.ts alongside domain.py
```

---

### `services/ai/agents/rfq_gen.py` (agent/service, request-response)

**Primary analog:** `services/ai/agents/_demo.py` (module docstring, `from __future__ import annotations`, `from llm.factory import get_llm` style, LangGraph node structure)

**Secondary analog:** `services/ai/llm/factory.py` (env-var + error pattern, `# ponytail:` comments)

**Imports pattern** (adapted from `_demo.py` lines 1-28 + RESEARCH.md Pattern 5):
```python
"""
rfq_gen.py — RFQ generation agent (DATA-01).

Calls rfq-gen.v1.md prompt via get_llm("reasoning") + with_structured_output(RFQ).
Returns a validated RFQ pydantic instance. Does NOT use LangGraph — a plain
LangChain chain suffices for a single structured call.
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from llm.factory import get_llm
from prompts.registry import load
from schemas.domain import RFQ
```

**Prompt loading pattern** (from `prompts/registry.py` lines 50-68 — use `load()` not `open()`):
```python
# Always load prompts via registry — never open() the file directly.
# load() handles version resolution and frontmatter parsing.
post = load("rfq-gen")
prompt = ChatPromptTemplate.from_messages([
    ("system", post.content),
    ("human", "Generate the RFQ now."),
])
```

**LLM tier call** (from `factory.py` lines 57-81 — always call `get_llm(tier)`, never hardcode model id):
```python
llm = get_llm("reasoning")
chain = prompt | llm.with_structured_output(RFQ, method="json_schema")
return chain.invoke({})
```

**No LangGraph for single calls** — `_demo.py` uses LangGraph because it's proving the streaming spine. `rfq_gen.py` is a one-shot structured call; a plain chain is correct (D-08 / RESEARCH.md Pattern 5).

---

### `services/ai/agents/vendor_gen.py` (agent/service, request-response — plain-text)

**Analog:** same as `rfq_gen.py` above, but with `.invoke()` instead of `.with_structured_output()`

**Plain-text call pattern** (RESEARCH.md Pattern 6 — copy verbatim):
```python
from langchain_core.messages import AIMessage

chain = prompt | llm          # NO .with_structured_output() — vendor text must be raw
result: AIMessage = chain.invoke({
    "rfq_text": rfq_text,
    "persona": persona,
    "mess_spec": str(mess_spec),
})
raw_text: str = result.content  # type: ignore[assignment]
```

**VendorResponse construction** (the schema carries raw text + provenance, not extracted fields — D-12):
```python
return VendorResponse(
    vendor_name=persona,
    persona=persona,
    mess_spec=mess_spec,
    source_id=f"vendor_{persona}",
    format_label="...",   # varies by persona
    raw_text=raw_text,
)
```

**Mess spec as hand-authored list** (D-09 — defined in this module, one per persona):
```python
MESS_SPECS: dict[str, list[dict]] = {
    "thorough-but-pricey": [
        {"line_item": "strategy-creative", "issue_type": "bundled_scope", "instruction": "..."},
        ...
    ],
    "cheap-but-incomplete": [...],
    "polished-fluff": [...],
}
```

---

### `services/ai/scripts/generate_samples.py` (utility/CLI, batch)

**Analog:** `services/ai/scripts/codegen.py` (CLI script structure — `repo_root()`, `if __name__ == "__main__"`, writes to `data/`)

**Imports pattern** (lines 1-23 of `codegen.py`):
```python
"""
generate_samples.py — CLI: generate and commit RFQ + 3 vendor responses.

Usage (from services/ai/):
    uv run python scripts/generate_samples.py

Writes JSON + Markdown fixtures to <repo_root>/data/.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.codegen import repo_root   # reuse the repo-root resolver
from agents.rfq_gen import generate_rfq
from agents.vendor_gen import generate_vendor_response, MESS_SPECS
```

**`repo_root()` reuse** (from `codegen.py` line 26 — do NOT reimplement; import it):
```python
root = repo_root()
data_dir = root / "data"
data_dir.mkdir(exist_ok=True)
```

**Output pattern** (write JSON via pydantic `.model_dump_json()` — consistent with how pydantic objects are serialized elsewhere):
```python
rfq_path = data_dir / "rfq.json"
rfq_path.write_text(rfq.model_dump_json(indent=2))
```

**`if __name__ == "__main__"` pattern** (from `codegen.py` lines 98-100):
```python
if __name__ == "__main__":
    main()
```

---

### Prompt files: `rfq-gen.v1.md`, `vendor-gen.v1.md`, `messy-data-gen.v1.md` (prompt, authored)

**Analog:** Existing stubs at the same paths — the frontmatter schema is already defined; only the body changes.

**Frontmatter pattern** (copy from existing `rfq-gen.v1.md` lines 1-16 — must keep ALL keys):
```yaml
---
id: rfq-gen          # must match filename stem (test_prompt_registry.py::test_id_matches_filename_stem)
version: 1
intent: >
  <single sentence — what the prompt produces>
model_tier: reasoning    # "reasoning" or "cheap" — validated in test_prompt_registry.py
failure_handling: >
  <what to do when the model produces bad output>
---
```

**Required frontmatter keys** (from `test_prompt_registry.py` lines 38-55 — tests assert all four):
- `id` — must match filename stem
- `intent` — non-empty string
- `model_tier` — must be `"reasoning"` or `"cheap"`
- `failure_handling` — non-empty string

**Body style** — Markdown prose. The stub bodies use `TODO P2 / DATA-0N:` as a placeholder; replace with real prompt content.

---

### `services/ai/tests/test_grounding_gate.py` (test — unit, pure)

**Analog:** `services/ai/tests/test_field_envelope.py` (exact match — same pydantic-object unit test structure)

**File-level docstring pattern** (lines 1-10 of `test_field_envelope.py`):
```python
"""
Grounding gate unit tests (EXTRACT-04).

Each invalid grounding case must produce a DowngradeEntry and return
status=unsupported (success criterion 1).
Each genuine evidence snippet must survive with recomputed offsets (success criterion 2).
"""
```

**Imports pattern** (lines 9-20 of `test_field_envelope.py`):
```python
from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.envelope import (
    ConflictingValue,
    Evidence,
    Field,
    FlagStatus,
)
from grounding.gate import ground_field, ground_model
from grounding.report import DowngradeEntry, DowngradeReport
```

**Test class grouping** (from `test_field_envelope.py` — comment-separated sections; class-per-concern):
```python
# ---------------------------------------------------------------------------
# Fabricated span downgrade (success criterion 1)
# ---------------------------------------------------------------------------

class TestFabricatedSpanDowngrade:
    def test_fabricated_span_is_downgraded(self) -> None: ...
    def test_downgraded_value_is_none(self) -> None: ...
    def test_downgraded_evidence_is_empty(self) -> None: ...


# ---------------------------------------------------------------------------
# Genuine span survival (success criterion 2)
# ---------------------------------------------------------------------------

class TestGenuineSpanPasses:
    def test_genuine_span_passes_grounding(self) -> None: ...
    def test_offsets_are_recomputed_not_trusted(self) -> None: ...
```

**Evidence construction pattern** (from `test_field_envelope.py` lines 39-43 — exact copy style):
```python
ev = Evidence(snippet="...", char_start=0, char_end=1, source_id="v1")
```

**Field construction pattern** (from `test_field_envelope.py` lines 57-59):
```python
f: Field[str] = Field[str](status=FlagStatus.present, value="...", evidence=[ev])
```

**Monkeypatch / fixture style** — gate tests are pure (no mocking needed; no env vars). Use plain `def test_...() -> None:` functions matching `test_field_envelope.py` style.

**Falsifiability test stubs** (from RESEARCH.md Validation Architecture — copy these exact signatures as the first two tests):
```python
def test_fabricated_span_is_downgraded() -> None:
    source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
    fabricated_evidence = Evidence(
        snippet="Vendor A proposes $99 for everything",
        char_start=0, char_end=10, source_id="v1"
    )
    field = Field[str](
        status=FlagStatus.present,
        value="$99 for everything",
        evidence=[fabricated_evidence],
    )
    grounded, report = ground_field(field, {"v1": source})
    assert grounded.status == FlagStatus.unsupported
    assert grounded.value is None
    assert grounded.evidence == []
    assert len(report) == 1


def test_genuine_span_passes_grounding() -> None:
    source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
    genuine_evidence = Evidence(
        snippet="$15,000 for strategy and creative",
        char_start=0, char_end=10,   # intentionally wrong — gate recomputes
        source_id="v1"
    )
    field = Field[str](
        status=FlagStatus.present,
        value="15000",
        evidence=[genuine_evidence],
    )
    grounded, report = ground_field(field, {"v1": source})
    assert grounded.status == FlagStatus.present
    assert len(report) == 0
    ev = grounded.evidence[0]
    assert source[ev.char_start:ev.char_end] == "$15,000 for strategy and creative"
```

---

### `services/ai/tests/test_sample_fixtures.py` (test — fixture existence + string assertions)

**Primary analog:** `services/ai/tests/test_codegen_drift.py` (fixture-path resolution pattern — `repo_root()` import, `Path` usage)

**Secondary analog:** `services/ai/tests/test_field_envelope.py` (pydantic deserialization assertions)

**Imports pattern** (from `test_codegen_drift.py` lines 1-17):
```python
"""
test_sample_fixtures.py — Existence and messiness assertions on committed sample data (DATA-01/02/03).

Tests run against COMMITTED files under data/ — no LLM calls (D-13).
Live regen is a separate smoke path, not tested here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.codegen import repo_root
from schemas.domain import RFQ, VendorResponse
```

**Fixture path resolution** (from `test_codegen_drift.py` lines 21-29 — use `repo_root()` not relative paths):
```python
_DATA_DIR = repo_root() / "data"

def test_rfq_fixture_valid() -> None:
    rfq_path = _DATA_DIR / "rfq.json"
    assert rfq_path.exists(), f"data/rfq.json not found at {rfq_path}"
    rfq = RFQ.model_validate_json(rfq_path.read_text())
    assert isinstance(rfq, RFQ)
    assert len(rfq.line_items) == 8
```

**Messiness string assertion pattern** (from RESEARCH.md D-13 — deterministic string search on committed fixtures):
```python
def test_cheap_incomplete_has_missing_price() -> None:
    """Cheap-but-incomplete persona must have at least one line item with no price mention."""
    vendor_path = _DATA_DIR / "vendor_cheap.json"
    vendor = VendorResponse.model_validate_json(vendor_path.read_text())
    raw = vendor.raw_text.lower()
    # Assert no price pattern for at least one expected missing-price marker
    assert "price not provided" in raw or "tbd" in raw or not any(
        f"${n}" in raw for n in range(1000, 999999)
    ), "cheap-but-incomplete vendor must have at least one line item with no visible price"
```

---

### `services/ai/api/app.py` — **modify in place** (add DATA-04 endpoints)

**Analog:** `services/ai/api/app.py` itself (modify in place — the existing lifespan + SSE route pattern is the template)

**Existing route pattern to copy** (lines 46-69 of `app.py`):
```python
@app.get("/stream/demo")
async def stream_demo() -> EventSourceResponse:
    ...
```

**New synchronous GET endpoint pattern** (DATA-04 — live regen, no SSE needed per RESEARCH.md Open Question 3):
```python
@app.get("/data/rfq")
async def get_rfq() -> dict:
    """Live-regenerate the RFQ via the rfq-gen prompt. Returns pydantic JSON."""
    rfq = generate_rfq()
    return json.loads(rfq.model_dump_json())
```

**Import additions** (follow existing `from agents._demo import demo_graph` pattern at line 26):
```python
from agents.rfq_gen import generate_rfq
from agents.vendor_gen import generate_vendor_response, MESS_SPECS
```

---

## Shared Patterns

### `from __future__ import annotations` (ALL new Python files)
**Source:** Every existing `.py` file in the codebase (`envelope.py` line 18, `factory.py` line 18, `_demo.py` line 18, `app.py` line 18, all test files)
**Apply to:** All new `.py` files — no exceptions.

### Module docstring structure
**Source:** `services/ai/schemas/envelope.py` lines 1-17; `services/ai/llm/factory.py` lines 1-16
**Apply to:** All new `.py` modules
```python
"""
<module_name>.py — <one-line role description>.

<Purpose paragraph: what it does, what it does NOT do, key decisions referenced.>

# ponytail: <any deliberate kept-complexity with rationale>
"""
```

### `ConfigDict(extra="forbid")` on every pydantic model
**Source:** `services/ai/schemas/envelope.py` line 52 (Evidence), line 80 (ConflictingValue), line 95 (Field); `services/ai/schemas/events.py` lines 28, 43
**Apply to:** `grounding/report.py` (DowngradeEntry, DowngradeReport), any new pydantic model in `domain.py`
```python
model_config = ConfigDict(extra="forbid")
```

### `# noqa: UP046` on `Generic[T]` pydantic classes
**Source:** `services/ai/schemas/envelope.py` lines 72, 86
```python
class ConflictingValue(BaseModel, Generic[T]):  # noqa: UP046
class Field(BaseModel, Generic[T]):  # noqa: UP046
```
**Apply to:** Any new class that extends `BaseModel, Generic[T]`. Not needed for plain `BaseModel` subclasses.

### `pydantic_Field` alias for list defaults
**Source:** `services/ai/schemas/envelope.py` lines 24, 83, 101-103
```python
from pydantic import Field as pydantic_Field
# ...
evidence: list[Evidence] = pydantic_Field(default_factory=list)
```
**Apply to:** Any pydantic model in `grounding/report.py` or `domain.py` that has a list field with a default.

### `# ponytail:` comment for deliberate kept-complexity
**Source:** `services/ai/schemas/envelope.py` lines 14-16, 99-100; `services/ai/schemas/domain.py` lines 11-19; `services/ai/llm/factory.py` line 51
**Apply to:** Any code in `grounding/gate.py` that looks "over-engineered" (the two-stage normalization map, the `MIN_SNIPPET_LEN` constant, the conflicting-field branch).
```python
# ponytail: two-stage normalization map exists because NFKC expansion and
# whitespace collapse both change string length; a single-pass assumption
# breaks offset recovery (D-04). Not simplifiable without breaking the invariant.
```

### `load(prompt_id)` for all prompt access
**Source:** `services/ai/prompts/registry.py` lines 50-68
**Apply to:** `rfq_gen.py`, `vendor_gen.py` — never use `open()` directly.
```python
from prompts.registry import load
post = load("rfq-gen")
system_content = post.content
```

### `get_llm(tier)` for all LLM access
**Source:** `services/ai/llm/factory.py` lines 57-81
**Apply to:** `rfq_gen.py`, `vendor_gen.py` — never hardcode a model id.
```python
from llm.factory import get_llm
llm = get_llm("reasoning")
```

### Test file `-> None` return type annotation
**Source:** `services/ai/tests/test_field_envelope.py` lines 28, 38, 47 (every test function)
**Apply to:** All test functions in `test_grounding_gate.py` and `test_sample_fixtures.py`.
```python
def test_something() -> None:
    ...
```

### pydantic v2 deserialization in tests
**Source:** `services/ai/tests/test_codegen_drift.py` pattern (read file, call `.model_validate_json()`)
**Apply to:** `test_sample_fixtures.py`
```python
rfq = RFQ.model_validate_json(rfq_path.read_text())
```

---

## No Analog Found

All files have codebase analogs. No files require falling back to RESEARCH.md patterns alone.

---

## Metadata

**Analog search scope:** `services/ai/schemas/`, `services/ai/agents/`, `services/ai/llm/`, `services/ai/api/`, `services/ai/prompts/`, `services/ai/scripts/`, `services/ai/tests/`
**Files scanned:** 18 Python source files + 7 prompt stubs + 1 pyproject.toml
**Pattern extraction date:** 2026-06-27
