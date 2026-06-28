---
phase: 05-buyer-ui-trace-submission
fixed_at: 2026-06-28T00:00:00Z
review_path: .planning/phases/05-buyer-ui-trace-submission/05-REVIEW.md
iteration: 1
findings_in_scope: 14
fixed: 14
skipped: 0
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-06-28
**Source review:** .planning/phases/05-buyer-ui-trace-submission/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 14 (fix_scope = all → Critical + Warning + Info)
- Fixed: 14
- Skipped: 0

**Verification (run by fixer, per CLAUDE.md §11):**
- `cd apps/web && pnpm build` → ✓ compiled, TypeScript clean, all 8 routes generated.
- `cd apps/web && pnpm tsc --noEmit` → ✓ exit 0 after every edit.
- `cd services/ai && uv run pytest` → 144 passed, 1 xfailed (identical to pre-fix baseline — no regression).
- `cd services/ai && uv run ruff check tests/...` → F401 cleared on the edited test files (3 remaining E501 line-length errors are pre-existing on untouched lines).

> Note: `pnpm lint` reports `react-hooks/set-state-in-effect` errors in `comparison/page.tsx`,
> `extraction/page.tsx`, and `BuyerContext.tsx`. These are **pre-existing** (present on the
> committed pre-fix files, verified via `git show HEAD~N`) and are not part of the build/ship
> gate (`pnpm build` passes). They were not introduced by these fixes and were out of scope.

## Fixed Issues

### CR-01: `conflicting` extracted fields display values with no evidence snippet

**Files modified:** `apps/web/app/(buyer)/extraction/page.tsx`
**Commit:** d945087
**Applied fix:** Rewrote `FieldRow` so evidence is surfaced for any field carrying a grounded
span — no longer hard-gated on `status === "present"`. For `conflicting` fields, each
`ConflictingValueStr` in `field.values[]` is rendered with its OWN `evidence[0].snippet`
(confirmed against `packages/shared-types/index.d.ts:277-280`), so a grounded conflicting value
is never mislabeled "No verified source". Preserves the absence-state machinery (FlagBadge per
field, "No verified source" still correct for missing/unclear/unsupported with no evidence).
Directly addresses CLAUDE.md §1 (evidence over assertion) / §8.

### CR-02: Comparison auto-start captures a stale `extractionList`

**Files modified:** `apps/web/app/(buyer)/comparison/page.tsx`
**Commit:** 4d1b4e6 (combined refactor — see WR-01/WR-02 below)
**Applied fix — requires human verification (logic/state correctness):** The auto-start effect
now snapshots the fresh extraction list *inside* the effect (`Object.keys(extractions).map(...)`)
instead of closing over a render-time `extractionList`, guards `snapshot.length < 2`, and depends
on `[rfq, vendorNames.length]` so it re-evaluates when the available vendor count changes. The
shared consume loop `break`s on terminal `result`/`done`/`error` so a late event can no longer flip
a rendered comparison back into an error state. Flagged for human verification because the fix
changes effect dependency/timing semantics (a logic/state-machine change that passes typecheck +
build but warrants a manual confirm that auto-start fires exactly once with the full vendor set).

### WR-01: Comparison unmount-abort cleanup aborts the wrong controller

**Files modified:** `apps/web/app/(buyer)/comparison/page.tsx`
**Commit:** 4d1b4e6
**Applied fix:** The auto-start effect now OWNS its `AbortController` + a `cancelled` guard and
aborts on deps-change re-run AND unmount (mirroring `extraction/page.tsx`). The manual "Run
Comparison" run stores its controller in `abortRef`; a minimal unmount-only effect aborts
`abortRef.current` so an in-flight manual run is cancelled on unmount (abort is idempotent).

### WR-02: Duplicated SSE-consumer logic in comparison page has already drifted

**Files modified:** `apps/web/app/(buyer)/comparison/page.tsx`
**Commit:** 4d1b4e6
**Applied fix:** Extracted a single `runComparison(list, rfq, controller, isCancelled)` async
function — the one source of truth for the consume loop, error string, and state transitions —
called by both the auto-start effect and the manual button. Removes the two drifted copies
(the auto/manual error strings are now unified). Root-cause dedup per CLAUDE.md §2 minimalism.

### WR-03: `pricing_status` is force-cast, silently dropping unknown flag state

**Files modified:** `apps/web/components/flag-badge.tsx` (commit 7d24513),
`apps/web/app/(buyer)/comparison/page.tsx` (commit 4d1b4e6 — caller cast removal)
**Commit:** 7d24513 (FlagBadge root cause) + 4d1b4e6 (caller)
**Applied fix:** Fixed the root cause once in `FlagBadge`: it now accepts `FlagStatus | string`,
falls back to a neutral variant for any out-of-enum value, and always renders the literal label —
so a bare-str `pricing_status` like `"bundled"` renders as a visible badge instead of an unstyled
raw string (absence/flag state stays surfaced, §8). The unsafe `as` cast at the comparison-page
call site was removed (no longer needed). Did NOT widen the pydantic schema (out of scope —
would require regenerating shared-types and re-verifying all callers; the component-side fix is
the minimal correct change).

