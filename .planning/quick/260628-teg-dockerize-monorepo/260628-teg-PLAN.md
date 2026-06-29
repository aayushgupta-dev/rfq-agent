---
phase: quick-260628-teg
plan: 01
type: execute
status: complete
wave: 1
depends_on: []
files_modified:
  - services/ai/api/app.py
  - services/ai/tests/test_health.py
  - services/ai/Dockerfile
  - services/ai/.dockerignore
  - apps/web/Dockerfile
  - .dockerignore
  - infrastructure/docker-compose.yml
  - infrastructure/rfq.sh
  - README.md
  - CLAUDE.md
autonomous: true
requirements: [DOCKERIZE]
user_setup:
  - service: docker
    why: "Live image build + `up` needs a running Docker daemon (down in this env) and the user's real OPENAI_API_KEY (verify_access boot gate). The plan verifies statically; the live build/run is a documented manual handoff."
    env_vars:
      - name: OPENAI_API_KEY
        source: ".env (gitignored) — required at backend container RUNTIME (D-16 verify_access boot gate aborts uvicorn without gpt-5.4/5.4-mini access)"

must_haves:
  truths:
    - "GET /health returns 200 {\"status\":\"ok\"} without any live OpenAI call"
    - "`docker compose -f infrastructure/docker-compose.yml config` validates (project name rfq-agent, images rfq-agent/ai + rfq-agent/web, web depends_on ai service_healthy)"
    - "`bash -n infrastructure/rfq.sh` passes; help text prints on no/unknown subcommand"
    - "README has a 'Run with Docker' section; CLAUDE.md §10 no longer says the compose infra is 'Not built yet'"
  artifacts:
    - path: "services/ai/api/app.py"
      provides: "GET /health endpoint (flat-path, hermetic)"
      contains: "/health"
    - path: "services/ai/tests/test_health.py"
      provides: "hermetic pytest for /health (no key)"
    - path: "services/ai/Dockerfile"
      provides: "multi-stage uv backend image; entrypoint pytest-then-uvicorn"
    - path: "services/ai/.dockerignore"
    - path: "apps/web/Dockerfile"
      provides: "multi-stage pnpm monorepo web image (context=repo root); next build gate; next start :3000"
    - path: ".dockerignore"
      provides: "repo-root ignore for the web build context"
    - path: "infrastructure/docker-compose.yml"
      provides: "rfq-agent-ai + rfq-agent-web services, /health healthcheck, e2e profile, no volumes"
    - path: "infrastructure/rfq.sh"
      provides: "control script: up/down/redeploy/rebuild/logs/e2e/health"
  key_links:
    - from: "infrastructure/docker-compose.yml"
      to: "services/ai/api/app.py GET /health"
      via: "healthcheck curl http://localhost:8000/health"
      pattern: "/health"
    - from: "infrastructure/rfq.sh"
      to: "infrastructure/docker-compose.yml"
      via: "docker compose -f ... -p rfq-agent"
      pattern: "docker compose -f infrastructure/docker-compose.yml -p rfq-agent"
---

<objective>
Dockerize the rfq-agent monorepo end-to-end (backend FastAPI + frontend Next.js), add one control script with a force-rebuild key, add a hermetic backend `/health` endpoint, and sync the docs — without breaking the existing Render/Vercel deploy.

Purpose: one-command local stack (`./infrastructure/rfq.sh up`) with test gates baked into the container lifecycle (backend pytest at runtime entrypoint, frontend `next build` at image-build time), per the locked decisions.
Output: `/health` + test, two Dockerfiles + two .dockerignores, compose, control script, README + CLAUDE.md updates.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@services/ai/api/app.py
@services/ai/pyproject.toml
@apps/web/package.json
@apps/web/next.config.mjs
@package.json
@pnpm-workspace.yaml
@render.yaml

