# Phase 5: Buyer UI, Trace & Submission - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning

<domain>
## Phase Boundary

A **thin, buyer-first Next.js UI** (App Router, Tailwind v4 + shadcn/ui, deployed to Vercel) renders
the **live AI behavior** already built in Phases 1–4 across the five buyer screens, makes the prompt
trace visible in-app, and ships the full submission package. The UI is a well-designed *client*: it
holds no business logic and no AI SDKs — it consumes the existing FastAPI/SSE service over HTTP.

**In scope (INPUT-01..04, UI-01..06, PROMPT-02, PROMPT-04, SHIP-01..05):**
- The five screens: RFQ Overview, Vendor Upload/Input, Extraction Review, Vendor Comparison,
  Prompt Trace / Prompt Pack.
- Vendor input: one-click sample load, paste (text/MD/JSON), and best-effort file upload
  (PDF/DOCX/XLSX/PPTX) — including a **new backend text-extraction path** the API does not yet have.
- Client SSE consumption of the existing POST `/extract/vendor` and `/compare/vendors` endpoints.
- Authoring `ui-ux-gen.v1.md` in full + running it once to capture a UI/UX spec artifact (the 10%
  UI/UX-generation deliverable).
- Prompt Pack documentation: per-prompt what/why/how-it-handles-unreliable-info (PROMPT-02) **and**
  the still-pending PROMPT-04 (≥1 documented failure example + fix + versioning notes).
- Deploy: web → Vercel, AI service → Render; CORS + disabled proxy buffering so SSE streams live.
- Submission: README, 1–2 page write-up, ≤5-min demo video, system + AI-pipeline architecture diagram.

**Out of scope (locked / excluded):**
- Any change to extraction/comparison/grounding **agent behavior or schemas** — Phases 1–4 are done;
  this phase renders their output, it does not re-open the AI contract. (A *minimal* new
  raw-text→VendorResponse wrapper + a new file-text-extraction endpoint are the only backend
  additions, both input-plumbing, not agent logic.)
- Database / queue / vector store, auth / multi-user, production OCR, heavy normalization, GPT-5.5 —
  permanently out of scope (PROJECT.md Out of Scope; §24).
- Numeric leaderboard / weighted scoring / should-cost — excluded by design (Phase 4 D-07).

</domain>

<decisions>
## Implementation Decisions

### A. App shell, buyer journey & demo path
- **D-01:** **Guided stage rail.** A persistent left-rail navigation showing the procurement stages
  (RFQ → Input → Extraction → Comparison → Trace) — free to click but ordered. Mirrors the real
  buyer journey and gives the ≤5-min demo a clean narrative spine (UI-06).
- **D-02:** **Live, session-cached results.** Extraction and comparison run the **real OpenAI
  pipeline on demand** (honors INPUT-04 — never hardcoded), and the result is cached in the client
  session so re-visiting a screen is instant. No always-live re-runs (too slow/fragile on a live
  demo); no "load committed result" affordance (reads as hardcoded — §24).
- **D-03:** **Substance-first + hero polish.** Clean shadcn baseline everywhere; concentrate visual
  polish on the AI-showcase surfaces — **evidence snippets, flag states, comparability matrix** —
  where polish *demonstrates AI behavior* rather than decorates. Guards the §24 "polish without
  strong AI behavior" anti-pattern while still landing the 10%.

### B. Vendor input strategy (INPUT-01..04)
- **D-04:** **One-click sample load is the hero path.** The 3 committed messy vendors load instantly;
  paste and upload are secondary. Most reliable demo and the committed messy samples are the
  strongest AI story.
- **D-05:** **All four upload formats, best-effort, with paste fallback.** A single backend
  text-extraction layer handles PDF/DOCX/XLSX/PPTX via libraries (best-effort, no production OCR per
  §11); when extraction is weak/empty the UI gracefully prompts "extraction weak — paste instead."
  (Library selection per format = researcher/planner detail.)
- **D-06:** **Minimal raw-text wrap; buyer names the vendor.** Pasted/extracted raw text becomes
  `VendorResponse.raw_text` with a buyer-supplied vendor name (or the filename); the **extraction
  agent does all structuring**. No manual structured-field entry, and the vendor name is buyer-given
  (not an ungrounded model guess). Needs a thin path/endpoint to wrap raw text into the minimal
  `VendorResponse` the existing `/extract/vendor` consumes.

