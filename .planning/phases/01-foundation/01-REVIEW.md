---
phase: 01-foundation
reviewed: 2026-06-27T00:00:00Z
depth: standard
files_reviewed: 41
files_reviewed_list:
  - apps/web/app/layout.tsx
  - apps/web/app/page.tsx
  - apps/web/eslint.config.mjs
  - apps/web/next-env.d.ts
  - apps/web/next.config.mjs
  - apps/web/package.json
  - apps/web/tsconfig.json
  - packages/shared-types/index.d.ts
  - packages/shared-types/package.json
  - services/ai/__init__.py
  - services/ai/agents/__init__.py
  - services/ai/agents/_demo.py
  - services/ai/api/__init__.py
  - services/ai/api/app.py
  - services/ai/llm/__init__.py
  - services/ai/llm/factory.py
  - services/ai/prompts/__init__.py
  - services/ai/prompts/clarification.v1.md
  - services/ai/prompts/comparison.v1.md
  - services/ai/prompts/extraction.v1.md
  - services/ai/prompts/messy-data-gen.v1.md
  - services/ai/prompts/registry.py
  - services/ai/prompts/rfq-gen.v1.md
  - services/ai/prompts/ui-ux-gen.v1.md
  - services/ai/prompts/vendor-gen.v1.md
  - services/ai/pyproject.toml
  - services/ai/schemas/__init__.py
  - services/ai/schemas/domain.py
  - services/ai/schemas/envelope.py
  - services/ai/schemas/events.py
  - services/ai/scripts/__init__.py
  - services/ai/scripts/codegen.py
  - services/ai/scripts/verify_access.py
  - services/ai/tests/test_codegen_drift.py
  - services/ai/tests/test_field_envelope.py
  - services/ai/tests/test_llm_factory.py
  - services/ai/tests/test_prompt_registry.py
  - services/ai/tests/test_sse_demo.py
  - services/ai/uv.lock
findings:
  critical: 0
  warning: 6
  info: 5
  total: 11
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-06-27
**Depth:** standard
**Files Reviewed:** 41
**Status:** issues_found

## Summary

Phase 1 lays the foundation contract: the `Field[T]` absence envelope, SSE event taxonomy,
LLM tier factory, prompt registry, pydantic→TS codegen, and shell apps. The 85-test suite
passes and the security-conscious patterns (API key never interpolated into errors, path-traversal
guard on prompt ids, code-enforced absence semantics) are genuinely present and tested.

No BLOCKER-class defects were found — there is no live data path yet, so injection/auth/data-loss
surfaces are minimal. However the reliability machinery in this phase IS the deliverable, and it
has real semantic gaps that will silently admit incoherent envelope states once Phase 3 agents
start producing `Field[T]` objects. The most serious findings are **false "drift guard" guarantees**
(WR-01, WR-02): two modules claim a guarantee in comments/tests that the code does not actually
enforce. Those are exactly the kind of "trust the comment, not the code" gaps CLAUDE.md §2/§8 warns
against, applied to the project's own infrastructure.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `_demo.py` claims an EVENT_TYPES "drift guard" that the code does not enforce

**File:** `services/ai/agents/_demo.py:27,35-41`
**Issue:** Line 27 imports `EVENT_TYPES` with the comment `# noqa: F401 (imported for drift guard;
used below)`. It is **not** used below — `_demo_node` emits hardcoded string literals
(`"status"`, `"partial"`, `"result"`). The module docstring (lines 11-13) makes the same false
claim: "The emitted type values are imported from schemas.events.EVENT_TYPES so the demo cannot
drift from the closed taxonomy." Nothing ties the emitted strings to `EVENT_TYPES`. The `noqa: F401`
actively suppresses the lint warning that would otherwise flag the unused import — so the lie is
load-bearing: it silences the tool that would expose it. If someone renames an event in
`EVENT_TYPES`, this graph keeps emitting the stale literal with no failure here.
**Fix:** Either reference the constant so the import is real, or delete the import + the false claim.
```python
# Couple emitted events to the canonical taxonomy so a rename of EVENT_TYPES fails here.
def _demo_node(state: dict[str, Any]) -> dict[str, Any]:
    w = get_stream_writer()
    assert {"status", "partial", "result"} <= set(EVENT_TYPES)  # fails if taxonomy drops one
    w({"type": "status", "payload": {"message": "Demo graph running", "phase": "demo"}})
    ...
```
The real taxonomy-drift coverage already lives in `test_sse_demo.py::test_all_event_types_in_closed_taxonomy`
(which cross-checks against `EVENT_TYPES`). Simplest correct fix: drop the import and the false
"drift guard" sentences and rely on that test.

