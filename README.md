# Bid Desk — Procurement Copilot

A prompt-driven AI prototype that turns messy, inconsistent vendor proposals into a
grounded, evidence-backed, side-by-side comparison. Built for the Aerchain / Agillos
*Generative AI Expert / Applied AI Engineer* assignment.

## Live Demo

- **App (buyer UI):** https://rfq-agent-web.vercel.app
- **AI service (API):** https://rfq-agent-ai.onrender.com

> The AI service runs on Render's free tier and **spins down after inactivity** — the first
> request can take ~50s to cold-start. Open the app, hit the RFQ screen once, and give it a
> moment to warm before running an extraction or comparison. Every screen runs live GPT‑5.4
> calls (RFQ generation, extraction, comparison), so allow a few seconds per step.

## What It Does

A procurement buyer uploads or pastes vendor responses to an RFQ for marketing services.
The system extracts structured facts from each response (with verbatim evidence snippets),
flags every missing, unclear, conflicting, or unsupported field, compares vendors across
six dimensions, and tells the buyer who is actually comparable — without inventing anything.
The Prompt Trace screen shows the full pipeline: raw model output alongside the
code-enforced grounding and comparability decisions that overruled the model where necessary.

## Architecture

| Layer | Technology | Deployment |
|-------|-----------|------------|
| Buyer UI | Next.js 15 (App Router), Tailwind v4, shadcn/ui | Vercel |
| AI Service | FastAPI + LangGraph, Python 3.12, uv | Render |
| Shared contract | Pydantic schemas → generated TypeScript types | — |
| LLM | OpenAI GPT-5.4 (reasoning), GPT-5.4-mini (cheap tasks) | OpenAI API |

See [docs/architecture/system-diagram.md](docs/architecture/system-diagram.md) and
[docs/architecture/ai-pipeline-diagram.md](docs/architecture/ai-pipeline-diagram.md) for
Mermaid diagrams.

## Prerequisites

- **Node 20+** and **pnpm 9+** (for the web app)
- **Python 3.12** and **uv** (for the AI service)
- **OpenAI API key** with access to `gpt-5.4` and `gpt-5.4-mini`

## Setup

```bash
# 1. Install web dependencies
pnpm install

# 2. Install AI service dependencies
cd services/ai
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (required) and other vars as needed
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | yes | — | OpenAI API key with GPT-5.4 access |
| `MODEL_REASONING` | no | `gpt-5.4` | Model for extraction, comparison, RFQ/vendor gen |
| `MODEL_CHEAP` | no | `gpt-5.4-mini` | Model for cheap tasks (clarification drafting) |
| `NEXT_PUBLIC_AI_BASE_URL` | yes (prod) | `http://localhost:8000` | URL of the AI service (browser-public) |

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`. The AI service reads `.env`
from `services/ai/` at startup. The web app reads `NEXT_PUBLIC_AI_BASE_URL` from the
environment (set in Vercel dashboard for production).

## Run Locally

**Terminal 1 — AI service:**

```bash
cd services/ai
uv run uvicorn api.app:app --reload --port 8000
```

The service starts a startup gate: it makes one test call to verify GPT-5.4 and GPT-5.4-mini
access. If either model is unreachable, startup fails loudly with a clear error.

**Terminal 2 — Web app:**

```bash
pnpm dev
```

Opens at `http://localhost:3000`. The web app communicates with the AI service at
`NEXT_PUBLIC_AI_BASE_URL` (defaults to `http://localhost:8000`).

## Sample Flow

1. Open `http://localhost:3000` — you land on the **RFQ Overview** screen.
   The committed `data/rfq.json` renders immediately; click "Regenerate RFQ" to prove live generation.

2. Navigate to **Vendor Input** and click "Load Sample" on any of the three pre-generated
   messy vendors (Thorough, Cheap, Fluff). This loads the vendor response from the committed
   `data/vendor_*.json` files and triggers a live extraction run.

3. The **Extraction Review** screen shows extracted fields with evidence snippets and flag badges
   (missing / unclear / conflicting / unsupported). Expand an evidence collapsible to see the
   verbatim source passage.

4. Load all three vendors, then navigate to **Comparison**. The system compares across 6 dimensions
   and surfaces which vendors are comparable. The attention panel lists clarification questions.

5. Navigate to **Prompt Trace** and select "Comparison 1" (fixture mode — has known amber clamp rows).
   The "Code vs. Model" section shows where the code overruled the model's comparability verdicts.