### C. Extraction Review screen (UI-03, UI-06)
- **D-07:** **Inline evidence + source on drill-down.** A short evidence snippet shows **inline under
  each fact** (always visible — evidence-first); clicking opens the source passage with the cited
  span highlighted in context.
- **D-08:** **Top gaps & risks panel + inline badges.** A summary panel at the top lists **every
  flagged field first** (missing/unclear/conflicting/unsupported — buyer-first UI-06), with
  color-coded badges inline on each field. Absence is unmissable, never hidden to tidy the UI (§8).
- **D-09:** **By-category layout under the gaps panel.** Fields grouped by schema category (scope,
  pricing, commercial terms, timeline, compliance, assumptions, exclusions, risks) — mirrors
  `ExtractionResult`, buyer-first.
- **D-10:** **One vendor at a time.** Per-vendor view with a vendor selector/tabs; side-by-side
  comparison lives on the Comparison screen (extraction is inherently per-vendor).

### D. Vendor Comparison screen (UI-04, UI-06) — renders Phase 4's locked `ComparisonResult`
- **D-11:** **Matrix-first.** The comparability matrix (vendors × 6 dimensions, color badges +
  one-line reason) is the hero at top; the 8-line-item × vendor offer table and per-dimension
  narrative live on drill-down. Matches Phase 4 D-01 + UI-06.
