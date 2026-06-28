---
phase: 04-comparison-agent
reviewed: 2026-06-28T06:58:03Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - services/ai/agents/comparison.py
  - services/ai/api/app.py
  - services/ai/schemas/domain.py
  - services/ai/schemas/__init__.py
  - services/ai/scripts/capture_comparison_trace.py
  - services/ai/tests/conftest_comparison.py
  - services/ai/tests/test_comparison_agent.py
  - services/ai/tests/test_extraction_agent.py
  - packages/shared-types/index.d.ts
findings:
  critical: 2
  warning: 4
  info: 2
  total: 8
status: resolved
resolved: 2026-06-28
---

# Phase 4: Code Review Report

> **Resolution (2026-06-28):** All 8 findings fixed (CR-01, CR-02, WR-01..04, IN-01, IN-02).
> While adding IN-02's route-level test, it surfaced a **critical latent bug**: the comparison
> graph used `StateGraph(dict)`, so LangGraph dropped the `extractions`/`rfq` input channels
> after the align node (which returns `{}`) — the production `astream`/route path KeyError-ed on
> every request. No test caught it because `run_comparison` bypasses the graph. Fixed by adding a
> typed `ComparisonState` schema so all channels persist. Suite: 138 passed / 1 xfailed.
> Remaining `ruff E501` (line-length) warnings are pre-existing style debt across the phase files,
> left unchurned.

**Reviewed:** 2026-06-28T06:58:03Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The comparison agent implementation is architecturally sound. The draft/result split (model proposes, code constructs) is correctly enforced. The verdict clamp is fail-closed for unknown dimension strings, and all six dimensions × N vendors matrix is initialized to `not_comparable` before filling from model output. The offer table, vendor readiness, and attention points are all code-built. Clarification questions are identity-validated against code-collected flagged fields.

Two bugs require fixing before shipping: (1) the `/compare/vendors` route emits a duplicate `done` event because the clarify node already emits one and the route appends another, violating the "exactly one event of each terminal type" invariant that the SSE spec and `test_comparison_sse_taxonomy` assert on the node-level path but miss on the route path; (2) the `ComparisonRequest` validator only enforces an upper bound (`> _MAX_VENDORS`) with no lower bound, allowing zero-vendor submissions through to the graph, where they produce a structurally valid but meaningless empty `ComparisonResult` instead of an error.

Four warnings address missing `unsupported`/`conflicting` coverage in the `compliance_gap` trigger, a repeated-import inside a hot inner loop, an overly broad bare `except Exception` that swallows non-recoverable errors in the compare node, and the `clamp_verdict` function returning an unknown string verbatim when the model bypasses schema coercion.

---

## Critical Issues

### CR-01: Duplicate `done` event on the `/compare/vendors` SSE stream

**File:** `services/ai/api/app.py:210-216`

**Issue:** The `_run_clarify_impl` node emits a `done` event unconditionally on both the error path (line 825) and the success path (line 887). The `compare_vendors` route then appends a second `done` event after `comparison_graph.astream` completes (line 216). Every successful comparison run therefore emits two `done` events. Clients that guard on the first `done` to stop reading will work correctly, but clients that assert "done appears exactly once" (which `test_comparison_sse_taxonomy` does — via the node-level wrapper, not the route) will pass in tests while failing over the actual HTTP endpoint. This also violates the documented invariant in `_run_clarify_impl`'s docstring ("SINGLE final result event") extended to terminal events generally. The same double-emit exists on the error path: `_run_clarify_impl` emits `done` at line 825 when there is no result, and the route appends another.

**Fix:** Remove the route-level appended `done` from `compare_vendors`, since the clarify node already owns the terminal sequence. The extraction agent does NOT emit done internally, so its route-level append is correct and should be kept. Make this asymmetry explicit with a comment:

```python
# compare_vendors route — DO NOT append a done event here.
# The clarify node emits the terminal done unconditionally (lines 825 / 887).
async def _generate() -> AsyncGenerator[dict, None]:
    async for chunk in comparison_graph.astream(
        {"extractions": req.extractions, "rfq": req.rfq},
        stream_mode="custom",
    ):
        yield {"data": EventEnvelope(**chunk).model_dump_json()}
    # no trailing done — clarify node owns it
```

Additionally, add a route-level integration test (not just node-level) that counts done events via `TestClient`.

---

### CR-02: Zero-vendor request bypasses validation and produces silent empty `ComparisonResult`

**File:** `services/ai/api/app.py:188-195`

