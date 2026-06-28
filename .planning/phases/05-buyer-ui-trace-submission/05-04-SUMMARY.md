---
phase: 05-buyer-ui-trace-submission
plan: "04"
subsystem: apps/web
tags: [ui, rfq-overview, vendor-input, static-data, sse, shadcn]
dependency_graph:
  requires: ["05-02", "05-03"]
  provides: ["UI-01", "UI-02", "INPUT-01", "INPUT-02", "INPUT-03", "INPUT-04", "UI-06"]
  affects:
    - apps/web/app/(buyer)/rfq/page.tsx
    - apps/web/app/(buyer)/rfq/regen-button.tsx
    - apps/web/app/(buyer)/input/page.tsx
    - apps/web/app/api/traces/[name]/route.ts
    - apps/web/public/data/
    - apps/web/public/traces/
tech_stack:
  added: []
  patterns:
    - Server Component + client island (RegenButton) for D-21 instant-load
    - Static JSON import at module scope for zero-fetch sample cards (D-04)
    - BuyerContext append-by-default setLoadedVendors (Plan 05-03 contract)
    - Path-traversal sanitization in Next.js Route Handler (T-05-04-A)
key_files:
  created:
    - apps/web/app/(buyer)/rfq/page.tsx
    - apps/web/app/(buyer)/rfq/regen-button.tsx
    - apps/web/app/(buyer)/input/page.tsx
    - apps/web/app/api/traces/[name]/route.ts
    - apps/web/public/data/rfq.json
    - apps/web/public/data/vendor_thorough.json
    - apps/web/public/data/vendor_cheap.json
    - apps/web/public/data/vendor_fluff.json
    - apps/web/public/traces/ (6 JSON files)
  modified: []
decisions:
  - "rfq/page.tsx is a Server Component; only RegenButton is a client island — keeps D-21 instant-load without a spinner on first render"
  - "RegenButton on success calls window.location.reload() — page is a Server Component so router.refresh() would be partial; full reload picks up regenerated JSON"
  - "vendor_*.json imported at module scope in input/page.tsx — static build-time resolution, no fetch/spinner on the hero path (D-04)"
  - "weak-extraction Alert uses variant='default' with amber-intent copy — Alert 'destructive' reserved for hard errors, not soft warnings (UI-SPEC)"
metrics:
  duration: "~4 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_changed: 13
---

# Phase 5 Plan 04: RFQ Overview + Vendor Input Screens Summary

**One-liner:** RFQ Overview as an instant Server Component with a RegenButton client island (D-21/D-22), and a Vendor Input screen with all three input paths — sample cards, paste form, and file upload — wired to BuyerContext's append-by-default setLoadedVendors (D-04/D-05/D-06).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Static data setup + fixture check + RFQ Overview screen + trace route | d8e6714 | rfq/page.tsx, regen-button.tsx, api/traces/[name]/route.ts, public/data/ (4 files), public/traces/ (6 files) |
| 2 | Vendor Input screen | bbd5478 | input/page.tsx |

## What Was Built

### Task 1 — RFQ Overview + static data + trace route handler (commit d8e6714)

**Static data setup:** `mkdir -p public/data public/traces` and copied all 4 data JSONs + 6 trace JSONs. Fixture conformance check (`uv run python -c "…"`) passed: all three vendor JSONs validate against the current `VendorResponse` schema.

**RFQ Overview (`/rfq`):**
- `rfq/page.tsx` — pure Server Component; imports committed `public/data/rfq.json` at module scope via `import rfqRaw from "../../../public/data/rfq.json"`. No `useEffect`, no spinner. D-21 instant-load achieved.
- Render hierarchy per D-21/D-22: page title (text-3xl), Summary Card (event name, dates, 8 line items, commercial summary, budget if present), Separator, full structured body (Scope, Timelines, Line Items, Commercial Expectations, Vendor Questionnaire, Compliance Requirements) — all as Cards.
- `regen-button.tsx` — `"use client"` island with `useState` for `loading` and `error`. Button shows "Regenerating..." and `disabled={true}` during the fetch; calls `fetchRfq()` from `@/lib/api` on click; on success calls `window.location.reload()` to force Server Component re-render with fresh data.

**Trace Route Handler (`/api/traces/[name]`):**
- Reads from `path.join(process.cwd(), "public", "traces", safe)`.
- T-05-04-A mitigated: `name.replace(/[^a-zA-Z0-9_.-]/g, "")` before path.join — no path traversal.
- Returns `Content-Type: application/json` on hit, 404 on ENOENT, 500 otherwise.

