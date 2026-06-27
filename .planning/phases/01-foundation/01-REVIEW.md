---
phase: 01-foundation
reviewed: 2026-06-27T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - services/ai/schemas/envelope.py
  - services/ai/schemas/events.py
  - services/ai/schemas/domain.py
  - services/ai/scripts/codegen.py
  - services/ai/scripts/verify_access.py
  - services/ai/llm/factory.py
  - services/ai/api/app.py
  - services/ai/agents/_demo.py
  - services/ai/prompts/registry.py
  - packages/shared-types/index.d.ts
findings:
  critical: 3
  warning: 3
  info: 2
  total: 8
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-06-27
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

This is the Phase 1 foundation for Bid Desk — schema contracts, LLM factory, SSE spine, and prompt registry. The structural choices are sound: the `Field[T]` absence envelope, closed SSE taxonomy, `_ID_RE`-guarded prompt loading, and API-key-safe error paths all show care. However, three critical defects undermine the product's most important invariants. The envelope's docstring claims code-enforced grounding but does not enforce it; the `Evidence` model permits semantically impossible offset values; and the `Field[present]` state allows an empty evidence list — meaning an LLM can return an asserted fact with zero grounding and pass schema validation. A secondary concern is that synchronous OpenAI pings block the async event loop at startup. Two minor quality issues round out the findings.

---

## Critical Issues

### CR-01: `Field[present]` Does Not Require Evidence — Grounding Invariant Is Unenforced

**File:** `services/ai/schemas/envelope.py:115-123`

**Issue:** The product's primary reliability contract ("every extracted fact carries a source snippet — if it can't be traced to the source it doesn't get shown as fact", CLAUDE.md §1, §8) is stated in comments and docs but is not enforced by the schema. `_validate_absence_semantics` checks that `status=present` has a non-None `value`, but it does not check that `evidence` is non-empty. Any agent — or an LLM fabricating structured output — can produce `Field(status="present", value="$1,200,000", evidence=[])` and it passes pydantic validation. There is no code barrier between a hallucinated claim and the buyer's comparison screen.

The same gap applies to `status=unclear`: a caller can emit a partial value with zero evidence and it validates cleanly.

**Fix:** Add a check in `_validate_absence_semantics` for both `present` and `unclear`-with-value cases:

```python
elif status == FlagStatus.present:
    if self.value is None:
        raise ValueError(
            "present status requires a value "
            "(use missing/unclear if the information is not available)"
        )
    if not self.evidence:
        raise ValueError(
            "present status requires at least one Evidence item "
            "(every asserted fact must be traceable to a source snippet)"
        )

# status == unclear: partial/tentative info allowed, but if a value is asserted,
# evidence is still required
if status == FlagStatus.unclear and self.value is not None and not self.evidence:
    raise ValueError(
        "unclear status with a value requires at least one Evidence item "
        "(partial facts still need a source)"
    )
```

---

### CR-02: `Evidence` Permits Semantically Impossible Offsets — Grounding Is Not Validated

**File:** `services/ai/schemas/envelope.py:43-54`

**Issue:** The `Evidence` model docstring states "Offsets are computed/validated in code, never trusted from the model (CLAUDE.md §8)." This is false. There is no validator enforcing:

1. `char_start >= 0` — negative offsets are silently accepted.
2. `char_end > char_start` — an LLM can emit `char_start=500, char_end=0` and it validates.
3. That `snippet` matches the source text at those offsets — but this requires the source text and is a Phase 3 concern.

Points 1 and 2 are pure schema-level checks that require no source text. Their absence means a model can emit a structurally valid `Evidence` object that is semantically impossible, and downstream code (or a UI reviewer) would have to independently detect the anomaly. The docstring creates false confidence that the schema catches these cases.

**Fix:** Add a model validator to `Evidence`:

```python
from pydantic import model_validator

@model_validator(mode="after")
def _validate_offsets(self) -> "Evidence":
    if self.char_start < 0:
        raise ValueError(
            f"char_start must be >= 0, got {self.char_start}"
        )
    if self.char_end <= self.char_start:
        raise ValueError(
            f"char_end ({self.char_end}) must be > char_start ({self.char_start})"
        )
    return self
```

Also update the docstring to be precise about what is and is not validated here (offset-against-source-text is deferred to Phase 3 agent logic).

---

### CR-03: `Field[conflicting]` Allows Evidence-Free Conflict Claims

**File:** `services/ai/schemas/envelope.py:101-106`

**Issue:** The `conflicting` status validator (`_validate_absence_semantics`) checks that `values[]` is non-empty. The docstring for `ConflictingValue` says "each contradictory claim becomes a ConflictingValue with its own evidence — so the UI can show 'Vendor says X here, Y there' with both sources." But the validator does not check that each `ConflictingValue` has non-empty `evidence`. A model can emit:

```python
Field(status="conflicting", values=[ConflictingValue(value="$500k"), ConflictingValue(value="$600k")])
```

Both items have `evidence=[]` (the default), yet this passes validation. The buyer sees a conflict with no source for either side — indistinguishable from a fabricated conflict.

**Fix:** Extend the `conflicting` branch of `_validate_absence_semantics`:

```python
if status == FlagStatus.conflicting:
    if not self.values:
        raise ValueError(
            "conflicting status requires non-empty values[] "
            "(each contradictory claim must carry its own evidence)"
        )
    for i, cv in enumerate(self.values):
        if not cv.evidence:
            raise ValueError(
                f"conflicting values[{i}] has no evidence — "
                "every contradictory claim must link to a source snippet"
            )
```

