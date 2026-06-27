---
phase: 03-extraction-agent
reviewed: 2026-06-28T00:00:00Z
depth: deep
files_reviewed: 8
files_reviewed_list:
  - services/ai/agents/extraction.py
  - services/ai/api/app.py
  - services/ai/schemas/domain.py
  - services/ai/scripts/capture_traces.py
  - services/ai/tests/test_extraction_agent.py
  - services/ai/tests/conftest_extraction.py
  - packages/shared-types/index.d.ts
  - services/ai/pyproject.toml
findings:
  critical: 2
  warning: 3
  info: 3
  total: 8
status: resolved
resolution:
  date: 2026-06-28
  fixed: [CR-01, CR-02, WR-01, WR-02, WR-03, IN-01, IN-02]
  accepted: [IN-03]
  notes: >
    7/8 fixed in code (commit follows). CR-01 verified with a targeted probe
    (success-path exception now emits a safe error event). Full suite GREEN
    (116 passed, 1 xfailed). IN-03 accepted: index.d.ts is pydantic2ts-generated
    ("do not modify by hand") and guarded by test_codegen_drift — the FieldStr/
    FieldStr1 duplicate is structurally identical, not consumed until Phase 5 UI,
    and a correct fix requires a codegen post-process step. Hand-editing would
    break the drift gate. Deferred to Phase 5.
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-28
**Depth:** deep
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Phase 3 implements the extraction agent, grounding gate, SSE streaming pipeline, and trace capture.
The core reliability contract (failure shapes → safe SSE error events, grounding before emit) is
well-structured. The schema envelope, grounding gate logic, and failure-shape routing in
`_run_extraction_impl` are sound. Two blockers were found: the success path is not wrapped by the
outer `try/except`, violating the stated guarantee that all failures produce safe error events; and
the live-guard test will raise the wrong exception type (KeyError, not `LengthFinishReasonError`)
once its `xfail` is removed. Three warnings cover: the stale module docstring that misleads about
test state, an unbounded server-side body for RFQ fields, and rfq_json logic duplicated across two
function bodies. The Python ↔ TS type contract is in sync; no security vulnerabilities found.

---

## Critical Issues

### CR-01: Success path not covered by error-handling — exceptions from `ground_model` or `model_dump` escape unhandled

**File:** `services/ai/agents/extraction.py:200-230`

**Issue:** The outer `try/except Exception` block spans lines 107–198 only. The success path
(lines 200–230) — which calls `parsed.model_copy()`, `ground_model()`, and `grounded.model_dump()`
— is at the same indentation level *after* the `except` clause. Any exception raised there
propagates uncaught out of `_run_extraction_impl`, crashes the LangGraph node, and produces no
SSE error event. The module docstring claims "every structured-output failure shape maps to a safe
error event" and "No half-parsed object ever reaches the result path," but that guarantee does not
hold if `ground_model()` raises (e.g., a pydantic `ValidationError` from `model_copy`) or if
`model_dump()` raises. The SSE client silently receives no result and no error.

**Fix:** Wrap the entire node body — including the success path — in a single outer
`try/except`:

```python
def _run_extraction_impl(state, emit):
    assert {"status", "result", "error"} <= set(EVENT_TYPES)
    vendor = state["vendor"]
    rfq = state["rfq"]
    # ... rfq_json, initial status emit ...

    try:
        # inner truncation try (unchanged)
        try:
            raw_output = _chain.invoke(...)
        except LengthFinishReasonError:
            emit({...recoverable...})
            return {"error": "truncated"}

        # refusal, parse, type checks (unchanged, each return early) ...

        # SUCCESS PATH — now inside the outer try
        raw = parsed.model_copy(update={"vendor_name": vendor.vendor_name})
        emit({"type": "status", "payload": {"message": "running grounding gate", ...}})
        grounded, report = ground_model(raw, {vendor.source_id: vendor.raw_text})
        result_event = {"type": "result", "payload": {...}}
        emit(result_event)
        return {"result": grounded, "report": report, "result_sse_event": result_event}

    except Exception as exc:
        emit({"type": "error", "payload": ErrorPayload(
            code="extraction_error", message=str(exc), recoverable=False
        ).model_dump()})
        return {"error": "extraction_error"}
```

---

### CR-02: `test_truncation_live_guard` omits `source_id` from `_chain.invoke` — will raise `KeyError`, not `LengthFinishReasonError`

**File:** `services/ai/tests/test_extraction_agent.py:551-554`

**Issue:** The live guard invokes `_chain` with only `vendor_text` and `rfq_line_items`:

```python
_chain.invoke(
    {"vendor_text": "x" * 50000, "rfq_line_items": ""},
    config={"max_tokens": 1},
)
```

The `_prompt` template (defined at `extraction.py:52-60`) contains a `{source_id}` placeholder
in the human turn. LangChain will raise a `KeyError` (or `PromptTemplate` rendering error) when
it tries to render the template, *before* any API call is made. The test currently hides this
behind `@pytest.mark.xfail(strict=True)`, but once `xfail` is removed (the intent of the live
guard is to verify a live OpenAI call), the test will fail with the wrong exception — not proving
the `LengthFinishReasonError` assumption it was designed to validate.

**Fix:** Add the missing `source_id` key:

```python
_chain.invoke(
    {
        "vendor_text": "x" * 50000,
        "rfq_line_items": "[]",
        "source_id": "live-guard-test",
    },
    config={"max_tokens": 1},
)
```

---

## Warnings

### WR-01: Module docstring falsely claims all nine tests carry `@pytest.mark.xfail(strict=True)`

**File:** `services/ai/tests/test_extraction_agent.py:4-7`

