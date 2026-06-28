---
phase: "05"
plan: "08"
subsystem: buyer-ui-trace-submission
tags: [deploy, render, vercel, cors, sse, blueprint, infrastructure-as-code, ship-01]
dependency_graph:
  requires: ["05-06", "05-07"]
  provides: ["SHIP-01"]
  affects: ["05-09"]
tech_stack:
  added:
    - "render.yaml (Render Blueprint / infrastructure-as-code)"
  patterns:
    - "Render Blueprint deploys the FastAPI AI service (rootDir services/ai, uv build, uvicorn start)"
    - "Vercel deploys ONLY the Next.js app (framework preset Next.js, root apps/web) — NOT the multi-service 'Services' preset, which would also deploy FastAPI on Vercel"
    - "Browser knows only NEXT_PUBLIC_AI_BASE_URL; OPENAI_API_KEY stays server-only on Render (D-24)"
    - "CORS allow_origin_regex https://.*\\.vercel\\.app covers production + preview deploys — no per-URL allowlist edit needed"
key_files:
  created:
    - render.yaml
    - docs/architecture/deployment.md
  modified:
    - README.md
status: executed_not_verified
requirements: ["SHIP-01"]
live_urls:
  web: "https://rfq-agent-web.vercel.app"
  ai: "https://rfq-agent-ai.onrender.com"
decisions:
  - "Deployed via Render Blueprint (render.yaml) instead of manual dashboard config — infrastructure-as-code, reproducible, fewer click-errors"
  - "No healthCheckPath in render.yaml: the only cheap-ish route /data/rfq live-regenerates the RFQ via gpt-5.4 (a paid call); Render's default port-bind liveness check is free and sufficient"
  - "Render build: 'pip install uv && uv sync --frozen' — native Python runtime ships pip; bootstraps uv, installs from uv.lock"
  - "Vercel preset switched from auto-detected 'Services' (multi-service) to 'Next.js' so FastAPI is NOT deployed on Vercel (long-running SSE must stay on Render per CLAUDE.md §12)"
  - "Did NOT add the exact Vercel URL to allow_origins (deviation from plan 05-08 Task 2 Step 1): the existing allow_origin_regex already matches https://rfq-agent-web.vercel.app, so no app.py change or Render redeploy was needed"
deviations:
  - "Plan assumed a CORS edit + Render redeploy after the Vercel URL was known; the regex made this unnecessary. app.py was not modified."
  - "OPENAI_API_KEY was entered into the Render dashboard field, which rendered it in plaintext in the automation snapshot — flagged for rotation (see open_items)"
verification:
  - "Backend liveness: GET / → 404 fast once warm (no / route); GET /openapi.json → 200 with all routes"
  - "CORS (warm): OPTIONS /extract/vendor and GET /data/rfq from Origin https://rfq-agent-web.vercel.app both return access-control-allow-origin: https://rfq-agent-web.vercel.app"
  - "End-to-end on the DEPLOYED stack (browser): loaded a sample vendor → live extraction rendered 60 evidence snippets, 12 absence flags, 6 gaps (missing/conflicting/unclear). Screenshot: docs/qa/uat-evidence/deployed-extraction.png"
open_items:
  - "ROTATE the OPENAI_API_KEY: it was exposed in plaintext during dashboard entry; create a new key, update Render, revoke the old one"
  - "Render free tier cold-starts (~50s) after idle — warm before demos (D-18). Cold-start 502s lack CORS headers and look like a CORS error in the browser (red herring)"
  - "GSD gates still open for this phase: code review, secure-phase, verify-work (UAT). Phase intentionally NOT closed."
metrics:
  completed_date: "2026-06-28"
---

## Plan 05-08 — Deploy (Render + Vercel) + CORS

**SHIP-01 satisfied: both services are live and verified end-to-end on the deployed stack.**

### What was done
1. **AI service → Render** via a new `render.yaml` Blueprint: web service `rfq-agent-ai`,
   `rootDir: services/ai`, build `pip install uv && uv sync --frozen`, start
   `uv run uvicorn api.app:app --host 0.0.0.0 --port $PORT`. Env: `OPENAI_API_KEY` (server-only),
   `MODEL_REASONING=gpt-5.4`, `MODEL_CHEAP=gpt-5.4-mini`, `X_ACCEL_BUFFERING=no`.
   → **https://rfq-agent-ai.onrender.com**
2. **Web → Vercel:** imported the repo, set the framework preset to **Next.js** (not the
   auto-detected multi-service "Services" preset, which would also deploy the FastAPI service),
   root `apps/web`, env `NEXT_PUBLIC_AI_BASE_URL=https://rfq-agent-ai.onrender.com`.
   → **https://rfq-agent-web.vercel.app**
3. **CORS:** confirmed the existing `allow_origin_regex` covers the Vercel domain — no app.py
   change needed (deviation from the plan, which assumed an exact-URL edit + redeploy).
4. **Verified** the live stack: warm CORS headers correct; a full extraction ran in the browser
   on production with grounded evidence + absence flags.
5. **Documented:** `docs/architecture/deployment.md` (full guide) and README "Live Demo" +
   Deployment sections.

### Status
Executed and verified end-to-end, but the phase is **not closed**: code review, security
verification, and human UAT sign-off remain, and the `OPENAI_API_KEY` must be rotated.
