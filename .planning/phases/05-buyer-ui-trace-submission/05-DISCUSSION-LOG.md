# Phase 5: Buyer UI, Trace & Submission - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-28
**Phase:** 5-Buyer UI, Trace & Submission
**Areas discussed:** A. App shell & demo path, B. Vendor input strategy, C. Extraction Review screen, D. Vendor Comparison screen, E. Prompt Trace screen + UI/UX-gen prompt + prompt docs, F. Deploy & submission package, G. RFQ Overview & data sourcing, H. Client streaming, env wiring & failure states

Mode: `--all` (auto-selected all gray areas; discussed interactively).

---

## A. App shell, buyer journey & demo path

| Option | Description | Selected |
|--------|-------------|----------|
| Guided stage rail | Persistent left-rail stages (RFQ→Input→Extraction→Comparison→Trace), ordered but clickable | ✓ |
| Top-nav, free routes | Plain top nav, no implied sequence | |
| Single scrolling dashboard | All sections on one long page | |

| Option | Description | Selected |
|--------|-------------|----------|
| Live, session-cached | Real pipeline on demand, cached in client session for instant re-view | ✓ |
| Always live, no cache | Re-run every visit | |
| Loadable committed result | Instant view from committed JSON | |

| Option | Description | Selected |
|--------|-------------|----------|
| Substance-first + hero polish | Clean baseline; polish on evidence/flags/matrix | ✓ |
| Minimal throughout | Restrained defaults everywhere | |
| Designed/branded | Custom theme/branding | |

**User's choice:** Guided stage rail · Live, session-cached · Substance-first + hero polish
**Notes:** Polish concentrated where it makes AI behavior legible (§24 guard).

---

## B. Vendor input strategy

| Option | Description | Selected |
|--------|-------------|----------|
| One-click sample load | 3 committed messy vendors load instantly; hero path | ✓ |
| Paste primary | Paste front-and-center | |
| Upload primary | File upload leads | |

| Option | Description | Selected |
|--------|-------------|----------|
| All four, best-effort + fallback | PDF/DOCX/XLSX/PPTX via one extraction layer + paste fallback | ✓ |
| PDF + DOCX only | Two formats well, others rejected | |
| Paste + sample only | No file parsing | |

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal wrap, buyer names vendor | raw text → VendorResponse.raw_text; extraction structures it | ✓ |
| Infer vendor name too | Model guesses the name | |
| Buyer fills key fields | Manual structured entry | |

**User's choice:** One-click sample load · All four best-effort + fallback · Minimal wrap, buyer names vendor
**Notes:** New backend text-extraction path + raw-text wrap needed; extraction agent does all structuring.

---

## C. Extraction Review screen

| Option | Description | Selected |
|--------|-------------|----------|
| Inline + source on drill-down | Snippet inline; source span highlighted on click | ✓ |
| Inline snippet only | No source view | |
| Hover/popover | Evidence hidden until hover | |

| Option | Description | Selected |
|--------|-------------|----------|
| Top gaps panel + inline badges | Summary panel lists flagged fields first + inline badges | ✓ |
| Inline badges only | No summary panel | |
| Summary panel only | No inline badges | |

| Option | Description | Selected |
|--------|-------------|----------|
| By category + gaps on top | Grouped by schema category under gaps panel | ✓ |
| By 8 line items | Organized around line items | |
| Hybrid summary + per-item | Summary + per-item drill-down | |

| Option | Description | Selected |
|--------|-------------|----------|
| One vendor at a time | Per-vendor view with selector/tabs | ✓ |
| All three side-by-side | Parallel columns here too | |

**User's choice:** Inline + source on drill-down · Top gaps panel + inline badges · By category + gaps on top · One vendor at a time

---

## D. Vendor Comparison screen

| Option | Description | Selected |
|--------|-------------|----------|
| Matrix-first | Comparability matrix hero; table + narrative on drill-down | ✓ |
| Line-item table first | Lead with offer table | |
| Per-vendor cards | One card per vendor | |

| Option | Description | Selected |
|--------|-------------|----------|
| Always-visible panel | Attention points + clarifications surfaced first, linked to gaps | ✓ |
| Separate tab | Own tab | |
| Inline per dimension | Attached per cell | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stable order + explicit framing | Never sorted; X/N labelled data-readiness, "not a ranking" | ✓ |
| Drop the count, list blockers | No X/N number | |

| Option | Description | Selected |
|--------|-------------|----------|
| Note here, full diff in Trace | Subtle note; clamp diff lives on Trace screen | ✓ |
| Surface diff inline | Raw-vs-clamped on the matrix | |
| Trace only | No mention here | |

**User's choice:** Matrix-first · Always-visible panel · Stable order + explicit framing · Note here, full diff in Trace

---

## E. Prompt Trace screen + UI/UX-gen prompt + prompt docs