<facts>
- Backend: Python 3.12, uv, deps in pyproject.toml + uv.lock. Entry `uvicorn api.app:app --host 0.0.0.0 --port 8000`. pytest hermetic (~5s, 144 pass / 1 strict-xfail; no key). `pythonpath=["."]`, `testpaths=["tests"]`.
- D-16 LOCKED: app.py lifespan calls verify_access() -> live OpenAI call -> backend container needs OPENAI_API_KEY at RUNTIME to start. Do NOT touch the lifespan.
- Frontend: Next.js 16.2.9, pnpm@10.28.1 via corepack. Web depends on workspace pkg @aerchain/shared-types (packages/shared-types), transpiled (next.config.mjs `transpilePackages`). Build context MUST be repo root (needs root pnpm-lock.yaml + pnpm-workspace.yaml + packages/shared-types + apps/web).
- No runtime disk persistence in request path -> NO docker volumes (YAGNI).
- Docker daemon is DOWN here -> all verify steps are static (pytest, `compose config`, `bash -n`, grep). Live build/up = manual user handoff.
- Existing health pattern is flat: /data/rfq, /stream/demo -> new endpoint is GET /health (matches nomenclature).
- next.config.mjs has NO `output: "standalone"` today -> treat standalone as optional/best-effort; non-standalone `next start` is the acceptable fallback (don't risk breaking the build).
- README sections: ## Run Locally (73), ## Sample Flow (94), ## Deployment (144). CLAUDE §10 "### Docker Compose (placeholder)" at line 251 says "Not built yet" — OUTDATED, rewrite in place.
</facts>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add hermetic GET /health endpoint + test</name>
  <files>services/ai/api/app.py, services/ai/tests/test_health.py</files>
  <behavior>
    - GET /health returns 200 with body exactly {"status": "ok"}
    - No live OpenAI call (no verify_access, no model). The test must reach the route WITHOUT triggering the lifespan's verify_access (which needs a key). Read an existing hermetic test in services/ai/tests/ (e.g. test_input_wrap.py or test_sse_demo.py) FIRST and copy its invocation style: if TestClient runs the lifespan, call the async route handler directly via anyio/asyncio instead, matching the lightest existing hermetic pattern so no key is required.
  </behavior>
  <action>Add `@app.get("/health")` to services/ai/api/app.py returning `{"status": "ok"}` (plain dict, async def, no params). Flat path to match /data/rfq and /stream/demo nomenclature (locked decision 5). Place it near the other GET routes; add a short docstring noting it is the docker-compose healthcheck target and makes no model call. Write services/ai/tests/test_health.py asserting status 200 and body `{"status": "ok"}` WITHOUT a key, mirroring an existing hermetic test's invocation so the verify_access lifespan gate is not triggered. Do NOT modify the lifespan handler.</action>
  <verify>
    <automated>cd services/ai && uv run pytest tests/test_health.py -q</automated>
  </verify>
  <done>GET /health returns 200 {"status":"ok"}; test_health.py passes with no OPENAI_API_KEY set.</done>
</task>

<task type="auto">
  <name>Task 2: Dockerfiles, .dockerignores, compose, control script</name>
  <files>services/ai/Dockerfile, services/ai/.dockerignore, apps/web/Dockerfile, .dockerignore, infrastructure/docker-compose.yml, infrastructure/rfq.sh</files>
  <action>
Backend `services/ai/Dockerfile` — multi-stage, uv-based, layer-cached deps. Base python:3.12-slim with uv copied from `ghcr.io/astral-sh/uv:latest` (or the official uv image). Copy pyproject.toml + uv.lock FIRST, run `uv sync --frozen` (cache layer), THEN copy source. apt-install curl (needed by the compose healthcheck). Non-root user preferred. The entrypoint runs `uv run pytest -q` and only on exit 0 does it `exec uv run uvicorn api.app:app --host 0.0.0.0 --port 8000` — use a small inline shell entrypoint (`sh -c 'uv run pytest -q && exec uv run uvicorn ...'`) so a pytest failure exits non-zero and the container does NOT start (locked decision 2). The lifespan verify_access still runs at uvicorn boot — unchanged.

Backend `services/ai/.dockerignore` — exclude .venv, __pycache__, .pytest_cache, .ruff_cache, *.pyc, .env.

Frontend `apps/web/Dockerfile` — build CONTEXT is repo root. Multi-stage: deps stage enables corepack + pins pnpm@10.28.1, copies root package.json + pnpm-lock.yaml + pnpm-workspace.yaml + packages/shared-types/package.json + apps/web/package.json, runs `pnpm install --frozen-lockfile`. Build stage copies full source (packages/ + apps/web), runs `pnpm --filter @aerchain/web build` (`next build` is the gate — locked decision 3). Runtime stage runs `pnpm --filter @aerchain/web start` (`next start` on :3000). Do NOT add `output: "standalone"` to next.config.mjs — keep non-standalone `next start` (standalone is optional and out of scope to avoid build risk).

Repo-root `.dockerignore` — exclude node_modules, **/.next, .git, .venv, .planning, .turbo, **/__pycache__, *.log (used by the web build whose context is repo root).

`infrastructure/docker-compose.yml`:
- `name: rfq-agent`
- service `rfq-agent-ai`: build context `services/ai`, image `rfq-agent/ai`, container_name `rfq-agent-ai`, ports 8000:8000, env OPENAI_API_KEY / MODEL_REASONING=gpt-5.4 / MODEL_CHEAP=gpt-5.4-mini supplied from `.env`/shell via `${VAR}` (never baked into the image), healthcheck `curl -f http://localhost:8000/health` (sensible interval/timeout/retries, generous start_period since pytest+verify_access run before ready). NO volumes.
- service `rfq-agent-web`: build context `.` (repo root) + dockerfile `apps/web/Dockerfile`, image `rfq-agent/web`, container_name `rfq-agent-web`, ports 3000:3000, env for the AI service base URL — grep apps/web for the existing var name the web app already reads and reuse it (do NOT invent a new one), `depends_on: rfq-agent-ai: condition: service_healthy`.
- service `e2e` under `profiles: ["e2e"]`: runs the existing Playwright spec `docs/qa/phase5-playwright.spec.ts` against the running stack (node base + corepack pnpm + playwright; depends_on web). NOT part of a normal `up`. Document that it needs both services up + a live key.

`infrastructure/rfq.sh` (executable, `#!/usr/bin/env bash`, `set -euo pipefail`) — single script, a case-dispatch over subcommands wrapping `docker compose -f infrastructure/docker-compose.yml -p rfq-agent`:
- `up` -> `up -d --build`
- `down` -> `down`
- `redeploy` -> `up -d --build` (rebuild changed + up)
- `rebuild` -> `build --no-cache` then `up -d` (THE force-rebuild key)
- `logs` -> `logs -f`
- `e2e` -> `--profile e2e up --abort-on-container-exit e2e`
- `health` -> `curl -fsS http://localhost:8000/health`
On no/unknown arg print a Usage help block listing every subcommand, then exit non-zero on unknown. # ponytail: one script, case dispatch — no per-command files, no arg-parse lib.
  </action>
  <verify>
    <automated>docker compose -f infrastructure/docker-compose.yml config >/dev/null && bash -n infrastructure/rfq.sh && test -x infrastructure/rfq.sh && grep -qi "usage" infrastructure/rfq.sh && echo OK</automated>
  </verify>
  <done>compose config validates (project rfq-agent, both services, /health healthcheck, web depends_on ai service_healthy, e2e profile, no volumes, key via env); rfq.sh syntax-clean, executable, prints Usage on bad arg; both Dockerfiles + both .dockerignores exist. Live build/up is a documented manual handoff (daemon down + needs user key).</done>
</task>

<task type="auto">
  <name>Task 3: Sync docs (README + CLAUDE.md)</name>
  <files>README.md, CLAUDE.md</files>
  <action>
README.md — add a "## Run with Docker" section, placed after "## Run Locally" and before "## Sample Flow". Cover: `./infrastructure/rfq.sh up` (build + start), `down`, `redeploy`, `rebuild` (force `--no-cache` — call out as THE no-cache rebuild key), `logs`, `health`, `e2e`. State env requirements: OPENAI_API_KEY + MODEL_REASONING/MODEL_CHEAP from `.env`. Explicitly document: the backend container REQUIRES OPENAI_API_KEY at RUNTIME (verify_access boot gate aborts startup without gpt-5.4/5.4-mini access), pytest gates backend startup (container won't start if tests fail), and `next build` gates the web image. Leave the existing "## Run Locally" (uv + uvicorn for AI, pnpm dev for web) intact as the no-Docker path.

CLAUDE.md — §10: rewrite the "### Docker Compose (placeholder) / Not built yet" subsection (lines ~251–255) IN PLACE to reflect the delivered `infrastructure/docker-compose.yml` + `infrastructure/rfq.sh` (subcommands up/down/redeploy/rebuild/logs/e2e/health; pytest runtime gate; next build gate; backend needs key at runtime; no volumes; e2e is an opt-in profile). Scan §12 (Deployment) and §15 (Gotchas) for now-outdated claims and rephrase minimally; if §12 implies no local container story, add a one-line pointer to §10's compose. Edits MUST be structured, minimal, and placed in their OWNING sections — do NOT append a trailing section or dump into Gotchas (user memory rule: integrate, don't append). No major rewrite.
  </action>
  <verify>
    <automated>grep -q "Run with Docker" README.md && grep -q "rfq.sh" README.md && grep -q "rebuild" README.md && ! grep -q "Not built yet — run the two apps directly" CLAUDE.md && grep -qE "infrastructure/rfq.sh|infrastructure/docker-compose.yml" CLAUDE.md && echo OK</automated>
  </verify>
  <done>README has a "## Run with Docker" section (after Run Locally) covering all rfq.sh subcommands, the no-cache `rebuild` key, runtime OPENAI_API_KEY requirement, and the pytest/next-build gates; the no-Docker "Run Locally" path is intact. CLAUDE.md §10 no longer claims the compose infra is "Not built yet"; it describes the delivered compose + rfq.sh in place. No trailing section appended.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| host shell -> container env | OPENAI_API_KEY and model IDs cross into the backend container via `.env`/shell |
| internet -> web container | Next.js serves on :3000; the only externally exposed app surface in local dev |
| container -> OpenAI API | backend makes live model calls (verify_access on boot, agents at runtime) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-DKR-01 | Information Disclosure | OPENAI_API_KEY in compose/Dockerfile | mitigate | Key passed only via `.env`/shell `${OPENAI_API_KEY}` at runtime; never ARG/ENV-baked into an image layer; `.env` is in both .dockerignores so it is never copied into a build context |
| T-DKR-02 | Elevation of Privilege | backend container process | mitigate | Backend Dockerfile runs as a non-root user |
| T-DKR-03 | Tampering | image build inputs | accept | Bases are official images (python:3.12-slim, ghcr.io/astral-sh/uv, node); deps pinned via uv.lock --frozen + pnpm --frozen-lockfile. No new package installs beyond `curl` (Debian apt) for the healthcheck |
| T-DKR-04 | Denial of Service | startup gates | accept | pytest + verify_access at boot can prevent startup on failure — the intended gate (locked decisions 2 + D-16), not a vulnerability |
</threat_model>

<verification>
- `cd services/ai && uv run pytest tests/test_health.py -q` passes with no key (hermetic).
- `cd services/ai && uv run pytest -q` still green (no regression from the /health addition).
- `docker compose -f infrastructure/docker-compose.yml config` validates without a daemon.
- `bash -n infrastructure/rfq.sh` clean; `test -x infrastructure/rfq.sh` true.
- README + CLAUDE.md grep checks pass; CLAUDE.md no longer says "Not built yet — run the two apps directly".
- render.yaml unchanged (git diff shows no edit) — Render/Vercel deploy intact.
</verification>

<success_criteria>
- GET /health -> 200 {"status":"ok"}, hermetic, with a passing test.
- Backend image: multi-stage uv, layer-cached deps, non-root, entrypoint pytest-then-uvicorn (fail -> container exits).
- Web image: multi-stage pnpm monorepo (context=repo root), `next build` gate, `next start` :3000.
- compose: project `rfq-agent`, images rfq-agent/ai + rfq-agent/web, container names rfq-agent-ai + rfq-agent-web, /health healthcheck, web depends_on ai service_healthy, e2e profile, no volumes, key via env.
- One control script `infrastructure/rfq.sh`: up/down/redeploy/rebuild(--no-cache)/logs/e2e/health + Usage help.
- README "Run with Docker" added; CLAUDE.md §10 synced in place (no append).
- render.yaml + Vercel config untouched.
- Live `docker compose build`/`up` is a documented manual handoff (daemon down here; needs the user's real key for the verify_access boot gate).
</success_criteria>

<output>
Create `.planning/quick/260628-teg-dockerize-monorepo/260628-teg-SUMMARY.md` when done
</output>