**Issue:** `ComparisonRequest._check_vendor_count` enforces `> _MAX_VENDORS` (upper bound) but has no lower bound. A POST with `extractions: []` passes validation, flows through all four nodes without error, and emits a `result` event containing a `ComparisonResult` with `vendor_names=[]`, `dimensions=[6 empty-verdict rows]`, `line_item_offers=[]`, `vendor_readiness=[]`. No error event is emitted. The buyer receives a structurally valid but semantically meaningless comparison — absence is not surfaced, which directly violates CLAUDE.md §1 ("absence is first-class, never hidden").

**Fix:** Add a minimum-vendor guard in `_check_vendor_count`:

```python
@model_validator(mode="after")
def _check_vendor_count(self) -> "ComparisonRequest":
    if len(self.extractions) < 2:
        raise ValueError(
            f"At least 2 vendors required for comparison, got {len(self.extractions)}."
        )
    if len(self.extractions) > self._MAX_VENDORS:
        raise ValueError(
            f"Too many vendors: {len(self.extractions)} > {self._MAX_VENDORS} (prototype limit). "
            f"Submit at most {self._MAX_VENDORS} vendors per comparison request."
        )
    return self
```

Minimum is 2 because a single-vendor "comparison" is also meaningless and would produce a `vendor_readiness` list with no peer reference. Add a test stub for this guard in `test_comparison_agent.py`.

---

## Warnings

### WR-01: `compliance_gap` trigger silently misses `unsupported` and `conflicting` compliance status

**File:** `services/ai/agents/comparison.py:549-557`

**Issue:** The `all_have_gap` predicate only checks `(FlagStatus.missing, FlagStatus.unclear)`:

```python
all_have_gap = all(
    len(ext.compliance_points) == 0
    or all(
        cp.status in (FlagStatus.missing, FlagStatus.unclear)
        for cp in ext.compliance_points
        if isinstance(cp, EnvelopeField)
    )
    for ext in extractions
)
```

A vendor with `compliance_points = [Field(status=conflicting)]` or `[Field(status=unsupported)]` evaluates the inner `all()` to `False`, so `all_have_gap` is `False` for that vendor, and no `compliance_gap` trigger fires. But `conflicting` and `unsupported` compliance is equally unverifiable. The ceiling computation (`_ceiling_for_flags`) correctly handles these cases (conflicting → `partially`; unsupported → `not_comparable`), but the attention point trigger — which is the buyer-facing call-out — is silently suppressed. This is a coverage gap in the trigger layer, not the clamp layer.

**Fix:**

```python
_UNVERIFIABLE = (FlagStatus.missing, FlagStatus.unclear, FlagStatus.conflicting, FlagStatus.unsupported)

all_have_gap = all(
    len(ext.compliance_points) == 0
    or all(
        cp.status in _UNVERIFIABLE
        for cp in ext.compliance_points
        if isinstance(cp, EnvelopeField)
    )
    for ext in extractions
)
```

---

### WR-02: `pydantic.BaseModel` imported inside hot inner loop in `_collect_flagged_fields`

**File:** `services/ai/agents/comparison.py:435`

**Issue:** The `_walk` closure inside `_collect_flagged_fields` imports `pydantic.BaseModel` on every invocation:

```python
def _walk(obj: Any, path: str, vendor_name: str) -> None:
    from pydantic import BaseModel as _BaseModel   # line 435
    for field_name in type(obj).model_fields:
        ...
        elif isinstance(value, _BaseModel):
            _walk(value, field_path, vendor_name)
```

`_walk` is recursive and called for every field of every nested model in every `ExtractionResult`. Python caches module imports after the first resolution, so this is not a correctness bug — but it adds a dict lookup (`sys.modules`) on every single recursive call. For a codebase that prioritizes simplicity (CLAUDE.md §2), a module-level import is cleaner and avoids any confusion about intent.

**Fix:** Move the import to the module level alongside the other `pydantic` imports, or import it at the top of `_collect_flagged_fields` (once per call, not once per recursive step):

```python
# At module level or at top of _collect_flagged_fields:
from pydantic import BaseModel as _BaseModel
```

---

### WR-03: `clamp_verdict` returns unknown string verbatim when `model_verdict` is not in `_VERDICT_ORDER`

**File:** `services/ai/agents/comparison.py:155-164`