### Task 2 — Vendor Input screen (commit bbd5478)

`input/page.tsx` — `"use client"` (needs `useState` for all three paths + `useRef` for file input).

**Section 1 — Hero (D-04):** Three `SampleCard` objects built from static JSON imports (`vendor_thorough.json`, `vendor_cheap.json`, `vendor_fluff.json`) — no fetch, no delay. Rendered as a `grid-cols-1 md:grid-cols-3` grid. Each card has `data-testid="vendor-card-{id}"` for Playwright. "Load Sample" button calls `setLoadedVendors(prev => [...prev, sample.vendor])` (APPEND) and `router.push("/extraction")`.

Min-vendor notice: renders `Alert` with "Load at least 2 vendors to use the Comparison screen." only when `loadedVendors.length === 1`. Empty-state copy renders when `loadedVendors.length === 0`.

**Section 2 — Paste path (D-06):** `Input` (vendor name, required) + `Textarea` (8 rows) + "Submit for Extraction" Button (disabled when name empty or loading). POSTs `{vendor_name, raw_text}` to `/input/raw-text`, receives `VendorResponse`, appends to context, navigates to `/extraction`. `StreamProgress` shows during fetch.

**Section 3 — File upload (D-05):** Hidden `<input type="file" accept=".pdf,.docx,.xlsx,.pptx">` triggered by a dashed drop zone. Vendor name `Input` required. "Extract & Analyze" Button appears after file selection. Upload flow: POST `FormData` to `/extract/file-text` → check `chars < 200` (if weak: show Alert, stop) → POST extracted text to `/input/raw-text` → append to context → navigate.

## Deviations from Plan

None — plan executed exactly as written, with two minor mechanical adjustments:

**1. [Rule 1 - Bug] JSON import path was `../../../../public/data/rfq.json` in plan but actual depth is `../../../`**
- **Found during:** Task 1 TypeScript check
- **Issue:** `app/(buyer)/rfq/page.tsx` is 3 directory levels deep from `apps/web/`, not 4. The plan's `../../../../` resolves to the wrong directory.
- **Fix:** Changed to `../../../public/data/rfq.json`.
- **Files modified:** apps/web/app/(buyer)/rfq/page.tsx

**2. [Rule 2 - Correctness] RegenButton on success uses `window.location.reload()` instead of `router.refresh()`**
- **Reason:** The RFQ page is a Server Component. `router.refresh()` in Next.js App Router re-fetches server data but the committed JSON import is resolved at build time, not request time — so `router.refresh()` would not pick up newly regenerated data from the API. A full page reload correctly triggers re-execution of the Server Component with updated cache.
- **Files modified:** apps/web/app/(buyer)/rfq/regen-button.tsx

## Known Stubs

None. Both screens are fully wired:
- `/rfq` renders from committed JSON; RegenButton calls a real endpoint.
- `/input` sample-load reads real vendor JSON files; paste/upload paths POST to real AI service endpoints.
- No hardcoded empty values, no placeholder text in the render path.

## Threat Flags

No new threat surfaces beyond the plan's threat model. T-05-04-A mitigated (path sanitization in route handler). T-05-04-B accepted (server-side 20 MB limit from Plan 05-02). T-05-04-C accepted (raw text passed through to extraction agent).

## Self-Check: PASSED

- [x] `apps/web/app/(buyer)/rfq/page.tsx` exists
- [x] `apps/web/app/(buyer)/rfq/regen-button.tsx` exists (contains "Regenerating...", "disabled", "setLoading" equivalents)
- [x] `apps/web/app/(buyer)/input/page.tsx` exists
- [x] `apps/web/app/api/traces/[name]/route.ts` exists (contains sanitization regex)
- [x] `apps/web/public/data/rfq.json` exists
- [x] `apps/web/public/traces/` has 6 JSON files
- [x] Commits d8e6714 and bbd5478 present in git log
- [x] `pnpm tsc --noEmit` exits 0 (no type errors)
- [x] Fixture conformance: `fixtures OK`
- [x] Acceptance criteria: all grep checks pass (Load Sample ≥1, Submit for Extraction ≥1, Extract & Analyze ≥1, setLoadedVendors ≥2, prev spread ≥1, chars<200 ≥1, /input/raw-text ≥1, data-testid ≥3, "at least 2 vendors" ≥1)
