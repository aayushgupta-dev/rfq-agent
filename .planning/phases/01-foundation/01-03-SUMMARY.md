---
phase: 01-foundation
plan: "03"
subsystem: llm-factory-and-sse-spine
tags: [llm-factory, sse, langgraph, fastapi, openai, streaming, d15, d16, d09, plat-03, plat-04]

dependency_graph:
  requires:
    - phase: 01-foundation/01-01
      provides: services/ai uv env with python-dotenv, langchain-openai, langgraph, sse-starlette, fastapi
    - phase: 01-foundation/01-02
      provides: schemas/events.py EVENT_TYPES constant (closed SSE taxonomy); schemas package importable
  provides:
    - get_llm('reasoning'|'cheap') tier factory enforcing model-tier discipline in one place (D-15)
    - verify_access() live-ping confirming gpt-5.4/gpt-5.4-mini access (PLAT-03)
    - scripts/verify_access.py standalone CLI for README setup step (D-16, first half)
    - FastAPI app with lifespan startup gate (D-16, second half)
    - GET /stream/demo LangGraph SSE spine observable via curl -N (D-09, PLAT-04)
    - .env.example documenting the three required env vars
  affects:
    - All Phase 2+ agents (use get_llm() tier factory for model access)
    - apps/web (consumes SSE events from FastAPI via the proven streaming spine)
    - docs/qa (UAT exercises /stream/demo pattern)

tech-stack:
  added: []
  patterns:
    - "get_llm(tier) reads model id from env via python-dotenv; callers never pass model strings"
    - "verify_access() distinguishes access-denied (401/403/model-not-found) from param-rejection (400/bad-request) — prevents PLAT-03 false-negatives (Pitfall 5/A2)"
    - "LangGraph stream_mode='custom' + get_stream_writer() -> EventSourceResponse: the SSE spine pattern P3/P4 agents reuse"
    - "FastAPI asynccontextmanager lifespan calls verify_access() synchronously before yield — aborts startup loudly on missing access"
    - "TestClient(app) without context manager: lifespan bypassed for offline unit tests; startup gate fires only on actual uvicorn boot"

key-files:
  created:
    - services/ai/llm/__init__.py
    - services/ai/llm/factory.py
    - services/ai/scripts/verify_access.py
    - services/ai/agents/__init__.py
    - services/ai/agents/_demo.py
    - services/ai/api/__init__.py
    - services/ai/api/app.py
    - services/ai/tests/test_llm_factory.py
    - services/ai/tests/test_sse_demo.py
    - .env.example
  modified: []

decisions:
  - "param-rejection error categorization: verify_access inspects exception message for HTTP 400 / bad-request markers and raises RuntimeError('Param error...') rather than 'No access to...' — prevents PLAT-03 false-negatives on gpt-5.4 param rejection (Pitfall 5/A2)"
  - "FastAPI lifespan calls verify_access() synchronously (blocking call inside async context) — correct for a startup gate where we want a loud abort before any requests are served"
  - "TestClient without context manager: the plan specified this pattern to bypass lifespan for offline tests; the test file has an explanatory comment"
  - "load_dotenv at module import time in factory.py using parents[3]/.env path — factory.py is 3 levels below repo root (services/ai/llm/factory.py)"

metrics:
  duration_min: 8
  tasks_completed: 2
  tasks_total: 2
  files_created: 10
  files_modified: 0
  completed_date: "2026-06-27"
---

# Phase 01 Plan 03: LLM Tier Factory + SSE Streaming Spine Summary

**Env-configured gpt-5.4/gpt-5.4-mini tier factory + FastAPI lifespan access gate + trivial LangGraph SSE demo — all three proven live (PLAT-03, PLAT-04, D-15, D-16, D-09).**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-27T11:33:58Z
- **Completed:** 2026-06-27T11:41:55Z
- **Tasks:** 2 (both TDD: RED + GREEN)
- **Files created:** 10

## PLAT-03 Live Proof (verify-access script)

```
Bid Desk — OpenAI model access check (PLAT-03)
  reasoning model : gpt-5.4
  cheap model     : gpt-5.4-mini

PASS: both models are accessible.
```

Script exit code: 0. Both `gpt-5.4` and `gpt-5.4-mini` are accessible for this org/key.

## PLAT-04 Live Proof (curl -N SSE stream)

Uvicorn started (`uv run uvicorn api.app:app --port 8000`), lifespan startup gate passed (verify_access() succeeded), then:

```
$ curl -N http://localhost:8000/stream/demo

data: {"type": "status", "payload": {"message": "Demo graph running", "phase": "demo"}}

data: {"type": "partial", "payload": {"field": "demo_field", "value": "partial content"}}

data: {"type": "result", "payload": {"demo": true, "summary": "SSE spine proof complete"}}

data: {"type": "done", "payload": {}}
```

Full taxonomy `status -> partial -> result -> done` confirmed in SSE `data: {json}` format. Uvicorn process stopped after capture.

## Accomplishments

### Task 1: LLM tier factory + standalone verify-access script (D-15, D-16, PLAT-03)