**Issue:** `_VERDICT_ORDER.get(model_verdict, 0)` maps unknown strings to rank 0. When both `mv` and `cc` are 0 (e.g. `model_verdict="comparable_ish"` with `code_ceiling="not_comparable"`), the condition `mv <= cc` is `0 <= 0 = True`, so the function returns `model_verdict` — the unknown string — unchanged. Downstream, `ComparabilityVerdict(verdict_str)` at line 315 will then raise a `ValueError` crash rather than failing closed to `not_comparable`. This path is structurally prevented by `DimensionVerdictDraft.model_proposed: ComparabilityVerdict` (Pydantic rejects unknown values before they reach `_apply_verdict_clamp`), but the defensive `isinstance` branch at line 281 (`if isinstance(vd.model_proposed, ComparabilityVerdict) else str(vd.model_proposed)`) explicitly acknowledges a fallback to raw string — which re-opens the path.

**Fix:** The default for an unknown verdict should be the fail-closed rank, and the return should be the code ceiling when the model produces an unrecognized value:

```python
def clamp_verdict(model_verdict: str, code_ceiling: str) -> str:
    mv = _VERDICT_ORDER.get(model_verdict)
    if mv is None:
        # Unknown model verdict — fail closed to code ceiling (not the unknown string)
        return code_ceiling
    cc = _VERDICT_ORDER.get(code_ceiling, 0)
    if mv <= cc:
        return model_verdict
    return code_ceiling
```

---

### WR-04: Bare `except Exception` in `_run_compare_impl` swallows non-recoverable errors with `recoverable=False` and no re-raise

**File:** `services/ai/agents/comparison.py:805-816`

**Issue:** The outer `except Exception as exc` block at the end of `_run_compare_impl` catches all exceptions that escape the inner `try` block, emits an error event with `recoverable=False`, and returns `{"error": "comparison_error"}`. This includes `KeyboardInterrupt` (not an `Exception` subclass — fine), but also things like `RecursionError`, `MemoryError` (technically not `Exception` but `BaseException`), import errors, or any programming error in the success path (e.g., a bad field access on `parsed`). For a prototype this is acceptable, but the pattern obscures programming errors that should be surfaced during development — a bad attribute access on `parsed` silently becomes a `comparison_error` event.

More concretely: the `except LengthFinishReasonError` is nested inside the outer `try`, which means that if the inner `except LengthFinishReasonError` block itself raises (e.g., a bug in `ErrorPayload` construction), the outer `except Exception` catches it and emits a misleading `comparison_error`. The outer handler returns without re-raising, so the exception is consumed.

**Fix:** Narrow the outer catch to the set of expected non-model errors, or add a log line that includes the full traceback so programming errors are not silently swallowed:

```python
except Exception as exc:
    logger.exception("Unexpected error in compare node")  # includes traceback
    emit(
        {
            "type": "error",
            "payload": ErrorPayload(
                code="comparison_error",
                message=str(exc),
                recoverable=False,
            ).model_dump(),
        }
    )
    return {"error": "comparison_error"}
```

---

## Info

### IN-01: `MessSpecItem` and `LineItem` not re-exported from `schemas/__init__.py`

**File:** `services/ai/schemas/__init__.py`

**Issue:** `MessSpecItem` and `LineItem` are defined in `schemas/domain.py` and appear in `packages/shared-types/index.d.ts` (discovered transitively through `VendorResponse.mess_spec` and `RFQ.line_items`), but they are not listed in `schemas/__init__.py`'s `__all__`. This means `from schemas import MessSpecItem` fails, and `pydantic2ts --module schemas` may not reliably discover them if the transitive path changes. Currently harmless because `pydantic2ts` discovers them as referenced types, but it creates an inconsistency: some domain types are explicitly exported and some are not.

**Fix:** Add to `schemas/__init__.py`:

```python
from schemas.domain import LineItem, MessSpecItem
```

And add both to `__all__`.

---

### IN-02: `test_comparison_sse_taxonomy` only exercises the node-level path, not the HTTP route

**File:** `services/ai/tests/test_comparison_agent.py:375-462`

**Issue:** `test_comparison_sse_taxonomy` calls `_run_*_impl` functions directly via the `run_comparison` wrapper, bypassing the FastAPI `EventSourceResponse` layer. It correctly asserts exactly one `result` and one `done` event at the node level. However, the route at `compare_vendors` appends an additional `done` event (CR-01 above), and this test cannot catch that because it never exercises the HTTP path. The `test_sse_event_taxonomy` test in `test_extraction_agent.py` correctly uses `TestClient` to cover the full HTTP path — the comparison test should do the same.

**Fix:** Add a `TestClient`-based SSE test for `/compare/vendors` analogous to `test_sse_event_taxonomy` in `test_extraction_agent.py`, counting `done` events in the raw SSE stream.

---

_Reviewed: 2026-06-28T06:58:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
