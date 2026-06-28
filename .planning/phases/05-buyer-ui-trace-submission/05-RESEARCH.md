# Phase 5: Buyer UI, Trace & Submission — Research

**Researched:** 2026-06-28
**Domain:** Next.js App Router UI, FastAPI CORS/file upload, SSE client consumption, Python file parsing, deployment (Vercel + Render), prompt docs, submission package
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01**: Guided stage rail (persistent left nav, RFQ → Input → Extraction → Comparison → Trace).
- **D-02**: Live, session-cached results (real OpenAI pipeline; session cache prevents re-runs).
- **D-03**: Substance-first + hero polish (shadcn baseline everywhere; concentrate polish on evidence snippets, flag states, comparability matrix).
- **D-04**: One-click sample load is the hero path (3 committed vendors, instant, no spinner).
- **D-05**: All four upload formats, best-effort, with paste fallback (PDF/DOCX/XLSX/PPTX; weak-extraction Alert prompts paste).
- **D-06**: Minimal raw-text wrap; buyer names the vendor (raw text → VendorResponse.raw_text + buyer-given vendor name; extraction agent does all structuring).
- **D-07**: Inline evidence + source on drill-down (evidence snippet always visible under each fact; Collapsible opens source passage with span highlighted).
- **D-08**: Top gaps & risks panel + inline badges (always-visible panel listing every non-`present` flag; color-coded badges inline).
- **D-09**: By-category layout under the gaps panel (scope, pricing, commercial_terms, timeline, compliance, assumptions, exclusions, risks).
- **D-10**: One vendor at a time on Extraction Review (vendor Tabs).
- **D-11**: Matrix-first on Comparison (comparability matrix hero; line-item table and narrative on drill-down).
- **D-12**: Always-visible clarifications/attention panel on Comparison.
- **D-13**: Stable input order + explicit no-rank framing (vendors never sorted; readiness X/N labelled "Data readiness", not a score).
- **D-14**: Clamp note on Comparison; full diff in Trace ("code disproves model" story lives in Trace).
- **D-15**: Full trace + Prompt Pack list in-app (renders existing `docs/traces/*.json`; no new capture needed).
- **D-16**: Author + run ui-ux-gen once, build React by hand (prompt + captured artifact = 10% deliverable).
- **D-17**: Prompt docs in `docs/prompts/`, fold PROMPT-04 here (one doc per prompt; include PROMPT-04 failure example + versioning notes).
- **D-18**: Render, warmed before demo (AI service → Render; proxy buffering disabled; warm before recording).
- **D-19**: Rubric-driven demo arc (load messy vendor → gaps with evidence → non-comparable + clarifications → code-disproves-model trace).
- **D-20**: Mermaid + Markdown for all docs.
- **D-21**: Committed RFQ by default + regen button.
- **D-22**: Full, grouped render with summary on top.
- **D-23**: fetch + ReadableStream for POST-SSE (endpoints stay POST; native EventSource is GET-only).
- **D-24**: Base URL public, OpenAI key server-only (NEXT_PUBLIC_AI_BASE_URL; no Next.js proxy layer).
- **D-25**: Stream progress + explicit errors (status events as progress; explicit error Alert; never blank screen).
- **D-26**: Fully responsive UI (reflow, not redesign; AI-showcase surfaces legible at narrow widths).

### Claude's Discretion
- Exact component breakdown, shadcn primitives used, file/route structure under `apps/web/app/(buyer)/`.
- Text-extraction libraries per upload format (D-05) and the empty-extraction threshold for paste-fallback.
- Client SSE parser implementation, session-cache mechanism (D-02), and loading/skeleton treatment.
- Mermaid diagram contents/granularity; README + write-up section ordering (within the rubric).
- How many prompts get a standalone `docs/prompts/` file vs a shared doc, and which prompt's failure becomes the PROMPT-04 example.
- Whether the new raw-text input path is a new endpoint or a thin wrapper before `/extract/vendor`.

### Deferred Ideas (OUT OF SCOPE)
- Loadable committed AI result (reads as hardcoded — rejected).
- Next.js proxy layer for AI calls (rejected — D-24).
- Stateful clarification → re-extraction feedback loop (v2: FLOW-01/FLOW-02).
- Production OCR / layout-aware parsing (v2: INPUT-05).
- Mobile-redesigned layouts (D-26 builds reflow, not bespoke mobile experience).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INPUT-01 | Buyer can paste text/Markdown/JSON as vendor response | D-06: thin raw-text wrapper endpoint feeds existing `/extract/vendor` |
| INPUT-02 | Buyer can upload PDF/Word/Excel/PPT; text extracted best-effort | D-05: Python libs (pypdf, python-docx, openpyxl, python-pptx) — NEW backend endpoint |
| INPUT-03 | Buyer can load a pre-generated sample vendor in one click | D-04: `data/vendor_{thorough,cheap,fluff}.json` read client-side, posted to extract endpoint |
| INPUT-04 | AI output generated dynamically from whatever input is provided | D-02: session cache; extraction always calls live `/extract/vendor` |
| UI-01 | RFQ Overview screen | `data/rfq.json` + `GET /data/rfq`; D-21/D-22 |
| UI-02 | Vendor Upload/Input screen | INPUT-01..03 + D-04..D-06 |
| UI-03 | Extraction Review screen | Renders `ExtractionResult`; D-07..D-10 |
| UI-04 | Vendor Comparison screen | Renders `ComparisonResult`; D-11..D-14 |
| UI-05 | Prompt Trace / Prompt Pack screen | Renders `docs/traces/*.json`; D-15 |
| UI-06 | Buyer-first information hierarchy | Gaps/risks surfaced first; drill-down for detail; all screens |
| PROMPT-02 | Each major prompt documented (what/why/how it handles unreliable info) | `docs/prompts/` — one doc per of the 7 prompts |
| SHIP-01 | Web → Vercel, AI service → Render; CORS + disabled proxy buffering | FastAPI CORSMiddleware + Render env var; Vercel deploy via CLI/dashboard |
| SHIP-02 | README | `README.md` at repo root |
| SHIP-03 | 1–2 page write-up | `docs/write-up.md` |
| SHIP-04 | ≤5-min demo video | `docs/demo/` script + recording |
| SHIP-05 | Architecture diagram (system + AI pipeline) | `docs/architecture/` — Mermaid |
</phase_requirements>