- **D-12:** **Always-visible clarifications/attention panel.** A dedicated panel surfaces buyer
  attention points + generated clarification questions **first**, each linking back to the
  dimension/line-item gap it came from (the product's primary output, surfaced — not tucked in a tab).
- **D-13:** **Stable order + explicit no-rank framing.** Vendors render in **stable input order
  (never sorted)**; the readiness X/N count (Phase 4 D-07) is labelled a *data-readiness* indicator
  with a "not a ranking/score" affordance. Honors the D-07 guardrail visually — ordering by readiness
  would be the leaderboard §24 forbids.
- **D-14:** **Clamp note here, full diff in Trace.** A subtle "comparability determined in code from
  evidence" note appears on the Comparison screen; the raw-model-verdict → code-clamped-verdict diff
  (the "code disproves the model" story) lives in full on the Trace screen, keeping Comparison
  buyer-clean.

### E. Prompt Trace screen, UI/UX-gen prompt & prompt docs (UI-05, PROMPT-02, PROMPT-04)
- **D-15:** **Full trace + Prompt Pack list in-app.** The Trace screen renders **≥1 complete
  pipeline trace** from committed trace JSON (input → resolved prompt id+version → raw model output →
  grounded/clamped final, **downgrade diff highlighted**) **plus** a browsable list of all 7 prompts.
  Renders existing `docs/traces/*.json` — no new trace capture required (extraction + comparison
  traces already committed).
- **D-16:** **Author + run ui-ux-gen once, build the React by hand.** Flesh `ui-ux-gen.v1.md` to a
  full prompt, **run it once** to produce a captured UI/UX spec artifact (JSON/MD) that genuinely
  informs the build; implement the actual shadcn/React by hand. Prompt + captured artifact = the
  10% deliverable. Honest (a prompt can't reliably emit our component tree) and not over-engineered.
- **D-17:** **Prompt docs in `docs/prompts/`, fold PROMPT-04 here.** One what/why/how-it-handles-
  unreliable-info doc per prompt in `docs/prompts/` (frontmatter already carries `intent` /
  `failure_handling`; the docs hold the fuller writeup). Include the PROMPT-04 deliverable — ≥1
  documented prompt failure + its fix + versioning/evaluation notes (§21 differentiator) — in this
  same pass. Closes PROMPT-02 and the long-pending PROMPT-04 together.

### F. Deploy & submission package (SHIP-01..05)
- **D-18:** **Render, warmed before the demo.** AI service → **Render** (simple long-running Python
  web service, SSE-friendly), with **proxy buffering disabled**; warm the instance right before
  recording so cold-start latency never stalls the live SSE stream. (Railway is an equivalent
  fallback if Render limits bite — same approach.)
- **D-19:** **Rubric-driven messy-case demo arc.** The ≤5-min demo storyline: load a messy vendor →
  extraction surfacing gaps **with evidence** → comparison flagging **non-comparable + clarifications**
  → trace showing **code-disproves-model**. The storyline *is* the rubric (reliability + product
  thinking), not a flat screen tour.
- **D-20:** **Mermaid + Markdown for all docs.** System + AI-pipeline diagrams as **Mermaid** in
  `docs/architecture/` (renders on GitHub, no tooling, never drifts from an exported image); README
  and write-up authored as Markdown to the rubric structure. Lazy + sufficient.

### G. RFQ Overview screen & data sourcing (UI-01)
- **D-21:** **Committed RFQ by default + regen button.** Render the committed `data/rfq.json`
  instantly on load; a "regenerate" button calls `GET /data/rfq` to prove dynamic generation
  (DATA-04). Fast first screen + a live dynamic-proof on demand (avoids a cold-start on the demo's
  opening screen).
- **D-22:** **Full, grouped render with a summary on top.** Buyer-first summary at the top, then the
  full structured RFQ: scope, timelines, all 8 line items, commercial expectations, vendor
  questionnaire, compliance. UI-01's job is to make clear *what vendors must respond to*.

### H. Client streaming, env wiring & failure states
- **D-23:** **fetch + ReadableStream for POST-SSE.** The client consumes the SSE endpoints via
  `fetch` with a streaming body reader parsing `data:` lines — the endpoints stay **POST** (they
  carry full `VendorResponse`/`RFQ`/`ExtractionResult[]` bodies; native `EventSource` is GET-only).
- **D-24:** **Base URL public, OpenAI key server-only.** The browser knows only
  `NEXT_PUBLIC_AI_BASE_URL` and calls the AI service directly; the **OpenAI key stays server-side**
  in the AI service, never shipped to the browser; CORS allowlists the Vercel domain + localhost.
  No Next.js proxy layer (extra moving parts + an SSE proxy-buffering risk).
- **D-25:** **Stream progress + explicit errors.** Surface the agent's status events as live progress
  (e.g. align → extract → ground → done); on truncation / refusal / API failure show an **explicit
  error state** — never a blank screen or a fabricated result. Absence-first (§8) applies to failures
  too: the UI must never paper over a failed run.
- **D-26:** **Fully responsive UI.** *(User chose this over the desktop-first recommendation.)* Build
  responsive layouts (mobile/tablet + desktop), not desktop-only. Note for the planner: keep the
  responsive work proportionate to the 10% weight — reflow, don't redesign — so it doesn't tip into
  the §24 "polish without strong AI behavior" anti-pattern. The AI-showcase surfaces (evidence,
  flags, matrix) must stay legible at narrow widths.

### Claude's Discretion (within the decisions above)
- Exact component breakdown, shadcn primitives used, file/route structure under `apps/web/app/(buyer)/`.
- Text-extraction libraries per upload format (D-05) and the empty-extraction threshold for the
  paste-fallback.
- Client SSE parser implementation, session-cache mechanism (D-02), and loading/skeleton treatment.
- Mermaid diagram contents/granularity; README + write-up section ordering (within the rubric).
- How many prompts get a standalone `docs/prompts/` file vs a shared doc, and which prompt's failure
  becomes the PROMPT-04 example (pick the most instructive one).
- Whether the new raw-text input path is a new endpoint or a thin wrapper before `/extract/vendor`
  (D-06) — researcher/planner call.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of truth (brief & rubric)
- `docs/assignment.md` — §22 rubric (UI/UX prompt quality & buyer usability 10%, Demo & docs 5%,
  Prompt quality 30%), §24 anti-patterns (**UI polish without strong AI behavior**, hardcoded
  outputs, static dashboards, ignoring missing/contradictory info, misleading comparisons), §11
  (best-effort text extraction, no production OCR), §21 differentiators (architecture diagram,
  prompt failure example + versioning).

### Product vision & reliability rules
- `CLAUDE.md` §1 — product principles (evidence over assertion, absence first-class,
  comparability before ranking, **buyer-first information hierarchy**, the Prompt Pack is the product).
- `CLAUDE.md` §5 — architecture: `apps/web` is a thin Next.js client (no AI SDKs, no business logic);
  Tailwind v4 + shadcn/ui (own-the-source, not a runtime kit); SSE consume; deploy split.
- `CLAUDE.md` §6 — the five buyer screens (the spec for UI-01..05).
- `CLAUDE.md` §7 — Prompt Pack & traceability (per-prompt what/why/failure-handling; ≥1 trace).
- `CLAUDE.md` §8 — absence states surfaced, never silently filled (drives D-08, D-25).
- `CLAUDE.md` §11 — testing: Playwright end-to-end buyer-flow pass is the handoff gate; capture the
  UAT script under `docs/qa/`.
- `CLAUDE.md` §12 — deploy (Vercel = Next.js only; Render/Railway for the Python service).
- `CLAUDE.md` §14 — `docs/` folder structure (the submission package maps onto it).

### Planning inputs
- `.planning/PROJECT.md` — product framing, Key Decisions (data strategy = commit samples + live
  regen + in-app upload; deploy to Vercel + Render/Railway; paste + PDF/Word/Excel/PPT best-effort),
  Out of Scope.
- `.planning/REQUIREMENTS.md` — INPUT-01..04, UI-01..06, PROMPT-02, PROMPT-04, SHIP-01..05 are this
  phase's mandated reqs; rubric weights per category.
- `.planning/ROADMAP.md` §"Phase 5" — the 5 success criteria this phase must make TRUE (dynamic
  input + one-click sample; five legible buyer-first screens; visible evidence + flagged
  non-comparability; deployed SSE-live stack; complete submission package).
- `.planning/STATE.md` — carried-forward gates now due:
  - **Prompt-quality peer review** — applies to `ui-ux-gen.v1.md` + the PROMPT-02 docs (30%).
  - **Trace/demo readability** — applies to the in-app trace render (D-15) + the demo video (D-19).
- `.planning/phases/04-comparison-agent/04-CONTEXT.md` — the `ComparisonResult` shape the Comparison
  screen renders (D-01 matrix, D-06 line-item table, D-07 readiness X/N never-sorted, D-08 attention
  points, D-09..10 clarifications, D-11 verdict-clamp trace).
- `.planning/phases/03-extraction-agent/03-CONTEXT.md` — the `ExtractionResult` shape the Extraction
  Review screen renders (per-line-item, evidence per fact, four flag types, SSE event stream).

### Existing code the phase builds on / extends
- `apps/web/` — greenfield client: `app/layout.tsx`, `app/page.tsx`, `app/globals.css` (Tailwind v4
  CSS-first), `components/ui/button.tsx` (sole shadcn component), `lib/utils.ts` (`cn`),
  `components.json` (shadcn config). Buyer screens go under `app/(buyer)/` (CLAUDE.md §5).
- `services/ai/api/app.py` — existing endpoints: `GET /data/rfq` (live RFQ regen), `POST
  /data/vendor-gen` (persona vendor regen), `POST /extract/vendor` (SSE, takes `VendorResponse` +
  `RFQ`), `POST /compare/vendors` (SSE, takes `ExtractionResult[]`), `GET /stream/demo`. **No CORS,
  no file-upload/text-extract endpoint, no raw-paste path yet** — all added here. `ExtractionRequest`
  / `VendorGenRequest` / `ComparisonRequest` request models live here.
- `services/ai/schemas/domain.py` — `RFQ`, `VendorResponse` (has `raw_text` — the D-06 wrap target),
  `ExtractionResult`, `ComparisonResult` (all rendered by screens). **Read-only — do not change.**
- `services/ai/schemas/events.py` — `EventEnvelope {type, payload}`, closed `EVENT_TYPES`,
  `ErrorPayload` — the SSE contract the D-23 client parser consumes (D-25 error/progress states).
- `services/ai/prompts/ui-ux-gen.v1.md` — the reserved stub to author in full (D-16);
  `services/ai/prompts/registry.py` — `load(id)` for the in-app Prompt Pack list (D-15).
- `docs/traces/*.json` + `*.md` — committed extraction (`trace_vendor_*`) and comparison
  (`comparison_trace_*`) traces the in-app Trace screen renders (D-15) — no new capture needed.
- `data/rfq.json`, `data/vendor_{thorough,cheap,fluff}.json` — committed samples for the RFQ default
  render (D-21) and the one-click sample-load hero path (D-04).
- `packages/shared-types/` — generated TS mirror of the pydantic schemas; the client imports these
  types (the contract). Any backend schema touch (avoided here) would require codegen (PLAT-02).

### Submission targets (`docs/` — CLAUDE.md §14)
- `docs/prompts/` — PROMPT-02 per-prompt docs + PROMPT-04 failure example (D-17).
- `docs/architecture/` — Mermaid system + AI-pipeline diagrams (D-20, SHIP-05).
- `docs/write-up.md` — the 1–2 page write-up (SHIP-03); `docs/demo/` — demo script/storyboard (D-19);
  `docs/qa/` — the Playwright UAT script (CLAUDE.md §11); README at repo root (SHIP-02).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- shadcn/ui substrate already initialized: `components.json`, `lib/utils.ts` (`cn`), `button.tsx`,
  Tailwind v4 CSS-first in `globals.css` — add components via the shadcn CLI, theme via tokens.
- The full SSE spine exists server-side (`/extract/vendor`, `/compare/vendors`) — the client only
  needs a `fetch`+ReadableStream consumer (D-23), no new streaming infra.
- `data/*.json` samples + `docs/traces/*.json` are ready-made content for the sample-load hero (D-04),
  RFQ default (D-21), and in-app Trace screen (D-15) — no generation work to render them.
- `EventEnvelope`/`EVENT_TYPES`/`ErrorPayload` define exactly the event shapes the client parses
  (D-25); `shared-types` already mirrors all rendered schemas to TS.

### Established Patterns
- `apps/web` is a **thin client**: no AI SDKs, no business logic; all AI stays in `services/ai`.
- pydantic schemas are the contract source → `shared-types` (PLAT-02). This phase **avoids** schema
  changes; the only backend additions are input plumbing (file-text extraction + raw-text wrap) and
  deploy config (CORS, proxy buffering) — neither touches agent schemas.
- Code-enforced reliability (grounding gate, comparability clamp) already runs server-side; the UI
  only **renders** grounded/clamped output — it never re-decides comparability or grounding.

### Integration Points
- The client → `NEXT_PUBLIC_AI_BASE_URL` → FastAPI (CORS-allowlisted) → existing agents (D-24).
- New backend file-text-extraction endpoint + raw-text wrapper feed the existing `/extract/vendor`.
- Deploy seam: Vercel (web) ↔ Render (AI service) over the env-configured base URL with SSE buffering
  disabled (D-18, SHIP-01).
- Phase 5 is the terminal phase — it renders the output of Phases 1–4 and packages the submission;
  nothing downstream depends on it.

</code_context>

<specifics>
## Specific Ideas

- The demo's **emotional beat is "code disproves the model"** — the Trace screen's highlighted
  downgrade diff (D-15) and the demo arc's closing trace (D-19) are the literal proof of the
  headline reliability claim. Trace readability is a graded quality gate, not just structural validity.
- **Polish follows the AI story** (D-03): the most-designed surfaces are evidence snippets, flag
  badges, and the comparability matrix — the places where good UI *makes the AI behavior legible*.
  Decoration elsewhere is the §24 trap.
- The **one-click sample load** (D-04) is the spine of a reliable demo: instant, deterministic
  inputs, real live pipeline on top (D-02) — fast *and* genuinely dynamic.
- `ui-ux-gen.v1.md` is run for real once (D-16) so the "prompt-driven UI" claim is honest evidence,
  not a stub — but the React is hand-built; the prompt + its captured artifact are the deliverable.

</specifics>

<deferred>
## Deferred Ideas

- **Loadable committed AI result** (instant view from cached JSON) — rejected, not deferred: reads as
  hardcoded output (§24). Live + session-cache (D-02) achieves snappiness honestly.
- **Next.js proxy layer for AI calls** — rejected (D-24): extra moving parts + SSE buffering risk;
  direct client→AI with CORS is simpler and sufficient for a single-buyer prototype.
- **Stateful clarification → re-extraction feedback loop** — v2 (FLOW-01/FLOW-02), out of scope.
- **Production OCR / layout-aware parsing** — v2 (INPUT-05); this phase is best-effort text only (§11).
- **Mobile-redesigned layouts** — D-26 builds responsive reflow, but a bespoke mobile experience
  beyond reflow stays out (proportionality to the 10% weight).

None of the above is lost; each is anchored to its decision or explicitly excluded.

</deferred>

---

*Phase: 5-Buyer UI, Trace & Submission*
*Context gathered: 2026-06-28*
