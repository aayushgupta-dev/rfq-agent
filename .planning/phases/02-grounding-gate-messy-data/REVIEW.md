---
phase: 02-grounding-gate-messy-data
reviewed: 2026-06-27T00:00:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - services/ai/grounding/gate.py
  - services/ai/grounding/report.py
  - services/ai/grounding/__init__.py
  - services/ai/schemas/domain.py
  - services/ai/agents/rfq_gen.py
  - services/ai/agents/vendor_gen.py
  - services/ai/scripts/generate_samples.py
  - services/ai/scripts/codegen.py
  - services/ai/api/app.py
  - services/ai/tests/test_grounding_gate.py
  - services/ai/tests/test_sample_fixtures.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-06-27
**Depth:** deep (cross-file analysis, call-chain tracing, unicode edge-case probing)
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the grounding gate, schemas, agents, API, and tests introduced in Phase 2. The grounding gate implementation is sound: the two-stage NFKC normalization map, the exact-then-fuzzy search strategy, the offset-recomputation logic, and the conservative "any failure downgrades the whole field" policy all behave correctly under adversarial probing. All 13 gate unit tests pass. No security vulnerabilities were found in the grounding logic itself.

The issues below are real defects or quality problems — none are hypothetical. The most important (WR-01) is a schema contract gap that directly contradicts CLAUDE.md §8 and will block the Phase 4 comparability-before-ranking requirement. WR-02 through WR-05 are correctness risks in the data-generation and API layers.

---

## Warnings

### WR-01: `FlagStatus` missing the `not-comparable` state mandated by CLAUDE.md §8

**File:** `services/ai/schemas/envelope.py:27`

**Issue:** CLAUDE.md §8 specifies six states a fact must be marked with: `present / missing / unclear / conflicting / unsupported / not-comparable`. `FlagStatus` only defines five — `not-comparable` is absent. The `ComparisonResult.comparable` field works around this with `Field[str]` (untyped string), meaning the comparability state is not validated or enumerable by pydantic or the TS contract. The gate cannot guard against invalid comparability states, and the UI cannot enumerate them without hard-coding string literals.

This directly violates the "comparability before ranking" product principle and will require a schema change + TS codegen run when Phase 4 arrives — changing a published contract mid-project is more disruptive than adding it now.

**Fix:**

```python
class FlagStatus(StrEnum):
    present = "present"
    missing = "missing"
    unclear = "unclear"
    conflicting = "conflicting"
    unsupported = "unsupported"
    not_comparable = "not-comparable"   # add this
```

Then change `ComparisonResult.comparable` from `Field[str]` to `Field[str]` using this enum value, or introduce a separate `ComparabilityStatus` enum if the comparison dimension needs richer typing. Either way, add `not_comparable` to `FlagStatus` now so the TS codegen produces the correct union type before P4 consumes it.

---

### WR-02: `generate_vendor_response()` KeyError on `FIXTURE_FILENAMES[persona]` for unchecked callers

**File:** `services/ai/agents/vendor_gen.py:232`

**Issue:** `generate_vendor_response()` is a public function. Line 232 accesses `FIXTURE_FILENAMES[persona]` to construct `source_id` without first verifying that `persona` is a valid key. The API endpoint (`app.py:86`) validates `persona` against `MESS_SPECS` before calling this function — but `FIXTURE_FILENAMES` and `MESS_SPECS` are two separate dicts maintained in parallel. If they ever diverge (a new persona added to one but not the other), the API validation passes but the function raises an unhandled `KeyError`, surfacing as a 500 with no useful error message to the caller.

The current keys are in sync, but the function trusts that invariant without enforcing it.

**Fix:**

Add a guard at the top of `generate_vendor_response()`:

```python
def generate_vendor_response(
    rfq_text: str,
    persona: str,
    mess_spec: list[MessSpecItem],
) -> VendorResponse:
    if persona not in FIXTURE_FILENAMES:
        raise ValueError(
            f"Unknown persona {persona!r}. Must be one of {list(FIXTURE_FILENAMES)}."
        )
    ...
```

Alternatively, derive `source_id` from the `persona` string directly (e.g. `f"vendor_{persona.replace('-', '_')}"`) and eliminate the second dict that must be kept in sync, but that changes the authoritative-filename contract the code explicitly chose to avoid.

---

### WR-03: `POST /data/vendor-gen` accepts unbounded `rfq_text` — potential for costly/abusive LLM calls

**File:** `services/ai/api/app.py:61,97`

**Issue:** `VendorGenRequest.rfq_text` is typed `str | None` with no length constraint. A caller can POST an arbitrarily large body: the text is forwarded verbatim into the vendor-gen prompt, creating an unbounded-cost OpenAI API call and a DoS surface (the server blocks until the LLM responds). For a prototype running locally this is acceptable, but the endpoint is already documented as live-regen (not localhost-only) and the comment at line 22 defers CORS/proxy-buffering only to Phase 5 — implying it will be exposed.

**Fix:**

Add a `max_length` constraint on the field:

```python
from pydantic import Field as pydantic_Field

class VendorGenRequest(BaseModel):
    persona: str
    rfq_text: str | None = pydantic_Field(default=None, max_length=50_000)
```

50,000 chars is generous for any realistic RFQ Markdown document and prevents runaway payloads without affecting legitimate use.

---