### WR-02: `EventEnvelope` / `ErrorPayload` schemas are never used to validate the live SSE stream

**File:** `services/ai/api/app.py:60-64`
**Issue:** The point of `EventEnvelope` (events.py) is that "the set of event names is enforced at
schema validation time, not by convention." But the SSE route bypasses it entirely: `_generate`
does `json.dumps(chunk)` on raw dicts straight from `demo_graph.astream(...)`, and the final `done`
event is also a raw literal dict. Nothing on the emit path constructs or validates an `EventEnvelope`.
A node that emits `{"type": "frobnicate", ...}`, omits `payload`, or adds extra keys would stream to
the client unchecked. The schema is decorative on the one path that emits events. This matters in
P3/P4 when real agents emit dynamically-shaped events — the contract is only as strong as the place
it is enforced, and that is currently nowhere on the wire.
**Fix:** Validate each chunk through the envelope before serializing so a malformed emit fails loudly:
```python
from schemas.events import EventEnvelope

async def _generate() -> AsyncGenerator[dict, None]:
    async for chunk in demo_graph.astream({}, stream_mode="custom"):
        yield {"data": EventEnvelope(**chunk).model_dump_json()}
    yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}
```

### WR-03: Absence envelope admits incoherent states — `present`/`unclear` with conflicting `values[]`, and `missing`/`unsupported` carrying `evidence`

**File:** `services/ai/schemas/envelope.py:105-156`
**Issue:** `_validate_absence_semantics` checks `value` vs `status` and the conflicting `values[]`
rule, but leaves two contradictory combinations valid (confirmed by direct construction):
1. `Field(status=present, value="x", evidence=[ev], values=[ConflictingValue(...)])` — a field that
   is simultaneously a single present fact **and** carries a conflicting-values list. `values` is
   documented as "populated only when status == conflicting" (lines 102-103) but that is never
   enforced for non-conflicting statuses.
2. `Field(status=missing, evidence=[ev])` and `Field(status=unsupported, evidence=[ev])` — an
   absent/unsupported field carrying source evidence snippets. Evidence for something that is, by
   status, not there is incoherent and could surface a snippet in the UI for a field marked missing.

Both violate "absence is first-class, never a suppressed nullable / never misleading" (CLAUDE.md
§1/§8). They pass today only because no agent populates them yet — an LLM in P3 happily will.
**Fix:** Add the mirror constraints to the validator:
```python
# values[] is only meaningful for conflicting status
if status != FlagStatus.conflicting and self.values:
    raise ValueError("values[] may only be populated when status == conflicting")

# absence states must not carry evidence (there is nothing to ground)
if status in (FlagStatus.missing, FlagStatus.unsupported) and self.evidence:
    raise ValueError(f"{status.value!r} status must not carry evidence — nothing is asserted")
```

### WR-04: `ConflictingValue.value` may be `None` while still passing the conflicting-evidence check

**File:** `services/ai/schemas/envelope.py:72-83,116-127`
**Issue:** A conflicting field requires each `ConflictingValue` to have evidence, but does **not**
require the value itself. `Field(status=conflicting, values=[ConflictingValue(value=None,
evidence=[ev])])` is accepted. The semantic of a conflicting field is "vendor says X here, Y there" —
a `None` claim with a source snippet asserts nothing, defeating the side-by-side "both sources" UI
the docstring (lines 75-77) promises. Softer instance of WR-03, but inside the branch the validator
does police.
**Fix:** In the conflicting loop, also reject `None` values:
```python
for i, cv in enumerate(self.values):
    if cv.value is None:
        raise ValueError(f"conflicting values[{i}] must carry a value (a contradiction needs both claims)")
    if not cv.evidence:
        raise ValueError(f"conflicting values[{i}] has no evidence ...")
```
If a deliberately-absent contradictory claim is a real future case, mark it with a `# ponytail:`
comment naming why `None` is allowed — otherwise close it.

### WR-05: Test imports rely on pytest implicitly inserting rootdir on sys.path — fragile, undocumented

