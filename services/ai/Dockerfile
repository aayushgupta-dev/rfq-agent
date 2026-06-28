# Bid Desk AI service — FastAPI + LangGraph. Build context: REPO ROOT.
# The whole monorepo is copied in so the unmodified pytest suite runs as-is
# (tests read data/, docs/traces/, packages/shared-types and resolve the repo
# root via parents[3] / pnpm-workspace.yaml). We build everything but start ONLY
# the AI server. Single uv base image kept at runtime so the entrypoint can
# `uv run pytest` then `uv run uvicorn`. Deps are layer-cached: lockfiles first.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/app/services/ai/.uv-cache \
    UV_PROJECT_ENVIRONMENT=/app/services/ai/.venv \
    PYTHONUNBUFFERED=1

# curl: required by the compose healthcheck (curl -f http://localhost:8000/health).
# nodejs + json2ts: test_codegen_drift.py regenerates the TS contract via the
# json-schema-to-typescript binary and asserts byte-equality — it needs node +
# the json2ts CLI on PATH (the test falls back to the global `json2ts`).
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl nodejs npm \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g json-schema-to-typescript@15.0.4

WORKDIR /app/services/ai

# Deps first (cached unless pyproject.toml/uv.lock change). Includes the dev group
# so the entrypoint's pytest gate (locked decision 2) can run. No project source yet.
COPY services/ai/pyproject.toml services/ai/uv.lock ./
RUN uv sync --frozen --no-install-project

# Whole monorepo (build everything; start only the AI server). pnpm-workspace.yaml,
# data/, docs/traces/, packages/shared-types land at /app so the tests resolve the
# repo root and read every committed artifact unmodified.
COPY . /app

# Non-root (T-DKR-02). The venv + cache live under /app/services/ai (owned by root
# from the sync above) — chown so the runtime user can write bytecode/.pytest_cache.
RUN groupadd --system app && useradd --system --gid app --no-create-home app \
 && chown -R app:app /app
USER app

EXPOSE 8000

# Locked decision 2: pytest gates startup. The FULL suite runs first; only on exit 0
# does uvicorn exec (a failure exits non-zero → container never serves). The lifespan
# verify_access boot gate (D-16) still runs at uvicorn boot — unchanged.
ENTRYPOINT ["sh", "-c", "uv run pytest -q && exec uv run uvicorn api.app:app --host 0.0.0.0 --port 8000"]