---

## Warnings

### WR-01: Synchronous Blocking Calls in Async Lifespan

**File:** `services/ai/api/app.py:39`

**Issue:** `verify_access()` is a synchronous function that calls `model.invoke("ping")` (also synchronous) for each model tier. It is invoked directly from an `async` lifespan context manager. This blocks the event loop during FastAPI startup. While uvicorn starts a new process for each worker so the block is short-lived and only occurs once, running sync I/O directly in an async context is incorrect and will cause problems if `asyncio.run()` or anyio is used in tests or if the startup path evolves.

**Fix:** Wrap the synchronous call with `asyncio.to_thread`:

```python
import asyncio

@asynccontextmanager
async def lifespan(app_: FastAPI):
    await asyncio.to_thread(verify_access)
    yield
```

Alternatively, create an `async def verify_access_async()` that uses `await asyncio.to_thread(model.invoke, "ping")` for each tier.

---

### WR-02: `_generate()` in `/stream/demo` Has No Exception Handling — Error Event Is Never Emitted

**File:** `services/ai/api/app.py:60-64`

**Issue:** If `demo_graph.astream()` raises an exception (e.g., LangGraph internal error, graph state corruption), the exception propagates through the async generator. `EventSourceResponse` will close the SSE connection without emitting an `error` event. The client receives a partial stream followed by a connection close — indistinguishable from a network drop. The `error` event type and `ErrorPayload` schema exist precisely for this case (D-10) but are never used on this code path.

**Fix:**

```python
async def _generate() -> AsyncGenerator[dict, None]:
    try:
        async for chunk in demo_graph.astream({}, stream_mode="custom"):
            yield {"data": json.dumps(chunk)}
        yield {"data": json.dumps({"type": "done", "payload": {}})}
    except Exception as exc:
        yield {
            "data": json.dumps({
                "type": "error",
                "payload": {
                    "code": "DEMO_GRAPH_ERROR",
                    "message": str(exc),
                    "recoverable": False,
                },
            })
        }
```

---

### WR-03: SSE Events Are Emitted as Raw Dicts Without Schema Validation

**File:** `services/ai/agents/_demo.py:35-41`, `services/ai/api/app.py:62-64`

**Issue:** The demo node emits events using `w({"type": "status", ...})` — raw Python dicts that are serialized directly to SSE without being passed through `EventEnvelope` for validation. The closed-taxonomy guarantee (`Literal["status", "partial", "result", "error", "done"]`) is a schema-level contract that only fires if the model is instantiated. As written, the emit path bypasses it entirely. A future agent developer can copy this pattern and emit `w({"type": "processing", ...})` — it will serialize and stream to the client with no validation error. The test `test_all_event_types_in_closed_taxonomy` catches this after the fact in tests, but not at emit time.

This matters more as real agents (extraction, comparison) get built in Phase 3/4: they will copy this unvalidated pattern.

**Fix:** Validate each event through `EventEnvelope` before emitting. A one-line helper is sufficient:

```python
# In _demo.py or a shared utility:
from schemas.events import EventEnvelope

def _emit(w, type_: str, payload: dict) -> None:
    EventEnvelope(type=type_, payload=payload)  # raises ValidationError on invalid type
    w({"type": type_, "payload": payload})
```

---

## Info

### IN-01: `_ID_RE` Is Compiled but Never Used — Dead Code

**File:** `services/ai/prompts/registry.py:28`

**Issue:** `_ID_RE = re.compile(r"^[a-z0-9-]+$")` is compiled at module level but never referenced. The `load()` function instead calls `re.fullmatch(r"^[a-z0-9-]+$", prompt_id)` inline, recompiling the same pattern on every call. The compiled `_ID_RE` was presumably intended to be used in `load()` but was not wired up.

**Fix:** Remove the unused `_ID_RE` constant and use `_ID_RE.fullmatch(prompt_id)` in `load()` to reuse the compiled pattern:

```python
_ID_RE = re.compile(r"[a-z0-9-]+")  # no anchors needed: fullmatch anchors implicitly

def load(prompt_id: str, base_dir: pathlib.Path = _DIR) -> frontmatter.Post:
    if not _ID_RE.fullmatch(prompt_id):
        raise ValueError(f"invalid prompt_id '{prompt_id}': must match ^[a-z0-9-]+$")
    ...
```

---

### IN-02: Generated TypeScript Emits Structurally Identical but Nominally Distinct Field Types

**File:** `packages/shared-types/index.d.ts:47-165`

**Issue:** `pydantic2ts` monomorphizes every use of `Field[str]` independently, producing `FieldStr`, `FieldStr1`, `FieldStr2`, `FieldStr3`, `FieldStr4` — five structurally identical interfaces for the same logical concept. A TypeScript consumer cannot write a single `processField(f: FieldStr)` helper that accepts all five. This will cause friction for the UI developer in Phase 5 and may result in duplicated UI logic or `as unknown as FieldStrN` casts.

This is a known `pydantic2ts` limitation (noted in RESEARCH.md as "Pitfall 3"). It is not fixable without switching the codegen tool or post-processing the output. Flagged here so the Phase 5 planner accounts for it.

**Fix (short-term):** Add a post-processing step in `codegen.py` after `_strip_empty_interfaces` that collapses all structurally identical `FieldStr*` variants into a single `FieldStr` alias, and similarly for `FieldDecimal*` and `FieldInt*`. Alternatively, accept the limitation and document it in `packages/shared-types/index.d.ts` with a comment block.

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