### WR-04: `mess_spec_dicts` serialized as Python `repr` (not JSON) when interpolated into the LLM prompt

**File:** `services/ai/agents/vendor_gen.py:216`

**Issue:** The mess spec is converted to a list of dicts via `model_dump()` and passed to `chain.invoke()`. LangChain interpolates template variables with `str()`, which produces Python `repr` notation (single quotes, `True`/`False` capitalized). The vendor-gen prompt presents `{mess_spec}` in a code block labelled as a structured list, but the model receives Python dict syntax rather than valid JSON:

```
[{'line_item': 'strategy-creative + tvc-development', 'issue_type': 'bundled_scope', ...}]
```

vs. what JSON-aware models expect:

```json
[{"line_item": "strategy-creative + tvc-development", "issue_type": "bundled_scope", ...}]
```

In practice GPT-5.4 handles Python repr fine, but this is fragile — a future model or a tighter system prompt could reject or misparse it.

**Fix:**

```python
import json

mess_spec_json = json.dumps([m.model_dump() for m in mess_spec], indent=2)

chain.invoke(
    {
        "rfq_text": rfq_text,
        "persona": persona,
        "mess_spec": mess_spec_json,
    }
)
```

---

### WR-05: `LineItem.budget_range_usd` documented as 2-element but not schema-enforced; silent budget omission on wrong-length list

**File:** `services/ai/schemas/domain.py:63`, `services/ai/agents/rfq_gen.py:86`

**Issue:** The docstring on `LineItem` (line 53–56) explains that `budget_range_usd` uses `list[int]` with a "2-element convention" because OpenAI structured output does not support Python tuples. The render function (`rfq_gen.py:86`) guards against wrong-length with `len(...) == 2`, silently skipping budget display without logging or raising. If the model returns a 1- or 3-element list (a plausible hallucination), the RFQ document rendered for vendors omits budget context with no warning to the caller.

**Fix:**

Add a `model_validator` in `LineItem` to enforce the invariant at construction time:

```python
from pydantic import model_validator

@model_validator(mode="after")
def _validate_budget_range(self) -> "LineItem":
    if self.budget_range_usd is not None and len(self.budget_range_usd) != 2:
        raise ValueError(
            f"budget_range_usd must be a 2-element [min, max] list, "
            f"got {len(self.budget_range_usd)} elements"
        )
    return self
```

---

## Info

### IN-01: `import re` inside test functions should be at module level

**File:** `services/ai/tests/test_sample_fixtures.py:99,140`

**Issue:** `import re` appears inside two test function bodies (`test_vendor_fixture_messiness` and `test_polished_fluff_has_conflict`). Python imports inside functions are re-executed on every call and clutter the function body. Standard practice is module-level import.

**Fix:** Move `import re` to line 6 alongside the other imports.

---

### IN-02: `_check_api_access()` in `generate_samples.py` swallows parameter-rejection errors as "cannot reach API"

**File:** `services/ai/scripts/generate_samples.py:43`

**Issue:** The broad `except Exception` catches parameter-rejection errors (HTTP 400 from OpenAI, which can occur with gpt-5.4 reasoning models that reject unsupported parameters) and reports them as "Cannot reach OpenAI API. Check OPENAI_API_KEY." This gives a misleading error message when the key is valid but the ping call uses unsupported params. `factory.py:verify_access()` handles this distinction correctly via `_is_param_rejection()`.

**Fix:** Replace the ad-hoc access check with a call to `verify_access()` from `llm.factory`:

```python
from llm.factory import verify_access

def _check_api_access() -> None:
    try:
        verify_access()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
```

This reuses the existing categorized error logic and removes the duplicate ping call.

---

### IN-03: `HTTPException` imported lazily inside the request handler

**File:** `services/ai/api/app.py:87`

**Issue:** `from fastapi import HTTPException` is imported inside the `post_vendor_gen` handler on the error path. This works correctly in Python (module-level cache means no performance penalty after the first call) but is non-standard and harder to grep/audit for exception handling.

**Fix:** Move `from fastapi import HTTPException` to the top-level imports in `app.py`.

---

### IN-04: `_walk_and_ground` does not traverse `dict`-valued pydantic fields

**File:** `services/ai/grounding/gate.py:346`

**Issue:** `_walk_and_ground` handles `BaseModel` fields and `list` fields but not `dict` fields. If a future Phase 3/4 schema has a `dict[str, Field[T]]` attribute (e.g. a per-line-item extraction keyed by line item ID), those `Field[T]` values will silently bypass grounding. No current domain schema triggers this, but the walker's coverage gap contradicts its "schema-agnostic recursive" contract.

**Fix:** Add a `dict` branch after the `list` branch:

```python
elif isinstance(value, dict):
    new_dict: dict[object, object] = {}
    for k, v in value.items():
        if isinstance(v, EnvelopeField):
            grounded_v, v_entries = ground_field(v, sources, f"{field_path}[{k!r}]")
            new_dict[k] = grounded_v
            report.extend(v_entries)
        elif isinstance(v, BaseModel):
            grounded_v, v_entries = _walk_and_ground(v, sources, f"{field_path}[{k!r}]")
            new_dict[k] = grounded_v
            report.extend(v_entries)
        else:
            new_dict[k] = v
    updates[field_name] = new_dict
```

This closes the gap before P3 schemas are written and prevents a silent grounding bypass that would violate the product's core reliability invariant.

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
