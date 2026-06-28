---
phase: 05-buyer-ui-trace-submission
plan: "06"
subsystem: apps/web
tags: [extraction-review, vendor-comparison, sse, evidence-snippets, comparability-matrix]
dependency_graph:
  requires:
    - 05-03  # BuyerContext, api.ts (streamExtract/streamCompare/normalizeExtractionPayload/fetchRfq), EvidenceSnippet, FlagBadge, StreamProgress, ComparabilityBadge
    - 05-04  # RFQ Overview + Vendor Input screens (nav context)
  provides:
    - UI-03  # Extraction Review screen
    - UI-04  # Vendor Comparison screen
  affects:
    - apps/web/app/(buyer)/extraction/page.tsx
    - apps/web/app/(buyer)/comparison/page.tsx
tech_stack:
  added: []
  patterns:
    - SSE streaming with AbortController on unmount (T-05-06-C)
    - Session-cached result skips re-stream (D-02)
    - Phase-driven StreamProgress (not a +20% counter) (D-25)
    - Absence-first FieldRow with EvidenceSnippet "No verified source" fallback (D-07)
    - Buyer-first information hierarchy: Gaps & Risks / Attention panel always first (UI-06)
    - ComparabilityMatrix with TooltipProvider for verdict reasons
    - Stable vendor column order (D-13 — no sort)
key_files:
  created:
    - apps/web/app/(buyer)/extraction/page.tsx
    - apps/web/app/(buyer)/comparison/page.tsx
  modified: []
decisions:
  - Extraction SSE auto-starts on mount when vendor selected + rfq loaded; comparison SSE auto-starts when ≥2 extractions + rfq (both with manual fallback button for comparison)
  - Phase progress driven from status event's "phase" field (model→40%, grounding→80% for extraction; align/comparability/compare/clarify sequence for comparison)
  - normalizeExtractionPayload separates downgrade_report from ExtractionResult before caching — bare ComparisonResult cast for comparison (asymmetric per API contract)
  - collectFlaggedFields helper sorts by severity (missing→conflicting→unclear→unsupported) for Gaps & Risks panel
metrics:
  duration: ~18min
  completed_date: "2026-06-28"
  tasks: 2
  files: 2
---

# Phase 05 Plan 06: Extraction Review + Vendor Comparison Summary

**One-liner:** Extraction Review (UI-03) and Vendor Comparison (UI-04) — evidence-first, absence-first AI-showcase screens with SSE streaming, session caching, and D-07..D-14 compliance.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extraction Review screen (UI-03) | 8927bc9 | apps/web/app/(buyer)/extraction/page.tsx |
| 2 | Vendor Comparison screen (UI-04) | 11be3f2 | apps/web/app/(buyer)/comparison/page.tsx |

## What Was Built

### Task 1: Extraction Review (UI-03)

`apps/web/app/(buyer)/extraction/page.tsx` implements:

- **Gaps & Risks panel** (`data-testid="gaps-panel"`, D-08): always-visible, buyer-first. Lists all non-present fields sorted by severity (missing → conflicting → unclear → unsupported) with FlagBadge per field. Shows "All fields present — no gaps detected." when none.
- **Vendor selector Tabs** (`data-testid="vendor-tabs"`, D-10): one tab per loadedVendor; switching tabs changes `selectedVendor` state.
- **Session cache check** (D-02): if `extractions[selectedVendor]` exists, renders immediately without firing SSE.
- **SSE streaming** via `streamExtract`: `AbortController` created per-vendor SSE call; `abort()` called in `useEffect` cleanup on unmount (T-05-06-C mitigate).
- **Phase-driven progress** (D-25): `status` event's `phase` field drives progress — `"model"→40`, `"grounding"→80`, done→100. Not a +20% counter.
- **`normalizeExtractionPayload`**: separates `downgrade_report` from `ExtractionResult` before caching. Only clean `ExtractionResult` stored in `extractions[]`.
- **8 Category Cards** (`data-testid="extraction-result"`, D-09): scope, pricing, commercial_terms, timeline, compliance, assumptions, exclusions, risks. Line items rendered under scope and pricing with `li.pricing` / `li.scope_coverage` exact field names from shared-types.
- **`FieldRow` component**: grid layout with field label + `FlagBadge(status)` left, value + `EvidenceSnippet` right. `undefined` snippet passed for non-present fields → renders "No verified source" (§8 absence-first; never a fake snippet).
- **Error state** (`data-testid="extraction-error"`): exact copy "Extraction could not complete. {error} — Try reloading or check the AI service is running."
- **Empty state**: Alert linking to `/input` when no vendors loaded.

### Task 2: Vendor Comparison (UI-04)

`apps/web/app/(buyer)/comparison/page.tsx` implements:

- **≥2-vendor empty state**: if 0 extractions → link to /extraction; if 1 extraction → "Load at least 2 vendors to compare" Alert with Button linking to /input. Prevents server 422 (_MIN_VENDORS=2).
- **Session cache** (D-02): if `comparison` exists, renders immediately.
- **SSE streaming** via `streamCompare`: auto-starts when `vendorNames.length >= 2 && rfq` and `comparison` is null. Phase sequence: align→20%, comparability→40%, compare→70%, clarify→90%, done→100%. Manual "Run Comparison" button as fallback.
- **AbortController on mount, abort on unmount** (T-05-06-C).
- **Bare ComparisonResult cast** (no normalization) — comparison result is not spread like extraction.
- **Attention panel** (D-12, buyer-first): card title "Needs Attention — N item(s)"; renders `attention_point.summary` (not `.description`); `clarification_questions` listed separately below attention points.
- **Comparability matrix** (`data-testid="comparability-matrix"`, D-11): vendors as columns (stable input order, D-13), 6 ComparisonDimension rows; `TooltipProvider` wrapping table; each cell `ComparabilityBadge(verdict)` + `Tooltip` with `reason`; `overflow-x-auto` for narrow screens (D-26).
- **D-14 note**: "Comparability determined in code from evidence — not a model verdict" always visible below matrix.
- **Data readiness** (D-13): per `VendorReadiness`: "Data readiness: N/6 dimensions comparable"; Tooltip: "Not a ranking or score".
- **Line-item offer table** (Collapsible, D-11): grouped by line item name, vendors as columns, `pricing_verbatim` + `FlagBadge(pricing_status)`.
- **Per-dimension narratives** (Collapsible per dimension, D-11): trigger "Show {dimension} detail".
- **No sort/rank logic**: `grep -cE "\bsort\b|\brank\b"` returns 0.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — both screens wire live SSE data from BuyerContext and call real API endpoints. No hardcoded or placeholder data.

## Threat Flags

No new threat surfaces introduced beyond what the plan's threat model accounts for (T-05-06-A, T-05-06-B, T-05-06-C). T-05-06-C mitigated: `AbortController` created on mount, `abort()` called in cleanup `useEffect` in both screens.

## Self-Check

### Files exist
- apps/web/app/(buyer)/extraction/page.tsx: FOUND
- apps/web/app/(buyer)/comparison/page.tsx: FOUND

### Commits exist
- 8927bc9: feat(05-06): Extraction Review screen — FOUND
- 11be3f2: feat(05-06): Vendor Comparison screen — FOUND

### TypeScript
- `pnpm tsc --noEmit` (via node_modules/.bin/tsc -p apps/web/tsconfig.json): 0 errors

## Self-Check: PASSED