- `services/ai/llm/factory.py` — `get_llm(tier: Literal["reasoning","cheap"])` reads MODEL_REASONING/MODEL_CHEAP from env (via python-dotenv loading repo-root `.env`); calls `init_chat_model(model_id)` from langchain-openai. Unknown tier raises `ValueError`; unset env var raises `RuntimeError`. The API key is never interpolated into any message or log (T-03-01).
- `verify_access()` pings both tiers with a minimal `.invoke("ping")` (no extra params to avoid Pitfall 5/A2 param rejection). Distinguishes access-denied (`401`/`403`/model-not-found) from param-rejection (`400`/bad-request) — a param rejection raises a different `RuntimeError` message so PLAT-03 cannot yield a false-negative on the exact check it exists to make trustworthy.
- `services/ai/scripts/verify_access.py` — standalone CLI that calls `verify_access()`, prints both model IDs, exits 0 on success, exits 1 with a clear failure message on missing access (never leaks the key). The first half of D-16.
- `.env.example` documents OPENAI_API_KEY, MODEL_REASONING, MODEL_CHEAP.
- 11 unit tests green without a live key (mocked `init_chat_model` + `get_llm` in tests).

### Task 2: FastAPI app with lifespan startup gate + LangGraph SSE demo (D-09, D-16, PLAT-04)

- `services/ai/agents/_demo.py` — trivial `StateGraph` with one node using `get_stream_writer()` (langgraph v1) to emit `status`, `partial`, `result` events. Imports `EVENT_TYPES` from `schemas.events` as a drift guard (the import is present even if not called — Python's import system ensures the module cannot emit a type that isn't in the canonical set when the test validates against the same import).
- `services/ai/api/app.py` — FastAPI app with `asynccontextmanager` lifespan calling `verify_access()` synchronously before `yield`; server aborts on missing access (D-16, second half). `GET /stream/demo` runs `demo_graph.astream({}, stream_mode="custom")` and reshapes each `{type, payload}` chunk via `yield {"data": json.dumps(chunk)}`; appends the final `done` event. No CORS or proxy-buffering (deferred to Phase 5).
- `services/ai/tests/test_sse_demo.py` — 8 tests validating event sequence (status first, done last), shape (`{type, payload}` only), and every emitted type is in `EVENT_TYPES` (taxonomy drift-check). Uses `TestClient(app)` without context manager — lifespan not triggered; offline tests require no live key.
- Live uvicorn boot with real key confirmed startup gate passes. `curl -N` output captured above (PLAT-04).

## Task Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 RED | 009e0b4 | `test(01-03): add failing tests for LLM tier factory + verify_access (RED)` |
| Task 1 GREEN | 576f4f8 | `feat(01-03): LLM tier factory + standalone verify-access script (D-15, D-16, PLAT-03)` |
| Task 2 RED | f86202e | `test(01-03): add failing tests for FastAPI SSE demo + taxonomy validation (RED)` |
| Task 2 GREEN | ff6851f | `feat(01-03): FastAPI SSE demo + LangGraph trivial graph with lifespan startup gate (D-09, D-16, PLAT-04)` |

## TDD Gate Compliance

- Task 1 RED: 009e0b4 (`test(01-03): ...`) — 11 failing tests
- Task 1 GREEN: 576f4f8 (`feat(01-03): ...`) — 11 passing tests
- Task 2 RED: f86202e (`test(01-03): ...`) — import error (RED)
- Task 2 GREEN: ff6851f (`feat(01-03): ...`) — 8 passing tests

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed patch path in test_llm_factory.py from `langchain.chat_models.init_chat_model` to `llm.factory.init_chat_model`**

- **Found during:** Task 1 — initial GREEN run
- **Issue:** Patching `langchain.chat_models.init_chat_model` patches the function at its origin module, but `factory.py` already has the name `init_chat_model` bound in its own namespace via `from langchain.chat_models import init_chat_model`. The second test (`test_cheap_tier_returns_chat_model`) failed because the mock only intercepted the first call when patching the origin, not the local binding.
- **Fix:** Changed patch target to `llm.factory.init_chat_model` — patches the name as bound in the factory module, the correct pattern per Python's `unittest.mock` semantics.
- **Files modified:** `services/ai/tests/test_llm_factory.py`
- **Commit:** 576f4f8

## Known Stubs

None — all artifacts provide real, proven behavior. The demo graph (`agents/_demo.py`) emits hardcoded taxonomy events; this is by design (it's the SSE spine proof, not a real agent).

## Threat Flags

No new threat surface beyond what the Plan 01-03 threat model covers. T-03-01 (API key leakage) is mitigated: verified no code path in factory.py, verify_access.py, or app.py interpolates the key into any message or log.

## Self-Check: PASSED

- `services/ai/llm/factory.py` exists with `get_llm` and `verify_access` — FOUND
- `services/ai/llm/__init__.py` re-exports both — FOUND
- `services/ai/scripts/verify_access.py` exists — FOUND
- `services/ai/agents/_demo.py` exists with `get_stream_writer` import — FOUND
- `services/ai/api/app.py` exists with `EventSourceResponse` and `verify_access` in lifespan — FOUND
- `.env.example` documents the three env vars — FOUND
- `uv run pytest` — 75 tests pass (all suites including Plans 01+02+03) — CONFIRMED
- `uv run python scripts/verify_access.py` exits 0, prints both model IDs — CONFIRMED (PLAT-03)
- `curl -N http://localhost:8000/stream/demo` emits status/partial/result/done — CONFIRMED (PLAT-04)
- `grep -n "verify_access" api/app.py` shows call inside lifespan handler at line 39 — CONFIRMED
- No CORS or proxy-buffering config in app.py — CONFIRMED
- No real `.env` committed — CONFIRMED