---

## Summary

Phase 5 is entirely greenfield on the frontend and thin additions on the backend. The AI pipeline (Phases 1–4) is complete and frozen; this phase renders its outputs in a Next.js App Router UI and ships the submission package.

The frontend is built on a working substrate: `apps/web` has Next.js 16 / React 19.2, Tailwind v4 (CSS-first), shadcn/ui initialized (`components.json`, `button.tsx`, `lib/utils.ts`), and the `@aerchain/shared-types` workspace link. No screen routes exist yet — `app/(buyer)/` is unbuilt. The sole page is a placeholder proof-of-concept.

The backend needs three additions: (1) FastAPI CORSMiddleware, (2) a file text-extraction endpoint (`POST /extract/file-text`) using Python file-parsing libs not yet in the venv, (3) a raw-text-to-VendorResponse wrapper endpoint or in-endpoint path. The existing SSE endpoints (`POST /extract/vendor`, `POST /compare/vendors`) work correctly and are not touched.

The trace screen is ready-made content: `docs/traces/*.json` contains 7 trace files with a consistent structure (`input`, `resolved_prompt`, `raw_model_output`, `grounding_step`/`clamp_step`, `clarification_step`, `final_result`). The extraction traces have `grounding_step.downgrade_report`; comparison traces have `clamp_step.entries` — both are the "code disproves model" proof the demo needs.

**Primary recommendation:** Build in two parallel streams — (A) Next.js screens in `app/(buyer)/`, reading the UI-SPEC.md design contract; (B) backend additions (CORS, file-extract endpoint, raw-text wrapper). Ship to Vercel + Render only after both streams are complete and local E2E passes.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Stage rail + buyer journey routing | Browser/Client | — | Pure navigation; no AI involvement |
| SSE stream consumption (extraction, comparison) | Browser/Client | — | `fetch + ReadableStream` direct to AI service (D-23/D-24) |
| Session cache (ExtractionResult, ComparisonResult) | Browser/Client | — | `sessionStorage` or React Context; server not involved |
| File text extraction (PDF/DOCX/XLSX/PPTX) | API/Backend | — | Python libs do heavy parsing; client sends raw bytes; result is plain text |
| Raw-text → VendorResponse wrap | API/Backend | — | Thin new endpoint; feeds existing `/extract/vendor` contract |
| CORS + proxy buffering | API/Backend | CDN/Deploy | FastAPI middleware + Render env flag |
| RFQ default render | Browser/Client | API/Backend | Client reads committed `data/rfq.json`; regen button calls `GET /data/rfq` |
| Trace screen render | Browser/Client | — | Static render from committed `docs/traces/*.json` served alongside the app |
| Prompt Pack list render | Browser/Client | API/Backend | Client reads prompt frontmatter from traces JSON (id, version, intent already embedded); no runtime registry call needed |
| Submission docs (README, write-up, diagrams, demo) | — (docs layer) | — | Pure documentation authoring, not a runtime tier |
| Playwright E2E UAT | Browser/Client | — | Tests run against running app; `docs/qa/` captures the script |

---

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| Next.js | 16.2.9 [VERIFIED: package.json] | App Router framework | Already in `apps/web` |
| React | 19.2.7 [VERIFIED: package.json] | UI rendering | Already installed |
| Tailwind CSS | 4.3.1 [VERIFIED: package.json] | CSS-first styling; CSS variables design tokens | Already configured |
| shadcn/ui | — (vendored source) [VERIFIED: components.json] | Radix + Tailwind component source | Initialized; `button.tsx` exists |
| lucide-react | ^1.21.0 [VERIFIED: package.json] | Icon set | Already installed |
| clsx / tailwind-merge | ^2.1.1 / ^3.6.0 [VERIFIED: package.json] | Class composition (`cn`) | `lib/utils.ts` exists |
| @aerchain/shared-types | workspace:* [VERIFIED: package.json] | TS mirror of pydantic schemas | Already wired |

### New Frontend (shadcn components to add)

Add via `npx shadcn@latest add <name>` from `apps/web/`. [VERIFIED: ui.shadcn.com registry; `components.json` confirms official registry, no third-party blocks]