### WR-04: Extraction streaming `error` after `result` not guarded

**Files modified:** `apps/web/app/(buyer)/extraction/page.tsx`
**Commit:** 89c74b0
**Applied fix — requires human verification (logic/state correctness):** Added `break` after the
terminal `result`/`done`/`error` events in the extraction SSE loop, so a late/flaky `error` after
a cached `result` no longer renders the destructive alert over the just-cached extraction. Flagged
for human verification because it is a state-machine/control-flow change.

### WR-05: `fetchRfq()` failure silently swallowed → permanently idle screen

**Files modified:** `apps/web/app/(buyer)/comparison/page.tsx` (commit 4d1b4e6),
`apps/web/app/(buyer)/extraction/page.tsx` (commit 1b0d7fb)
**Commit:** 4d1b4e6 (comparison) + 1b0d7fb (extraction)
**Applied fix:** Both pages now set an `rfqError` state on `fetchRfq()` failure and render an
explicit destructive alert ("Could not load the RFQ — check the AI service is running, then reload
this page.") instead of leaving an inert/blank screen (CLAUDE.md §11 / D-25 — error states
explicit, not blank).

### WR-06: Input page upload/paste — no unmount guard, late setState after navigation

**Files modified:** `apps/web/app/(buyer)/input/page.tsx`
**Commit:** 7404b8f (combined with WR-07 — same handlers, intermixed hunks)
**Applied fix:** Added a `mountedRef` (set false in an unmount cleanup effect) and guarded all
post-await writes — `setLoadedVendors`, `router.push`, error, and loading state — in both
`handlePasteSubmit` and `handleFileExtract`, so a fetch resolving after the user navigates away
no longer sets state on an unmounted component or triggers a surprise navigation.

### WR-07: File upload — no client-side size guard, opaque "HTTP 413"

**Files modified:** `apps/web/app/(buyer)/input/page.tsx`
**Commit:** 7404b8f (combined with WR-06)
**Applied fix:** Added a `MAX_UPLOAD_BYTES = 20_000_000` pre-check (mirrors the server cap in
`services/ai/api/app.py:154`) before upload, surfacing "File too large — max 20 MB." instead of
uploading the whole file and failing late. Also mapped a 413 response to the same human message
rather than echoing the bare HTTP status code.

> Note: WR-06 and WR-07 modify the same two handlers in `input/page.tsx` with intermixed hunks;
> committed together in 7404b8f (interactive partial staging unavailable). Both findings are
> fully applied.

### IN-01: Unused `import pytest` fails the repo's ruff `F` lint gate

**Files modified:** `services/ai/tests/test_file_extract.py`, `services/ai/tests/test_input_wrap.py`
**Commit:** 7cf4f11
**Applied fix:** Removed the unused `import pytest` line from both GREEN-phase test stubs (no
`pytest.` reference remains in either). Verified: F401 cleared by `ruff check`; full pytest suite
still 144 passed / 1 xfailed.

### IN-02: EvidenceSnippet "Show in context" is redundant

**Files modified:** `apps/web/components/evidence-snippet.tsx`,
`apps/web/app/(buyer)/extraction/page.tsx`
**Commit:** c24d49c
**Applied fix:** `snippet` and `sourcePassage` were always the identical value, so the Collapsible
expanded to text already shown inline; the `Evidence` contract carries no separate
surrounding-passage source to reveal. Simplified `EvidenceSnippet` to the inline snippet only,
dropped the `sourcePassage` prop, and removed both call-site args in `FieldRow`. No test/spec
referenced "Show in context".

### IN-03: `RegenButton` ignores its only prop; `initialRfq` is dead

**Files modified:** `apps/web/app/(buyer)/rfq/regen-button.tsx`,
`apps/web/app/(buyer)/rfq/page.tsx`
**Commit:** d22b98c
**Applied fix:** Removed the unused `initialRfq` prop, the `RegenButtonProps` interface, and the
now-dead `RFQ` import; the only caller now renders `<RegenButton />` with no props.

### IN-04: `BuyerContext.setLoadedVendors` split append/replace contract

**Files modified:** `apps/web/contexts/BuyerContext.tsx`
**Commit:** c9cd195
**Applied fix:** Collapsed the split append-array / replace-via-function setter (whose
array-append branch no real caller exercised) to the standard
`Dispatch<SetStateAction<VendorResponse[]>>` — exposing the raw `setLoadedVendorsState`. All three
callers already use the functional form `(prev) => [...prev, x]`, so the append-vs-replace decision
now lives unambiguously at the call site; the dead branch is removed. Typecheck clean.

### IN-05: Trace `displayName` + `order` duplicate the filename literal list

**Files modified:** `apps/web/app/(buyer)/trace/page.tsx`
**Commit:** d463acf
**Applied fix:** Replaced the parallel hand-synced `order` array and `displayName` if-chain with a
single `TRACE_LABELS` map keyed on filename stem. Insertion order defines the canonical trace
order; the map provides labels; unlisted files fall back to underscores-to-spaces and sort last.

## Skipped Issues

None — all 14 in-scope findings were fixed.

---

_Fixed: 2026-06-28_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
