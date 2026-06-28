# Deployment Guide — Bid Desk

How to deploy and verify the Bid Desk prototype end to end. Two services:

| Component | Tech | Host | Live URL |
|---|---|---|---|
| Buyer UI | Next.js (App Router) | **Vercel** | https://rfq-agent-web.vercel.app |
| AI service | FastAPI + LangGraph (Python) | **Render** | https://rfq-agent-ai.onrender.com |

> **Why split hosts:** Vercel is ideal for Next.js but its functions are short-lived and
> can't hold a long-running SSE stream. The AI service streams GPT‑5.4 output over SSE and
> must be a long-running process → Render (or Railway). Vercel hosts **only** the Next.js app.

The browser only ever knows `NEXT_PUBLIC_AI_BASE_URL` (the Render URL). The `OPENAI_API_KEY`
stays server-side on Render and is never shipped to the client.

---

## Prerequisites

- The repo on GitHub (`aayushgupta-dev/rfq-agent`), with the latest `main` pushed.
- A Render account and a Vercel account (sign in with GitHub for both).
- The `OPENAI_API_KEY` and model IDs (`gpt-5.4`, `gpt-5.4-mini`) from your local `.env`.
- `render.yaml` committed at the repo root (Render Blueprint — already in the repo).

**Deploy order:** backend (Render) first, because the frontend needs the backend URL.

---

## 1. Backend → Render (Blueprint)

The repo ships a `render.yaml` Blueprint, so setup is almost entirely declarative:

```yaml
# render.yaml (repo root)
services:
  - type: web
    name: rfq-agent-ai
    runtime: python
    plan: free
    rootDir: services/ai
    buildCommand: pip install uv && uv sync --frozen
    startCommand: uv run uvicorn api.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.12.7"
      - key: OPENAI_API_KEY
        sync: false           # set in the dashboard; never commit
      - key: MODEL_REASONING
        value: gpt-5.4
      - key: MODEL_CHEAP
        value: gpt-5.4-mini
      - key: X_ACCEL_BUFFERING
        value: "no"
```

**Steps (Render dashboard):**

1. **New → Blueprint** → connect the GitHub repo `rfq-agent`.
2. Render reads `render.yaml` and proposes one web service, **`rfq-agent-ai`**, on branch `main`.
3. When prompted, paste **`OPENAI_API_KEY`** (it's `sync:false`, so it's stored only in Render,
   never in git).
4. **Apply / Deploy Blueprint.** First build runs `pip install uv && uv sync --frozen` (~3–5 min),
   then starts uvicorn.
5. Copy the public URL, e.g. `https://rfq-agent-ai.onrender.com`.

**Design notes / gotchas:**

- **No `healthCheckPath`.** The only cheap-ish route, `/data/rfq`, **regenerates the RFQ via
  GPT‑5.4** (a paid call). A health check on it would bill on every ping. Render's default
  port-bind liveness check is free and sufficient.
- **`uv` on Render:** the native Python runtime has `pip`, so `pip install uv && uv sync --frozen`
  bootstraps `uv` and installs from `uv.lock`. `uv run uvicorn …` then uses the synced `.venv`.
- **Free-tier cold start:** the instance spins down after ~15 min idle; the next request takes
  **~50s** to wake. During that window Render's edge returns errors **without** CORS headers,
  which a browser surfaces as a misleading "No 'Access-Control-Allow-Origin'" error. It is *not*
  a CORS bug — warm the service and it clears. Upgrade to a paid instance to stay always-on.

**Verify the backend (no browser needed):**

```bash
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" https://rfq-agent-ai.onrender.com/   # 404 fast once warm (no / route)
curl -s https://rfq-agent-ai.onrender.com/openapi.json | python3 -c "import sys,json;print(*sorted(json.load(sys.stdin)['paths']),sep='\n')"
# CORS preflight from the Vercel origin → must return access-control-allow-origin:
curl -s -D - -o /dev/null -X OPTIONS https://rfq-agent-ai.onrender.com/extract/vendor \
  -H "Origin: https://rfq-agent-web.vercel.app" \
  -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" \
  | grep -i access-control-allow
```

---

## 2. Frontend → Vercel

**Steps (Vercel dashboard):**

1. **Add New → Project** → import `aayushgupta-dev/rfq-agent`.
2. Vercel detects the Turborepo and may default the **Application Preset** to **"Services"**
   (multi-service) — which would also try to deploy the FastAPI service on Vercel.
   **Change the preset to `Next.js`.** We deploy only the web app here; FastAPI is on Render.