**File:** `services/ai/pyproject.toml:37-41`, `services/ai/tests/*.py`
**Issue:** Tests import top-level packages (`from schemas.envelope import ...`,
`from llm.factory import ...`, `from scripts.codegen import ...`) but there is no `conftest.py`, no
`[tool.pytest.ini_options] pythonpath`, and `tests/` has no `__init__.py`. The suite passes today
only because pytest's default rootdir/prepend import mode happens to put `services/ai/` on
`sys.path`. This is brittle: running pytest from a different cwd, switching to
`importmode=importlib`, or packaging the service can break collection with `ModuleNotFoundError`.
The verify-access CLI even hand-patches `sys.path` (verify_access.py:26-28) precisely because the
import root is not declared anywhere — evidence the import strategy is ad hoc.
**Fix:** Declare the source root explicitly so collection does not depend on cwd:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

### WR-06: `verify_access` param-rejection heuristic substring-matches error text and will misclassify

**File:** `services/ai/llm/factory.py:47-55,85-92,127-133`
**Issue:** `_is_param_rejection` lowercases the exception string and checks for substrings including
bare `"400"`. Matching `"400"` anywhere in a message is fragile: a model id, request id, token count,
or timestamp containing `400` (e.g. "context 8400 tokens", a UUID fragment) flips a genuine
access-denied error into the "Param error" branch — the opposite of the PLAT-03 false-negative this
code tries to avoid. The categorization is reliability infrastructure (it decides whether the access
proof passes), so a loose substring match is a real robustness defect, not style.
**Fix:** Prefer the exception's status-code attribute when present, and drop bare `"400"`:
```python
status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
if status == 400:
    return True
msg = str(exc).lower()
return any(m in msg for m in _PARAM_REJECTION_MARKERS)  # remove "400" from the tuple
```

## Info

### IN-01: Dead code — `_ID_RE` defined but never used

**File:** `services/ai/prompts/registry.py:28`
**Issue:** `_ID_RE = re.compile(r"^[a-z0-9-]+$")` is compiled with a "guards against path traversal"
comment but never referenced. `load()` (line 65) re-implements the identical check inline with
`re.fullmatch(r"^[a-z0-9-]+$", prompt_id)`. Two copies of the same regex; one is dead. (The guard
itself works and is tested — only the duplication is the issue.)
**Fix:** Use the compiled constant in `load()` and delete the inline literal:
`if not _ID_RE.fullmatch(prompt_id):`.

### IN-02: `import re` inside `_strip_empty_interfaces` instead of module scope

**File:** `services/ai/scripts/codegen.py:53`
**Issue:** `re` is imported inside the function body; convention is module-level imports (PEP 8). The
defensive regex strip itself is reasonable for a prototype.
**Fix:** Move `import re` to the top of the module.

### IN-03: `EventEnvelope.payload: dict[str, Any] | Any` collapses to `Any` — the dict half is meaningless

**File:** `services/ai/schemas/events.py:50`
**Issue:** `dict[str, Any] | Any` is type-equivalent to `Any`; the union's first member adds no
constraint and the generated TS (`packages/shared-types/index.d.ts:82`) correctly reduces it to
`payload: unknown`. The `dict[str, Any]` half is misleading documentation — it implies a dict shape
that is not enforced.
**Fix:** Pick one: `payload: Any` (honest — shape lands in P3/P4) or `payload: dict[str, Any]`
(enforce object-shaped payloads now). The union is noise.

### IN-04: `app_` lifespan param unused; `# noqa: ANN201` on a context-manager signature

**File:** `services/ai/api/app.py:32`
**Issue:** `async def lifespan(app_: FastAPI)` never uses `app_` (fine for the FastAPI signature),
and the `# noqa: ANN201` suppresses a return-annotation warning. Trivial.
**Fix:** Leave as-is, or annotate the return as `AsyncGenerator[None, None]` and drop the noqa.

### IN-05: Stub domain fields use `# type: ignore[call-arg]` to construct `Field[T](status="missing")`

**File:** `services/ai/schemas/domain.py:33,34,46-48,61-63,76,77`
**Issue:** Every stub default constructs `Field[T](status="missing")` with a `# type:
ignore[call-arg]` because the generic `Field` call confuses the type checker — seven suppressions for
placeholder scaffolding that P2/P3/P4 replace. Acceptable for a stub, but worth a single helper or a
note so the ignores do not propagate into real field definitions later.
**Fix:** Optionally add a `_missing()` factory returning the placeholder `Field`, or note that real
fields in P2+ should not need the ignore.

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