**Issue:** The module docstring says:

> "All 9 tests are marked `@pytest.mark.xfail(strict=True)` — they must FAIL until the
> corresponding implementation plan executes."

Only `test_truncation_live_guard` (test 9, line 536) carries the decorator. Tests 1–8 have no
`xfail` marker and are active. When the next developer reads this docstring, they will believe
that passing tests 1–8 are an unexpected success (`XPASS`) and may not trust the suite. More
seriously, if CI is gated on `--strict-markers` and someone applies the docstring literally by
adding `xfail` to tests that already pass, those tests will flip to `XFAIL` status, hiding real
regressions.

**Fix:** Remove the false claim from the module docstring. The accurate state is: "Tests 1–8 are
active assertions that must pass. `test_truncation_live_guard` (test 9) is `@pytest.mark.live +
@pytest.mark.xfail(strict=True)` pending live-guard validation."

---

### WR-02: No server-level body size limit — RFQ subfields are unbounded, bypassing the 200 k guard

**File:** `services/ai/api/app.py:101-124`

**Issue:** `ExtractionRequest._check_raw_text_length` only validates
`vendor_response.raw_text ≤ 200,000 chars`. The `RFQ` subfields — `questionnaire` (unbounded
`list[str]`), `compliance_requirements` (unbounded `list[str]`), `line_items[*].description`,
and `line_items[*].deliverables` — carry no length constraints. A request body containing a
questionnaire with hundreds of multi-kilobyte entries would be deserialized in full before any
validation fires, then forwarded to the model. FastAPI/Starlette has no default body size limit,
so this path is limited only by memory. The comment at line 109 defers server-level controls to
Phase 5 (SHIP-01), which is an acceptable prototype trade-off, but the guard's comment implies
the 200 k check is the "operative guard" when it actually covers only one of several large-input
vectors.

**Fix (for Phase 5 / SHIP-01):** Add a uvicorn `--limit-concurrency` and a Starlette
`ContentSizeLimitMiddleware` (or nginx `client_max_body_size`) to bound total request size before
pydantic deserializes it. For the prototype, at minimum note in the comment that RFQ fields are
also unbounded so reviewers don't believe the guard is comprehensive.

---

### WR-03: `rfq_json` construction duplicated in `_run_extraction_impl` and `generate_extraction_with_trace`

**File:** `services/ai/agents/extraction.py:92-97` and `347-352`

**Issue:** The `rfq_json` building block — iterating `rfq.line_items` and serialising `id`,
`name`, `description` — appears twice, character-for-character, in two separate functions.
If the RFQ prompt contract changes (e.g., adding `timeline_weeks` to the serialised items), one
copy is likely to be updated and the other missed, causing the production SSE path and the trace
capture path to present different inputs to the model without any error.

**Fix:** Extract a one-liner helper at module level:

```python
def _rfq_items_json(rfq: RFQ) -> str:
    return json.dumps(
        [{"id": li.id, "name": li.name, "description": li.description}
         for li in rfq.line_items]
    )
```

Replace both call sites with `_rfq_items_json(rfq)` / `_rfq_items_json(rfq)`.

---

## Info

### IN-01: Stale `xfail`/wave-0 comments throughout test module

**File:** `services/ai/tests/test_extraction_agent.py:1-24`

**Issue:** Several inline comments reference "Wave 0", "until Plan 03-03 executes", and similar
pre-execution state (e.g., `# type: ignore[import-not-found]` on `from agents.extraction import`
and `# type: ignore[attr-defined]` on schema imports that now exist). These are harmless now but
will confuse the next reviewer into thinking the imports are still broken.

**Fix:** Remove `# type: ignore[import-not-found]` and `# type: ignore[attr-defined]` comments
on imports that resolve cleanly now that Phase 3 is implemented. Update or remove the "Wave 0"
references in the module docstring.

---

### IN-02: `downgrade_report` key collision risk is undocumented in schema and relies on implicit assumption

**File:** `services/ai/agents/extraction.py:219-226`

**Issue:** The result payload is built by spreading `grounded.model_dump(mode="json")` and
adding `"downgrade_report"` as a sibling key. A comment notes "no key collision since
`ExtractionResult` has no field named `downgrade_report`." This invariant is maintained purely
by convention — the `ExtractionResult` schema (`extra="forbid"`) prevents adding the field
accidentally at runtime, but there is no static check (type annotation, assertion, or test) that
would catch the collision if a future schema change added `downgrade_report` as a field.

**Fix:** Add a one-line guard assertion before the spread, or use a dedicated result wrapper
model instead of a raw `dict` spread:

```python
assert "downgrade_report" not in grounded.model_fields, (
    "ExtractionResult gained a 'downgrade_report' field — result payload key collides"
)
```

---

### IN-03: `FieldStr` / `FieldStr1` duplicate interfaces in generated TS types reduce readability

**File:** `packages/shared-types/index.d.ts:51-111`

**Issue:** `pydantic2ts` generates `FieldStr` (used in `ComparisonResult`) and `FieldStr1` (used
in `ExtractionResult`) as structurally identical interfaces — both are
`{status, value?, evidence?, values?}` — because the generator deduplicates by name, not
structure. Frontend code using `ComparisonResult` and `ExtractionResult` must deal with two
incompatible type names for the same shape. This creates friction for Phase 4 comparison work
when both types appear in the same function.

**Fix:** This is a `pydantic2ts` limitation. Add a single alias in the generated file
(`export type FieldStr = FieldStr1;`) or move to `datamodel-codegen` / manual type maintenance
for this contract. For now, document the equivalence as a comment.

---

_Reviewed: 2026-06-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
