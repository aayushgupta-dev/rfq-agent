---
phase: "05"
plan: "03"
subsystem: apps/web
tags: [ui, shadcn, sse, context, components]
dependency_graph:
  requires: ["05-01"]
  provides: ["05-04", "05-05", "05-06", "05-07"]
  affects: ["apps/web/app/(buyer)", "apps/web/lib", "apps/web/contexts", "apps/web/components"]
tech_stack:
  added: [badge, card, tabs, separator, textarea, input, progress, skeleton, alert, tooltip, collapsible, scroll-area]
  patterns: [shadcn new-york, fetch+ReadableStream SSE, React Context + sessionStorage, named exports]
key_files:
  created:
    - apps/web/app/page.tsx
    - apps/web/app/(buyer)/layout.tsx
    - apps/web/lib/sse.ts
    - apps/web/lib/session.ts
    - apps/web/lib/api.ts
    - apps/web/contexts/BuyerContext.tsx
    - apps/web/components/stage-rail.tsx
    - apps/web/components/flag-badge.tsx
    - apps/web/components/comparability-badge.tsx
    - apps/web/components/evidence-snippet.tsx
    - apps/web/components/stream-progress.tsx
    - apps/web/components/ui/badge.tsx
    - apps/web/components/ui/card.tsx
    - apps/web/components/ui/tabs.tsx
    - apps/web/components/ui/separator.tsx
    - apps/web/components/ui/textarea.tsx
    - apps/web/components/ui/input.tsx
    - apps/web/components/ui/progress.tsx
    - apps/web/components/ui/skeleton.tsx
    - apps/web/components/ui/alert.tsx
    - apps/web/components/ui/tooltip.tsx
    - apps/web/components/ui/collapsible.tsx
    - apps/web/components/ui/scroll-area.tsx
  modified: []
decisions:
  - "SSE buf accumulation: buf += decoder.decode(value, { stream: true }) — chunks straddle read() calls; decoding each independently causes JSON parse errors (Pitfall 1)"
  - "api.ts request body uses 'vendor_response' key (not 'vendor') matching FastAPI ExtractionRequest — documented in comment"
  - "BuyerContext.setLoadedVendors is append-by-default (prev => [...prev, ...updater]); clearVendors() for replacement"
  - "normalizeExtractionPayload destructs downgrade_report from extraction SSE payload before caching clean ExtractionResult"
  - "EvidenceSnippet renders 'No verified source' (not empty/undefined) when snippet absent — absence is first-class"
  - "StreamProgress accepts pre-computed value prop; phase name drives caller to compute: model→40%, grounding→80%, done→100%"
metrics:
  duration: "~18 min"
  completed: "2026-06-28"
  tasks: 3
  files: 23
---

# Phase 05 Plan 03: UI Substrate — shadcn, Shell, SSE Spine, Display Components Summary

**One-liner:** Full UI substrate — 12 shadcn components vendored, buyer shell with responsive stage rail, fetch+ReadableStream SSE parser with buf accumulation, typed BuyerContext with sessionStorage persistence, and 5 reusable display components (FlagBadge, ComparabilityBadge, EvidenceSnippet, StreamProgress, StageRail).

## What Was Built

### Task 1 — shadcn components + app shell (commit e4018ba)

Added 12 shadcn components (badge, card, tabs, separator, textarea, input, progress, skeleton, alert, tooltip, collapsible, scroll-area) into `components/ui/`. All vendored via `npx shadcn@latest add` — source is owned, no runtime kit dependency.

Replaced `app/page.tsx` placeholder with a server-side `redirect("/rfq")`. Created `app/(buyer)/layout.tsx` with the two-column flex shell (StageRail + main content), BuyerProvider wrapping children, and a hamburger placeholder for `<md` screens.

### Task 2 — Streaming spine (commit 011bde3)

- **lib/sse.ts**: `streamSSE` async generator using `fetch + ReadableStream` (D-23). Critical: `buf += decoder.decode(value, { stream: true })` accumulates across `read()` calls — partial SSE events straddling chunk boundaries are correctly reassembled before JSON parsing.
- **lib/session.ts**: Thin typed `getSession<T>` / `setSession<T>` wrappers with `typeof window === "undefined"` SSR guard and try/catch for malformed JSON.
- **lib/api.ts**: `streamExtract` (body key `vendor_response` — not `vendor`), `streamCompare`, `fetchRfq`, `normalizeExtractionPayload` (destructs `downgrade_report` from extraction SSE payload sibling before caching clean `ExtractionResult`).
- **contexts/BuyerContext.tsx**: Provider with `loadedVendors`, `extractions`, `downgradeReports`, `comparison`. Hydrated from sessionStorage on mount, persisted on each mutation. `setLoadedVendors` is append-by-default; `clearVendors()` for full replacement.

### Task 3 — Display components (commit c22043c)

Five components per 05-PATTERNS.md:
- **StageRail**: 5 nav items (RFQ Overview, Vendor Input, Extraction Review, Comparison, Prompt Trace), active state via `usePathname`, responsive — hidden `sm`, icon-only `md`, full labels `lg`.
- **FlagBadge**: 5-state palette (green/red/amber/orange/slate) — missing is red, absence is first-class.
- **ComparabilityBadge**: 3-verdict palette (primary/amber/red).
- **EvidenceSnippet**: Always-visible `Source:` label with `data-testid="evidence-snippet"` for Playwright. Renders `No verified source` (not empty/undefined) when `snippet` absent. Collapsible source passage when both `snippet` and `sourcePassage` present.
- **StreamProgress**: `phase` + pre-computed `value` props; full-width no horizontal padding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] normalizeExtractionPayload cast required `unknown` intermediate**
- **Found during:** Task 2 TypeScript check
- **Issue:** `{ downgrade_report, ...result }` spreads into `{ [x: string]: unknown }` which TypeScript won't directly cast to `ExtractionResult` without an intermediate `unknown` cast
- **Fix:** `result as unknown as ExtractionResult` — safe because the payload IS an ExtractionResult; the intermediate cast is structurally correct
- **Files modified:** apps/web/lib/api.ts

None — plan executed essentially as written, with one minor TypeScript cast adjustment.

## Known Stubs

None. This plan creates pure infrastructure (no data rendering, no AI calls). All components accept props from future screen pages — no hardcoded data, no empty placeholders that block the plan's goal.

## Threat Flags

No new threat surfaces beyond those documented in the plan's threat model (T-05-03-A, T-05-03-B, T-05-03-C). All three are accepted per the threat register.

## Self-Check: PASSED

All 11 source files exist on disk. All 3 task commits verified in git log.
TypeScript (`pnpm tsc --noEmit`) exits 0 across all files.