## Running Tests

**AI service (Python):**

```bash
cd services/ai
uv run pytest tests/ -q
```

**Streaming verification:**

```bash
curl -N http://localhost:8000/stream/demo
```

Events arrive as `data: {"type": ..., "payload": ...}` — confirms SSE is live and unbuffered.

**End-to-end buyer journey (Playwright):** the product UAT drives a real browser through all
five screens against the running app (local or deployed), asserting the rubric behaviours —
evidence snippets present, absence flags surfaced, comparability before ranking, no fabrication.

```bash
# Local (both servers running):
npx playwright test docs/qa/phase5-playwright.spec.ts --reporter=list
# Against the deployed stack:
PLAYWRIGHT_BASE_URL=https://rfq-agent-web.vercel.app \
  npx playwright test docs/qa/phase5-playwright.spec.ts --reporter=list
```

Full checklist and results: [docs/qa/phase5-UAT.md](docs/qa/phase5-UAT.md).

## Deployment

The app is **live** (see [Live Demo](#live-demo)): the buyer UI on **Vercel** and the AI
service on **Render**. Both auto-redeploy on every push to `main`.

- **AI service → Render** via the committed `render.yaml` Blueprint (root `services/ai`,
  `uv` build, uvicorn start; `OPENAI_API_KEY` set server-only). Deploy backend first.
- **Web → Vercel:** import the repo, set the framework preset to **Next.js** (not the
  multi-service "Services" preset — FastAPI stays on Render), root directory `apps/web`,
  and set `NEXT_PUBLIC_AI_BASE_URL` to the Render URL.
- **CORS** allows `http://localhost:3000` plus `https://*.vercel.app` (regex) — no change
  needed for Vercel domains.
- **Warm the free-tier Render instance before a demo** (`curl https://<render-url>/data/rfq`)
  to avoid the ~50s cold start.

📖 **Full step-by-step guide, gotchas, and verification:**
[docs/architecture/deployment.md](docs/architecture/deployment.md).

## Documentation & Deliverables

The `docs/` folder is the submission package, mapped to the assignment deliverables:

| Deliverable (assignment §9 / §20) | Where |
|---|---|
| Working prototype | This repo — live at [rfq-agent-web.vercel.app](https://rfq-agent-web.vercel.app) |
| Generated sample data (1 RFQ + 3 messy vendors) | `apps/web/public/data/` (rfq + vendor_thorough/cheap/fluff; each vendor carries a `mess_spec` documenting its intentional messiness) |
| Prompt Pack (versioned prompt source) | `services/ai/prompts/` · per-prompt docs in `docs/prompts/` |
| UI/UX generation output | `services/ai/prompts/ui-ux-gen.v1.md` · captured run in `docs/traces/ui-ux-gen-run.md` |
| Extraction & comparison outputs (evidence + clarifications) | Live on the Extraction/Comparison screens · captured traces in `docs/traces/` |
| ≥1 full prompt trace | `docs/traces/` and the in-app **Prompt Trace** screen |
| Write-up (problem, prompt architecture, product thinking, limitations) | `docs/write-up.md` |
| Architecture | `docs/architecture/system-diagram.md`, `ai-pipeline-diagram.md`, `deployment.md` |
| Functional UAT (end-to-end buyer flow) | `docs/qa/phase5-UAT.md` + `docs/qa/phase5-playwright.spec.ts` + `docs/qa/uat-evidence/` |
| Deployment guide | `docs/architecture/deployment.md` |
| Demo video (≤5 min) | `docs/demo/` (script: `demo-script.md`) |
| README (setup, run, env, sample flow, assumptions) | this file |

## Assumptions

- Best-effort text extraction from uploaded files (PDF, DOCX, XLSX, PPTX). Full OCR is not
  required per the assignment brief (§11). For best results, load the committed sample vendors.
- Single-buyer session; no authentication or multi-user isolation.
- GPT-5.4 model family only. The startup gate rejects runs if access cannot be confirmed.
- Extraction and comparison are live (not cached on the server) — results may vary slightly run-to-run.

## Model / API Requirements

- `gpt-5.4` — reasoning-heavy agents (RFQ gen, vendor gen, extraction, comparison).
- `gpt-5.4-mini` — cheap tasks (clarification question drafting).
- Do not substitute `gpt-5.5` — too expensive for this prototype.
- Confirm model access with your OpenAI org before running.