| Component | shadcn name | Purpose |
|-----------|-------------|---------|
| Badge | `badge` | Flag + comparability badges |
| Card | `card` | Primary surface container |
| Tabs | `tabs` | Vendor picker (Extraction), trace selector |
| Separator | `separator` | Section dividers |
| Textarea | `textarea` | Paste path (D-06) |
| Input | `input` | Vendor name field (D-06) |
| Progress | `progress` | SSE streaming progress bar (D-25) |
| Skeleton | `skeleton` | Loading treatment while SSE streams |
| Alert | `alert` | Error states (D-25), weak-extraction warning (D-05) |
| Tooltip | `tooltip` | Matrix cell reasons, flag badge explanations |
| Collapsible | `collapsible` | Evidence drill-down (D-07), comparison drill-down |
| ScrollArea | `scroll-area` | Stage rail mobile scroll, Trace raw output |

**Install command:**
```bash
cd apps/web && npx shadcn@latest add badge card tabs separator textarea input progress skeleton alert tooltip collapsible scroll-area
```

### New Backend (Python — NOT yet in venv)

| Library | PyPI | Version | Purpose | Status |
|---------|------|---------|---------|--------|
| pypdf | PyPI | 6.14.2 [VERIFIED: PyPI] | PDF text extraction | NOT in venv |
| python-docx | PyPI | 1.2.0 [VERIFIED: PyPI] | DOCX text extraction | NOT in venv |
| openpyxl | PyPI | 3.1.5 [VERIFIED: PyPI] | XLSX text extraction | NOT in venv |
| python-pptx | PyPI | 1.0.2 [VERIFIED: PyPI] | PPTX text extraction | NOT in venv |
| python-multipart | PyPI | 0.0.32 [VERIFIED: PyPI] | FastAPI `UploadFile` / `multipart/form-data` | NOT in venv |

**Add to `pyproject.toml` dependencies, then `uv sync`:**
```
"pypdf>=6.14.2",
"python-docx>=1.2.0",
"openpyxl>=3.1.5",
"python-pptx>=1.0.2",
"python-multipart>=0.0.32",
```

Note: `python-multipart` is a FastAPI requirement for `UploadFile` — without it FastAPI raises a 422 at runtime, not at import time.

---

## Package Legitimacy Audit

> slopcheck was not available at research time (install failed — not in PATH). All PyPI packages below confirmed via direct PyPI API query. All are long-established, high-download libraries with clear source repos. Planner should add a `checkpoint:human-verify` before venv install if slopcheck cannot be run.

| Package | Registry | Age | Source Repo | Disposition |
|---------|----------|-----|-------------|-------------|
| pypdf | PyPI | ~10 yrs (PyPDF2 lineage) | github.com/py-pdf/pypdf | Approved [CITED: pypi.org/project/pypdf] |
| python-docx | PyPI | ~12 yrs | github.com/python-openxml/python-docx | Approved [CITED: pypi.org/project/python-docx] |
| openpyxl | PyPI | ~14 yrs | foss.heptapod.net/openpyxl/openpyxl | Approved [CITED: pypi.org/project/openpyxl] |
| python-pptx | PyPI | ~11 yrs | github.com/scanny/python-pptx | Approved [CITED: pypi.org/project/python-pptx] |
| python-multipart | PyPI | ~10 yrs | github.com/andrew-d/python-multipart | Approved [CITED: pypi.org/project/python-multipart] |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck unavailable — all packages tagged `[ASSUMED]` until verified. Planner must gate each `uv add` behind a `checkpoint:human-verify` task.*

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (Vercel — Next.js App Router)
  │
  │  fetch + ReadableStream (POST, SSE data: lines)
  │  NEXT_PUBLIC_AI_BASE_URL
  ▼
FastAPI AI Service (Render)
  ├─ CORS allowlist: Vercel domain + localhost
  ├─ POST /extract/file-text  ← NEW: UploadFile → extracted text string
  ├─ POST /extract/vendor     ← EXISTING: VendorResponse + RFQ → SSE ExtractionResult
  ├─ POST /compare/vendors    ← EXISTING: ExtractionResult[] + RFQ → SSE ComparisonResult
  ├─ GET  /data/rfq           ← EXISTING: live RFQ regen
  └─ POST /data/vendor-gen   ← EXISTING: persona → VendorResponse regen

Browser session cache (sessionStorage / React Context)
  ├─ loadedVendors: VendorResponse[]  (sample load / paste / upload)
  ├─ extractions: ExtractionResult[]  (per-vendor, keyed by vendor_name)
  └─ comparison: ComparisonResult     (most recent run)