| Option | Description | Selected |
|--------|-------------|----------|
| Full trace + Prompt Pack list | Render ≥1 full trace in-app + browsable 7-prompt list | ✓ |
| Trace only | No Prompt Pack browser | |
| Prompt Pack list only | Trace stays in docs | |

| Option | Description | Selected |
|--------|-------------|----------|
| Author + run once, build by hand | Full prompt + captured artifact; React hand-built | ✓ |
| Generate then implement faithfully | Implement generated structure literally | |
| Author prompt only | No run/artifact | |

| Option | Description | Selected |
|--------|-------------|----------|
| docs/prompts/ + fold PROMPT-04 | Per-prompt docs + failure example/fix/versioning together | ✓ |
| docs/prompts/, defer PROMPT-04 | Docs now, failure example later | |
| Frontmatter only | Inline in prompt frontmatter | |

**User's choice:** Full trace + Prompt Pack list · Author + run once, build by hand · docs/prompts/ + fold PROMPT-04
**Notes:** Renders existing committed traces; no new trace capture needed. Closes pending PROMPT-04 in this phase.

---

## F. Deploy & submission package

| Option | Description | Selected |
|--------|-------------|----------|
| Render, warm before demo | Render + disabled buffering; warm instance pre-recording | ✓ |
| Railway, warm before demo | Same on Railway | |
| Deploy as proof, demo local | Deploy for SHIP-01, record locally | |

| Option | Description | Selected |
|--------|-------------|----------|
| Rubric-driven messy-case arc | Messy vendor → gaps+evidence → non-comparable+clarifications → code-disproves-model | ✓ |
| Linear screen tour | Walk five screens, happy path | |
| Two-vendor contrast | Thorough vs incomplete end-to-end | |

| Option | Description | Selected |
|--------|-------------|----------|
| Mermaid + Markdown | Mermaid diagrams + Markdown write-up/README | ✓ |
| External diagram tool | Figma/Excalidraw/draw.io image | |

**User's choice:** Render, warm before demo · Rubric-driven messy-case arc · Mermaid + Markdown
**Notes:** Railway is an equivalent fallback if Render limits bite.

---

## G. RFQ Overview & data sourcing

| Option | Description | Selected |
|--------|-------------|----------|
| Committed default + regen button | Render committed rfq.json; regen button calls GET /data/rfq | ✓ |
| Always live-generate | GET /data/rfq every visit | |
| Committed only | No regen | |

| Option | Description | Selected |
|--------|-------------|----------|
| Full, grouped + summary on top | Summary then full scope/items/commercials/questionnaire/compliance | ✓ |
| Summary + drill-down | Full detail behind expanders | |
| Compact key facts | Scope + item titles + dates only | |

**User's choice:** Committed default + regen button · Full, grouped + summary on top

---

## H. Client streaming, env wiring & failure states

| Option | Description | Selected |
|--------|-------------|----------|
| fetch + ReadableStream | Streaming body reader for POST-SSE; endpoints stay POST | ✓ |
| Switch endpoints to GET | EventSource-friendly GET endpoints | |

| Option | Description | Selected |
|--------|-------------|----------|
| Base URL public, key server-only | NEXT_PUBLIC_AI_BASE_URL; OpenAI key server-side; CORS allowlist | ✓ |
| Proxy via Next API routes | Route AI calls through Next server | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stream progress + explicit errors | Live status events; explicit error state, never blank/fabricated | ✓ |
| Spinner + generic error | Simple spinner + generic message | |

| Option | Description | Selected |
|--------|-------------|----------|
| Desktop-first + keyboard-accessible | Optimize for desk; no dedicated mobile layout | |
| Fully responsive | Mobile/tablet + desktop layouts | ✓ |

**User's choice:** fetch + ReadableStream · Base URL public, key server-only · Stream progress + explicit errors · Fully responsive
**Notes:** User chose fully responsive over the desktop-first recommendation; planner to keep responsive work proportionate to the 10% weight (reflow, not redesign) and keep AI-showcase surfaces legible at narrow widths.

---

## Claude's Discretion

- Component breakdown, shadcn primitives, file/route structure under `app/(buyer)/`.
- Text-extraction libraries per upload format + empty-extraction threshold for the paste-fallback.
- Client SSE parser implementation + session-cache mechanism + loading/skeleton treatment.
- Mermaid diagram granularity; README/write-up section ordering (within the rubric).
- Standalone vs shared `docs/prompts/` files; which prompt's failure becomes the PROMPT-04 example.
- New raw-text input path as a new endpoint vs a thin wrapper before `/extract/vendor`.

## Deferred Ideas

- Loadable committed AI result — rejected (reads as hardcoded, §24).
- Next.js proxy layer for AI calls — rejected (moving parts + SSE buffering risk).
- Stateful clarification → re-extraction loop — v2 (FLOW-01/02).
- Production OCR / layout-aware parsing — v2 (INPUT-05).
- Bespoke mobile redesign beyond responsive reflow — out (proportionality to 10% weight).