3. **Root Directory:** `apps/web` (auto-selected once Next.js is chosen).
4. **Environment Variables:** add
   - `NEXT_PUBLIC_AI_BASE_URL = https://rfq-agent-ai.onrender.com`
   (This is public by design — it's a `NEXT_PUBLIC_` var inlined into the client bundle.)
5. **Deploy.** Build ≈1–2 min.
6. Production URL: `https://rfq-agent-web.vercel.app`. Pushing to `main` auto-redeploys.

**CORS:** the AI service allows `http://localhost:3000` (exact) plus `allow_origin_regex =
https://.*\.vercel\.app`, which covers the production URL **and** all preview deploys — so no
Render change is needed when the Vercel URL is a `*.vercel.app` domain. If you add a **custom
domain**, add it to `allow_origins` in `services/ai/api/app.py` and redeploy Render.

---

## 3. Verify the deployed stack (Playwright, browser-driven)

The same E2E spec runs against the deployed URL — just point `PLAYWRIGHT_BASE_URL` at Vercel:

```bash
# Warm the backend first (free tier cold start) — open the app once, or:
curl -s -o /dev/null https://rfq-agent-ai.onrender.com/data/rfq

PLAYWRIGHT_BASE_URL=https://rfq-agent-web.vercel.app \
  npx playwright test docs/qa/phase5-playwright.spec.ts --reporter=list
```

This is the real product UAT — it drives a Chromium browser through the full buyer journey
(RFQ → vendor input → live extraction → comparison → trace), asserting the rubric behaviours
(evidence snippets present, absence flags surfaced, comparability before ranking, no fabrication).
See `docs/qa/phase5-UAT.md` for the full checklist and what each test proves.

**Manual browser verification (what to look for):**

1. `/rfq` loads instantly (committed RFQ data).
2. `/input` → "Load sample" on a vendor → `/extraction`.
3. `/extraction` streams a progress bar, then renders the **Gaps & Risks** panel, per-field
   **evidence snippets** ("Source:"), and `missing`/`unclear`/`conflicting` flags.
4. `/comparison` (after a 2nd vendor) → **Needs Attention** panel + comparability matrix +
   "Comparability determined in code from evidence — not a model verdict".
5. `/trace` → trace tabs + "Code overruled the model on N verdict(s)" diff.

> **Cost & latency:** every screen makes live GPT‑5.4 calls (RFQ regen, extraction, comparison).
> A full deployed UAT run ≈ several GPT‑5.4 calls. Don't loop it; one pass verifies the journey.

---

## 4. Gated CI/CD pipeline (GitHub Actions)

Pushes to `main` (and manual `workflow_dispatch`) run through a three-job chain
defined in `.github/workflows/deploy.yml`. **The frontend is never deployed against
a stale or dead backend.**

```
test ──► backend ──► frontend
```

| Job | What it does |
|---|---|
| **test** | `uv run pytest` (AI service) + `next build` compile check (web). No `OPENAI_API_KEY` — all tests must pass hermetically. |
| **backend** | Triggers a Render deploy via the REST API (`clearCache: clear`), polls the deploy status every 15 s until `live` (≤15 min), then polls `/health` until `{"status":"ok"}`. Fails the pipeline on any terminal Render status (`build_failed`, `update_failed`, `canceled`, etc.). |
| **frontend** | `vercel build --prod` + `vercel deploy --prebuilt --prod`. Only runs after **backend** succeeds — the `needs: backend` gate enforces this in-engine. |

**Why gate the frontend on the backend?** The buyer UI makes live SSE calls to the AI
service on every screen. Deploying a new frontend against a broken or mid-deploy
backend would serve a live app with a dead API. The `needs:` chain eliminates that
window entirely.

### Required GitHub repository secrets

Set these in **Settings → Secrets and variables → Actions** before the pipeline runs:

| Secret | Used by |
|---|---|
| `RENDER_API_KEY` | backend job — authenticates Render API calls |
| `RENDER_SERVICE_ID` | backend job — identifies the `rfq-agent-ai` Render service |
| `VERCEL_TOKEN` | frontend job — authenticates Vercel CLI |
| `VERCEL_ORG_ID` | frontend job — Vercel team/org scope |
| `VERCEL_PROJECT_ID` | frontend job — identifies the `rfq-agent-web` Vercel project |

### Native auto-deploy disabled

Both platforms' git-triggered auto-deploy is turned off so the workflow is the
**single deploy authority** — no race between a dashboard auto-deploy and the
pipeline:

- `render.yaml`: `autoDeploy: false`
- `apps/web/vercel.json`: `git.deploymentEnabled.main: false`

---

## 5. Operations & troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Browser shows "No 'Access-Control-Allow-Origin'" | Render free-tier **cold start** (502 w/o CORS headers) | Warm it (`curl …/data/rfq`), retry; or upgrade to paid |
| First request hangs ~50s | Cold start | Expected on free tier; warm before demos (D-18) |
| Extraction/comparison spins forever | `NEXT_PUBLIC_AI_BASE_URL` wrong, or backend down | Check the env var in Vercel; curl the Render URL |
| `429 insufficient_quota` in Render logs | OpenAI credits exhausted | Add credits in the OpenAI dashboard |
| Vercel deploys FastAPI too | Preset left on "Services" | Set preset to **Next.js**, root `apps/web`, redeploy |

**Secrets:** `OPENAI_API_KEY` lives only in Render's Environment tab (and your local gitignored
`.env`). If a key is ever exposed (logs, screen shares, transcripts), **rotate it** in the OpenAI
dashboard, update Render, and revoke the old one.

**Updating a deploy:** push to `main` → Render (Blueprint) and Vercel both auto-redeploy.

---

## Architecture references

- System diagram: `docs/architecture/system-diagram.md`
- AI pipeline diagram: `docs/architecture/ai-pipeline-diagram.md`
- UAT checklist + results: `docs/qa/phase5-UAT.md`