Static committed data (served alongside Next.js app)
  ├─ data/rfq.json
  ├─ data/vendor_{thorough,cheap,fluff}.json
  └─ docs/traces/*.json  (7 trace files, rendered by Trace screen)
```

### Recommended Route Structure

```
apps/web/app/
  layout.tsx                  ← root layout (html/body, no chrome)
  page.tsx                    ← redirect → /rfq
  (buyer)/
    layout.tsx                ← stage rail + main content wrapper (D-01)
    rfq/page.tsx              ← UI-01 RFQ Overview
    input/page.tsx            ← UI-02 Vendor Input
    extraction/page.tsx       ← UI-03 Extraction Review
    comparison/page.tsx       ← UI-04 Vendor Comparison
    trace/page.tsx            ← UI-05 Prompt Trace
  lib/
    sse.ts                    ← fetch+ReadableStream SSE parser (D-23)
    session.ts                ← session cache read/write helpers (D-02)
    api.ts                    ← typed wrappers for AI service calls
  contexts/
    BuyerContext.tsx          ← React Context holding session state (D-02)
  components/
    ui/                       ← shadcn vendored components
    stage-rail.tsx            ← stage rail nav (D-01)
    flag-badge.tsx            ← FlagStatus → Badge color mapping (D-08)
    comparability-badge.tsx   ← ComparabilityVerdict → Badge (D-11)
    evidence-snippet.tsx      ← inline snippet + Collapsible drill-down (D-07)
    stream-progress.tsx       ← Progress + status text (D-25)
```

### Pattern 1: POST-SSE client consumer (D-23)

The AI service endpoints are `POST` (they carry full request bodies). Native `EventSource` is GET-only. The correct client pattern is `fetch` with `response.body.getReader()`:

```typescript
// lib/sse.ts — ponytail: one generic parser handles all SSE endpoints
// Source: Next.js docs + MDN ReadableStream

export type EventEnvelope = { type: string; payload: unknown };

export async function* streamSSE(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<EventEnvelope> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE lines: "data: <json>\n\n"
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      if (part.startsWith("data: ")) {
        yield JSON.parse(part.slice(6)) as EventEnvelope;
      }
    }
  }
}
```

[VERIFIED: Next.js docs streaming guide — ReadableStream + getReader pattern confirmed current for App Router]

### Pattern 2: Session cache (D-02)

Use `sessionStorage` (survives navigation within tab, cleared on tab close) with a thin React Context wrapper. No server involvement.

```typescript
// contexts/BuyerContext.tsx
"use client";
// Store ExtractionResult[] and ComparisonResult in sessionStorage.
// React state hydrated on mount from sessionStorage.
// ponytail: sessionStorage is tab-scoped; correct for a single-buyer prototype.
```

JSON-serialize with `JSON.stringify`; deserialize with `JSON.parse`. The types come from `@aerchain/shared-types`.

### Pattern 3: File text extraction backend endpoint (D-05)

New FastAPI endpoint `POST /extract/file-text`:

```python
from fastapi import UploadFile, File, HTTPException

@app.post("/extract/file-text")
async def extract_file_text(file: UploadFile = File(...)) -> dict:
    """Extract plain text from an uploaded file (best-effort, no OCR).

    Returns: {"text": str, "filename": str, "chars": int}
    Empty or minimal extraction is not an error — caller shows paste-fallback Alert.
    """
    content = await file.read()
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    text = _extract_text(content, suffix)  # dispatcher → pypdf/docx/openpyxl/pptx
    return {"text": text, "filename": file.filename, "chars": len(text)}
```

**Empty-extraction threshold (Claude's Discretion):** recommend 200 chars — if extracted text is fewer than 200 chars, the client shows the weak-extraction Alert (D-05) regardless of error status.

### Pattern 4: Raw-text → VendorResponse wrapper (D-06)

New endpoint `POST /input/raw-text`:

```python
class RawTextInput(BaseModel):
    vendor_name: str = pydantic_Field(max_length=200)
    raw_text: str = pydantic_Field(max_length=200_000)

@app.post("/input/raw-text")
async def wrap_raw_text(req: RawTextInput) -> dict:
    """Wrap buyer-supplied raw text into a minimal VendorResponse for extraction."""
    vendor = VendorResponse(
        vendor_name=req.vendor_name,
        persona="buyer-upload",
        mess_spec=[],
        source_id=f"upload-{req.vendor_name[:20]}",
        format_label="text",
        raw_text=req.raw_text,
    )
    return vendor.model_dump(mode="json")
```

Alternatively, a single new endpoint accepts raw text + vendor name and immediately streams the extraction (combining wrap + extract). **Planner's call** — both approaches are valid; the two-step is slightly cleaner for the client (allows the Input screen to show the VendorResponse before triggering extraction).

### Pattern 5: CORS config for FastAPI (SHIP-01)

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://*.vercel.app",
    "http://localhost:3000",
    # Add exact Vercel production URL once known
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

[ASSUMED — standard FastAPI CORS pattern; verified `fastapi.middleware.cors` exists in FastAPI]

**Render proxy buffering:** Set the environment variable `X_ACCEL_BUFFERING=no` on the Render service (Render docs recommend this for SSE). [ASSUMED — Render environment variable approach; verify in Render dashboard]

### Anti-Patterns to Avoid

- **Buffering SSE before rendering:** Never collect all SSE events then display. Render each `status` event incrementally as it arrives — the live progress is the demo value.
- **EventSource for POST endpoints:** The existing endpoints are `POST`; native `EventSource` only handles `GET`. Use `fetch + ReadableStream` as specified in D-23.
- **Touching `ExtractionResult`/`ComparisonResult` schemas:** Phase 4 schemas are frozen. This phase renders the output — no schema changes, no codegen reruns needed.
- **Re-running extraction on tab revisit:** Session cache (D-02) must prevent re-runs. Check cache before any fetch.
- **Axios/other HTTP clients for SSE:** Axios buffers by default and does not support streaming body readers. Use native `fetch`.
- **`npx shadcn@latest add` with third-party registry blocks:** The `components.json` declares no third-party registries; only the official shadcn registry is in scope.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom PDF parser | `pypdf` | PDF internals (compression, cross-refs, fonts) have infinite edge cases |
| DOCX text extraction | XML unzipping + namespace handling | `python-docx` | DOCX XML schema has ~40 element types; `python-docx` normalizes them |
| XLSX cell reading | CSV hack or raw OpenXML | `openpyxl` | Sheet indexing, merged cells, formula cells all break naive reads |
| PPTX slide text | ZIP + XML walk | `python-pptx` | Multiple text frame types (title, content, notes, table cells) |
| SSE `data:` parsing | Regex or split("data:") | The `buf += decode; split("\n\n")` pattern shown above | SSE chunks can straddle read() calls; naive split drops events |
| CSS design tokens | Hand-coded oklch values | `globals.css` CSS variables (already defined) | Token naming prevents drift; the full palette is already in `globals.css` |
| `cn()` class composition | String concatenation | `lib/utils.ts` `cn` (already exists) | Handles conditional classes and Tailwind conflicts; already written |

**Key insight:** The file parsing work is entirely backend Python — the browser has no reliable way to extract text from binary office formats without WASM libraries that would bloat the client bundle unnecessarily.

---

## What Already Exists (Reuse Inventory)

| Asset | Path | Phase 5 use |
|-------|------|-------------|
| shadcn substrate | `apps/web/components.json`, `lib/utils.ts`, `components/ui/button.tsx` | Add 12 more components; reuse `cn` everywhere |
| Tailwind v4 tokens | `apps/web/app/globals.css` | All color/spacing tokens already defined; just use the semantic names |
| Shared types | `packages/shared-types/index.d.ts` | `ExtractionResult`, `ComparisonResult`, `FlagStatus`, `ComparabilityVerdict` — all ready |
| SSE endpoints | `services/ai/api/app.py` | `/extract/vendor`, `/compare/vendors` — working, frozen |
| Sample data | `data/rfq.json`, `data/vendor_{thorough,cheap,fluff}.json` | RFQ default render (D-21) + sample-load hero (D-04) |
| Trace files | `docs/traces/*.json` (7 files) | Trace screen (D-15) — extraction traces have `grounding_step.downgrade_report`; comparison traces have `clamp_step.entries` |
| Prompt registry | `services/ai/prompts/registry.py` + 7 `.md` files | Prompt Pack list on Trace screen (D-15) — read frontmatter: `id`, `version`, `intent`, `failure_handling` |
| Extraction prompt doc | `docs/prompts/extraction-prompt-doc.md` | Already written — PROMPT-02 partially done for extraction; do the remaining 6 |
| Data-gen prompt doc | `docs/prompts/data-generation.md` | Already written — PROMPT-02 partially done |
| FastAPI app | `services/ai/api/app.py` | Add CORS middleware + 2 new endpoints |
| Playwright | `/opt/homebrew/bin/playwright` (v1.58.0) | Available globally; add `@playwright/test` to root devDeps for E2E script |
| `next.config.mjs` | `apps/web/next.config.mjs` | Already has `transpilePackages: ["@aerchain/shared-types"]` — no change needed |

---

## Trace Screen Data Contract

The 7 committed trace files in `docs/traces/` have a consistent structure the Trace screen reads:

**Extraction traces** (`trace_vendor_*.json`, `trace_adversarial_fixture.json`):
```
{ input: { vendor_name, source_id, rfq_line_items, raw_text_preview },
  resolved_prompt: { id, version, system_message, human_message_template },
  raw_model_output: { ... ExtractionResult fields ... },
  grounding_step: { downgrade_report: { entries: [...] }, fields_downgraded: int },
  final_result: { ... ExtractionResult fields after grounding ... } }
```

**Comparison traces** (`comparison_trace_*.json`):
```
{ _fixture_mode: bool,
  input: { vendor_names, rfq_title, extraction_summaries },
  resolved_prompt: { id, version, system_message_excerpt },
  raw_model_output: { dimensions, narrative_summary },
  clamp_step: { entries: [ { vendor_name, dimension, model_proposed, code_ceiling, clamped_to, ceiling_reason } ] },
  clarification_step: { flagged_fields_input, note },
  final_result: { ... ComparisonResult fields ... } }
```

**The "code disproves model" diff** lives in `grounding_step.downgrade_report.entries` (extraction) and `clamp_step.entries` (comparison). These are the highlighted amber cells in the Trace screen (D-15).

**How to serve these files to the client:** Since Next.js App Router allows `fetch()` to local files in `public/` or importing JSON via `import`, the simplest approach is:
1. Copy (or symlink) `docs/traces/*.json` into `apps/web/public/traces/` at build time, OR
2. Create a Next.js Route Handler (`GET /api/traces/[name]`) that reads from the filesystem. Route handler approach avoids duplicating files. **Planner's call** — Route Handler is lazier (no copy step).

---

## Common Pitfalls

### Pitfall 1: SSE chunks straddle `reader.read()` calls
**What goes wrong:** A `data: {...}\n\n` event may be split across two `reader.read()` calls. If you parse each chunk independently, you get partial JSON that throws.
**Why it happens:** TCP/HTTP chunking is independent of SSE line boundaries.
**How to avoid:** Buffer across reads (`buf += decoder.decode(value, { stream: true })`), split on `"\n\n"`, only parse complete parts. The pattern in Code Examples above handles this correctly.
**Warning signs:** Intermittent JSON parse errors in the SSE consumer.

### Pitfall 2: FastAPI `UploadFile` requires `python-multipart`
**What goes wrong:** Using `UploadFile = File(...)` in a FastAPI route without `python-multipart` installed raises a runtime error on the first request — not at startup.
**Why it happens:** FastAPI doesn't import `multipart` until a request with that body type arrives.
**How to avoid:** Add `python-multipart` to `pyproject.toml` and `uv sync` before testing the file upload endpoint.

### Pitfall 3: Render cold start kills the SSE demo
**What goes wrong:** Render free-tier instances sleep after 15 min of inactivity. A cold start during the demo recording causes a 10-30 second delay at the most visible moment (first SSE event).
**Why it happens:** Render spins down idle instances.
**How to avoid:** D-18 — warm the instance by hitting `GET /data/rfq` before recording. Alternatively use the paid Render tier (no sleep) or Railway (similar approach).

### Pitfall 4: Next.js `import` of JSON from `docs/traces/` at build time
**What goes wrong:** `import traceData from "../../../../docs/traces/comparison_trace_1.json"` works locally but breaks on Vercel because the `docs/` directory is outside the `apps/web/` package boundary.
**Why it happens:** Vercel builds only the app package directory; sibling directories are not copied to the build context by default.
**How to avoid:** Serve traces via Next.js Route Handler in `apps/web/app/api/traces/[name]/route.ts` (reads from filesystem using `path.resolve(process.cwd(), "../../docs/traces/", name)`) — works locally; on Vercel, `process.cwd()` is the project root if the app is not isolated. Alternatively, explicitly include `docs/traces/` in the Vercel build via `vercel.json` `includeFiles`. **Verify this during Wave 0.**

### Pitfall 5: CORS wildcard vs exact origin for SSE
**What goes wrong:** Using `allow_origins=["*"]` breaks SSE in browsers that require explicit CORS headers on streaming responses.
**Why it happens:** Browser SSE via `fetch` checks CORS; wildcard `*` is blocked when credentials are involved (even if credentials aren't sent, some browsers are stricter).
**How to avoid:** List the exact Vercel production URL + localhost in `ALLOWED_ORIGINS`. The exact Vercel URL is known only after first deploy; use `*.vercel.app` as a placeholder for preview deployments.

### Pitfall 6: `sessionStorage` is per-tab, not per-browser
**What goes wrong:** If the demo opens a second tab, state is not shared.
**Why it happens:** `sessionStorage` is intentionally tab-isolated.
**How to avoid:** For this single-buyer prototype, tab isolation is the correct behavior. Document in UAT script that the demo must use one tab.

### Pitfall 7: shadcn `npx shadcn@latest add` version pin
**What goes wrong:** `npx shadcn add` (without `@latest`) may use a cached older version that generates code incompatible with Tailwind v4.
**Why it happens:** npm caches the last resolved version of unversioned `npx` invocations.
**How to avoid:** Always run `npx shadcn@latest add <name>` (with `@latest`) from `apps/web/`.

---

## Deployment Details (SHIP-01)

### Vercel (apps/web)
- Deploy from monorepo root; set **Root Directory** to `apps/web` in Vercel dashboard.
- Environment variable: `NEXT_PUBLIC_AI_BASE_URL=https://<render-service>.onrender.com`
- No special headers needed for the client — SSE is initiated by the browser directly.
- `next.config.mjs` needs no changes for deployment (already has `transpilePackages`).
- Build command: `pnpm build` (or `next build`) from `apps/web/`.

### Render (services/ai)
- Service type: **Web Service** (not a static site) — long-running Python process.
- Build command: `uv sync --frozen` (or `pip install -e .`).
- Start command: `uvicorn api.app:app --host 0.0.0.0 --port $PORT`.
- Environment variables: `OPENAI_API_KEY`, `MODEL_REASONING=gpt-5.4`, `MODEL_CHEAP=gpt-5.4-mini`.
- **Proxy buffering:** Set `X_ACCEL_BUFFERING=no` as an environment variable — Render uses nginx internally and respects this header to pass SSE through without buffering. [ASSUMED — verify in Render docs at deploy time]
- CORS: add the exact Vercel production URL to `ALLOWED_ORIGINS` after first Vercel deploy.

### Deploy sequence
1. Deploy AI service to Render → get the service URL.
2. Set `NEXT_PUBLIC_AI_BASE_URL` in Vercel project settings.
3. Deploy `apps/web` to Vercel.
4. Add Vercel URL to Render CORS `ALLOWED_ORIGINS` env var.
5. Warm Render instance before demo recording.

---

## Submission Package Gap Analysis

| Deliverable | Path | Status |
|------------|------|--------|
| README | `README.md` (repo root) | MISSING — needs authoring |
| Write-up (1–2 page) | `docs/write-up.md` | MISSING — needs authoring |
| Demo script/storyboard | `docs/demo/` | Dir exists; content MISSING |
| Architecture diagram | `docs/architecture/` | Dir does NOT exist — needs creation |
| Prompt docs (PROMPT-02) | `docs/prompts/` | PARTIAL — extraction + data-gen docs exist; 5 prompts (rfq-gen, vendor-gen, messy-data-gen, ui-ux-gen, comparison, clarification) need docs |
| Prompt failure example (PROMPT-04) | `docs/prompts/` | MISSING — needs one failure + fix + versioning notes |
| ui-ux-gen prompt (full) | `services/ai/prompts/ui-ux-gen.v1.md` | STUB — `TODO P5 / UI-01` — needs authoring + one live run |
| UAT script | `docs/qa/` | Dir exists with Phase 2/4 scripts; Phase 5 Playwright script MISSING |
| Committed traces | `docs/traces/*.json` | COMPLETE (7 traces) |
| Sample data | `data/rfq.json`, `data/vendor_*.json` | COMPLETE |

**PROMPT-02 docs still needed** (5 remaining prompts):
- `rfq-gen` — what/why/failure handling
- `vendor-gen` — what/why/failure handling
- `messy-data-gen` — what/why/failure handling
- `ui-ux-gen` — what/why/failure handling (author after running the prompt once)
- `comparison` — what/why/failure handling
- `clarification` — what/why/failure handling

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | apps/web build | ✓ | 26.4.0 | — |
| pnpm | monorepo package mgmt | ✓ | 10.28.1 | — |
| uv | Python dep mgmt | ✓ | installed at `/opt/homebrew/bin/uv` | — |
| Python 3.12 | services/ai | ✓ | 3.12.12 | — |
| uvicorn (in venv) | AI service startup | ✓ | in `.venv/bin/uvicorn` | — |
| Playwright | E2E UAT | ✓ | 1.58.0 (global) | Install `@playwright/test` as devDep |
| pypdf | PDF extraction | ✗ | — | Add to pyproject.toml + uv sync |
| python-docx | DOCX extraction | ✗ | — | Add to pyproject.toml + uv sync |
| openpyxl | XLSX extraction | ✗ | — | Add to pyproject.toml + uv sync |
| python-pptx | PPTX extraction | ✗ | — | Add to pyproject.toml + uv sync |
| python-multipart | FastAPI UploadFile | ✗ | — | Add to pyproject.toml + uv sync |
| shadcn CLI | Component vendoring | ✗ (global) | — | Use `npx shadcn@latest add` |
| Render account | AI service deploy | [ASSUMED] | — | Railway (equivalent, same approach) |
| Vercel account/CLI | Web deploy | [ASSUMED] | — | Manual dashboard deploy |

**Missing dependencies blocking local dev:** pypdf, python-docx, openpyxl, python-pptx, python-multipart — all resolved by `uv add` + `uv sync`.

**Missing dependencies blocking deploy:** Render + Vercel accounts (outside scope of codebase — human action).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Python framework | pytest (already configured in `pyproject.toml`) |
| Python quick run | `uv run pytest tests/ -x -q` from `services/ai/` |
| Python full suite | `uv run pytest tests/` from `services/ai/` |
| TS framework | None configured — no vitest/jest in `apps/web` |
| E2E framework | Playwright (global v1.58.0; add `@playwright/test` as devDep) |
| E2E script location | `docs/qa/` per CLAUDE.md §11 |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INPUT-01 | Paste path wraps raw text into VendorResponse | unit | `uv run pytest tests/test_input_wrap.py -x` | ❌ Wave 0 |
| INPUT-02 | File text extraction: PDF/DOCX/XLSX/PPTX returns text string | unit | `uv run pytest tests/test_file_extract.py -x` | ❌ Wave 0 |
| INPUT-03 | Sample load path: vendor JSON file readable and valid | unit | existing `test_sample_fixtures.py` | ✅ |
| INPUT-04 | Dynamic output: extraction called live, not hardcoded | integration/manual | Playwright E2E | ❌ Wave 0 |
| UI-01..06 | Buyer screens render correct content | E2E | `playwright test` | ❌ Wave 0 |
| SHIP-01 | CORS allows Vercel origin; SSE streams through Render | smoke | `curl -N` + manual browser test | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `services/ai/tests/test_file_extract.py` — unit tests for `_extract_text()` dispatcher (PDF/DOCX/XLSX/PPTX)
- [ ] `services/ai/tests/test_input_wrap.py` — unit test for `POST /input/raw-text` endpoint returns valid `VendorResponse`
- [ ] `docs/qa/phase5-e2e.py` or `phase5-playwright.spec.ts` — Playwright E2E covering the full buyer journey per CLAUDE.md §11
- [ ] `@playwright/test` in root `devDependencies` (`pnpm add -D -w @playwright/test`)
- [ ] No TypeScript unit tests warranted (thin client; logic lives server-side per CLAUDE.md §5)

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q` (Python suite; ~15 tests, fast)
- **Per wave merge:** `uv run pytest tests/` + Playwright smoke against local running stack
- **Phase gate:** Full pytest suite green + Playwright E2E pass before `/gsd:verify-work`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Single-buyer prototype, no auth |
| V3 Session Management | yes (lite) | `sessionStorage` tab-scoped; no server session |
| V4 Access Control | no | No auth, no RBAC |
| V5 Input Validation | yes | Pydantic models on all backend endpoints; `max_length` on raw_text; filename validation on upload |
| V6 Cryptography | no | No key material in browser; `OPENAI_API_KEY` server-only (D-24) |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized file upload | DoS | `python-multipart` file size limit; FastAPI `UploadFile` max size param |
| Path traversal via filename | Tampering | Discard filename in `_extract_text()`; use only file extension and bytes |
| CORS misconfiguration exposes OpenAI key | Info Disclosure | Key is server-only; browser only knows `NEXT_PUBLIC_AI_BASE_URL` (D-24); CORS gates the origin |
| Raw-text input with huge payload | DoS | `max_length=200_000` on `RawTextInput.raw_text` — same cap as `ExtractionRequest` |
| LLM fabricated facts rendered as fact | Spoofing/Tampering | Grounding gate already enforced server-side on Phase 3; UI renders the grounded `ExtractionResult` as-is |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Render respects `X_ACCEL_BUFFERING=no` env var to disable SSE buffering | Deployment | SSE arrives as one big chunk after stream closes; demo fails to show incremental progress |
| A2 | `*.vercel.app` wildcard works in FastAPI `allow_origins` for preview deploys | CORS Config | Preview deployments can't reach AI service; add exact URLs instead |
| A3 | All five PyPI packages (pypdf, python-docx, openpyxl, python-pptx, python-multipart) are legitimate and safe | Package Legitimacy | slopcheck not run; packages are well-known (>10yr age, major repos) but not formally verified this session |
| A4 | Serving `docs/traces/*.json` via a Next.js Route Handler works on Vercel (filesystem accessible at runtime) | Trace Screen | May need to copy traces to `apps/web/public/traces/` instead |
| A5 | pnpm workspace resolves `@aerchain/shared-types` correctly after adding new shadcn components (no codegen needed) | Package setup | Codegen is only needed if pydantic schemas change — they are frozen this phase |

---

## Open Questions (RESOLVED)

1. **Trace file serving on Vercel** — **RESOLVED:** Copy `docs/traces/*.json` → `apps/web/public/traces/` (build/setup step) and serve via a Route Handler `GET /api/traces/[name]` that reads from `public/traces/`. Avoids the `process.cwd()` monorepo-root ambiguity entirely. Implemented in plan 05-04 Task 1 Step 0.
   - Original concern: Whether `process.cwd()` in a Route Handler on Vercel resolves to monorepo root or to `apps/web/`. Sidestepped by serving from `public/`.

2. **ui-ux-gen prompt run output format** — **RESOLVED:** Request Markdown with structured headings per screen — easier to include verbatim in `docs/` as the UI/UX artifact, and still demonstrably prompt-driven. Implemented in plan 05-05 Task 1.

3. **PROMPT-04 example selection** — **RESOLVED:** Use `extraction.v1.md` humility-bias failure (model confidently marked `present` on weak evidence, then got downgraded by the grounding gate) — maps directly to the rubric's reliability concern. Implemented in plan 05-05 Task 2.

---

## Sources

### Primary (HIGH confidence)
- `services/ai/api/app.py` — existing endpoints, request models, SSE pattern confirmed
- `services/ai/schemas/domain.py` — ExtractionResult, ComparisonResult shapes confirmed
- `services/ai/schemas/events.py` — EventEnvelope, EVENT_TYPES confirmed
- `apps/web/package.json` — exact dependency versions confirmed
- `apps/web/components.json` — shadcn style=new-york, CSS variables, lucide icons confirmed
- `apps/web/app/globals.css` — full token set confirmed
- `docs/traces/comparison_trace_1.json`, `docs/traces/trace_vendor_thorough.json` — trace schemas confirmed via inspection
- `packages/shared-types/index.d.ts` — TypeScript types for all domain models confirmed
- [VERIFIED: Next.js docs v16 — `fetch + ReadableStream` pattern for SSE]
- [VERIFIED: PyPI — pypdf 6.14.2, python-docx 1.2.0, openpyxl 3.1.5, python-pptx 1.0.2, python-multipart 0.0.32]
- [VERIFIED: npm — @radix-ui/react-tabs 1.1.15, @radix-ui/react-collapsible 1.1.14, etc. — all in official shadcn registry]

### Secondary (MEDIUM confidence)
- Render SSE buffering via `X_ACCEL_BUFFERING=no` — standard pattern for nginx-proxied SSE services [ASSUMED; verify in Render docs]
- FastAPI CORSMiddleware with `allow_origins` list — well-established FastAPI pattern [ASSUMED as standard]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified via package.json, PyPI, or npm registry
- Architecture: HIGH — grounded in actual code (`app.py`, `domain.py`, trace files)
- File parsing libs: MEDIUM — PyPI existence verified; slopcheck not run (not installed)
- Deployment: MEDIUM — Render SSE config and Vercel monorepo deploy are [ASSUMED] patterns
- Pitfalls: HIGH — grounded in the actual codebase (SSE chunk boundary, multipart dependency, Render cold start)

**Research date:** 2026-06-28
**Valid until:** 2026-07-12 (stable Next.js/shadcn stack; deployment platform configs may change faster)
