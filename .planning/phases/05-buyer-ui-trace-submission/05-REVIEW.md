---
phase: 05-buyer-ui-trace-submission
reviewed: 2026-06-28T00:00:00Z
depth: standard
files_reviewed: 36
files_reviewed_list:
  - apps/web/app/(buyer)/comparison/page.tsx
  - apps/web/app/(buyer)/extraction/page.tsx
  - apps/web/app/(buyer)/input/page.tsx
  - apps/web/app/(buyer)/layout.tsx
  - apps/web/app/(buyer)/rfq/page.tsx
  - apps/web/app/(buyer)/rfq/regen-button.tsx
  - apps/web/app/(buyer)/trace/page.tsx
  - apps/web/app/(buyer)/trace/trace-tabs.tsx
  - apps/web/app/api/traces/[name]/route.ts
  - apps/web/app/page.tsx
  - apps/web/components/comparability-badge.tsx
  - apps/web/components/evidence-snippet.tsx
  - apps/web/components/flag-badge.tsx
  - apps/web/components/stage-rail.tsx
  - apps/web/components/stream-progress.tsx
  - apps/web/components/ui/alert.tsx
  - apps/web/components/ui/badge.tsx
  - apps/web/components/ui/card.tsx
  - apps/web/components/ui/collapsible.tsx
  - apps/web/components/ui/input.tsx
  - apps/web/components/ui/progress.tsx
  - apps/web/components/ui/scroll-area.tsx
  - apps/web/components/ui/separator.tsx
  - apps/web/components/ui/skeleton.tsx
  - apps/web/components/ui/tabs.tsx
  - apps/web/components/ui/textarea.tsx
  - apps/web/components/ui/tooltip.tsx
  - apps/web/contexts/BuyerContext.tsx
  - apps/web/lib/api.ts
  - apps/web/lib/session.ts
  - apps/web/lib/sse.ts
  - services/ai/api/app.py
  - services/ai/pyproject.toml
  - services/ai/tests/test_file_extract.py
  - services/ai/tests/test_input_wrap.py
  - docs/qa/phase5-playwright.spec.ts
findings:
  critical: 2
  warning: 7
  info: 5
  total: 14
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-28
**Depth:** standard
**Files Reviewed:** 36
**Status:** issues_found

## Summary

This phase is the buyer-facing Next.js UI plus a thin FastAPI trace/proxy layer. The thin-client
discipline is mostly held — no business logic leaks into the frontend, grounding/clamp results are
rendered as the AI service emits them, and the SSE parser correctly handles the `\r\n\r\n` boundary
gotcha. The trace API route's path-traversal sanitizer is sound.

However, two reliability defects directly undermine the graded product principles in CLAUDE.md §1
("evidence over assertion", "absence first-class"):

1. **`conflicting` extracted fields render their values with NO evidence snippet** — the buyer sees
   a contradictory fact stated as if unsourced, and the EvidenceSnippet falsely prints "No verified
   source" even though grounded evidence exists on the conflicting values. This is the exact
   failure the rubric penalizes (a fact shown without its evidence).
2. **The comparison `result` event handler does not stop on `done`/abort robustly, and a stale
   closure on `extractionList` means the comparison can be run against an empty/partial extraction
   set** — auto-start fires on `[rfq]` only, capturing the first render's `extractionList`.

Several warnings cover error-state gaps on streamed data, a status type-cast that can silently drop
an unknown flag state, and duplicated SSE-consumer logic that has already drifted between the two
code paths in `comparison/page.tsx`. Info items cover unused imports that will fail the repo's own
ruff lint gate (`F401`), and dead/redundant evidence wiring.

## Critical Issues

### CR-01: `conflicting` extracted fields display values with no evidence snippet ("No verified source" shown despite grounded evidence)

**File:** `apps/web/app/(buyer)/extraction/page.tsx:65-83`
**Issue:**
`FieldRow` only pulls evidence when `field.status === "present"`:

```ts
const evidence = field.status === "present" && field.evidence?.length ? field.evidence[0] : undefined;
```

But for a `conflicting` field the value text comes from `field.values[]` (each `ConflictingValueStr`
carries its own `evidence: Evidence[]` per the contract in `packages/shared-types/index.d.ts:277-280`).
The render then shows the joined conflicting values:

```ts
{field.status === "conflicting" && field.values?.length
  ? field.values.map((v, i) => v.value).filter(Boolean).join(" / ")
  : (field.value ?? "—")}
```

…immediately followed by `<EvidenceSnippet snippet={undefined} .../>`, which renders the italic
**"No verified source"** label (`evidence-snippet.tsx:18`). The buyer is shown two contradictory
commercial/technical claims joined with " / " and told there is *no* source for them — when in fact
each value is grounded. This is a direct violation of CLAUDE.md §1 "evidence over assertion" and §8
("every fact is marked... surfaced, never silently filled"): a shown fact loses its evidence, and a
grounded fact is mislabeled as unsourced. It is the precise anti-pattern the rubric scores against.

**Fix:** Surface evidence for conflicting values too, and stop hard-gating on `present`:

```ts
function FieldRow({ label, field }: { label: string; field: FieldStr }) {
  // Direct evidence for present/unclear/unsupported; per-value evidence for conflicting.
  const directEvidence = field.evidence?.length ? field.evidence[0] : undefined;
  const isConflicting = field.status === "conflicting" && field.values?.length;
  return (
    <div className="grid grid-cols-[auto_1fr] gap-2 py-2 border-b border-border last:border-0">
      <div className="flex items-start gap-1.5 pt-0.5">
        <span className="text-xs font-semibold text-muted-foreground">{label}</span>
        <FlagBadge status={field.status} />
      </div>
      <div>
        {isConflicting ? (
          field.values!.map((v, i) => (
            <div key={i}>
              <p className="text-sm">{v.value ?? "—"}</p>
              <EvidenceSnippet snippet={v.evidence?.[0]?.snippet} sourcePassage={v.evidence?.[0]?.snippet} />
            </div>
          ))
        ) : (
          <>
            <p className="text-sm">{field.value ?? "—"}</p>
            <EvidenceSnippet snippet={directEvidence?.snippet} sourcePassage={directEvidence?.snippet} />
          </>
        )}
      </div>
    </div>
  );
}
```
(Confirm the desired UX for `missing`/`unclear`/`unsupported` — those legitimately have no value, so
"No verified source" is correct there. The bug is specifically that `conflicting` and any
`present`-with-evidence-but-mistyped case lose their grounded spans.)

### CR-02: Comparison auto-start captures a stale `extractionList` and can run against the wrong vendor set

**File:** `apps/web/app/(buyer)/comparison/page.tsx:332-396`
**Issue:**
`extractionList` is derived on every render from context (`vendorNames.map((n) => extractions[n])`,
line 335), but the auto-start effect's dependency array is `[rfq]` only (line 396, with
`exhaustive-deps` disabled). The async generator loop on line 370 closes over the `extractionList`
value from the render in which `rfq` first became non-null. If extractions are still arriving in
`BuyerContext` (the extraction page caches them asynchronously, and comparison reads the same
session-backed map), the comparison can fire with a stale list — e.g. only the first vendor present,
or vendor objects from a prior render. The server enforces `_MIN_VENDORS=2`
(`services/ai/api/app.py:302-318`), so a too-short list throws a 422 → the UI shows the generic
"Connection lost" error (line 391) rather than a correct comparison. Worse, if exactly 2 stale
entries are captured, it silently compares the wrong snapshot.

Additionally, the loop never `break`s after a terminal `result`/`done`/`error` event; it relies on
the server closing the stream. If the server emits `result` then keeps the connection open (or emits
a late event), `setStreaming(false)` has already run but the loop keeps consuming — and on `error`
after `result`, the page flips from a rendered comparison back into an error state.

**Fix:** Depend on the actual inputs and guard the snapshot; break on terminal events.

```ts
useEffect(() => {
  if (comparison) return;
  if (extractionList.length < 2 || !rfq) return;
  const controller = new AbortController();
  abortRef.current = controller;
  // ...setStreaming(true) etc.
  (async () => {
    try {
      for await (const event of streamCompare(extractionList, rfq, controller.signal)) {
        if (controller.signal.aborted) return;
        if (event.type === "status") { /* ... */ }
        if (event.type === "result") {
          setComparison(event.payload as ComparisonResult);
          setProgressValue(100); setStreaming(false);
          break; // terminal — stop consuming
        }
        if (event.type === "error") {
          setError((event.payload as { message: string }).message);
          setStreaming(false); break;
        }
        if (event.type === "done") { setStreaming(false); break; }
      }
    } catch (e) { /* ... */ }
  })();
  return () => controller.abort();
}, [rfq, extractionList.length]); // re-evaluate when the available vendor count changes
```
Also add the `cancelled`/abort-guard pattern already used in `extraction/page.tsx:248,288` (the
comparison effect's cleanup on line 352-354 aborts a *different* controller than the one created
inside the auto-start effect — see WR-01).

## Warnings

### WR-01: Comparison unmount-abort cleanup aborts the wrong controller

**File:** `apps/web/app/(buyer)/comparison/page.tsx:351-354` vs `361-362`
**Issue:** The unmount cleanup effect (`return () => { abortRef.current?.abort(); }`, deps `[]`)
captures `abortRef` correctly, but the auto-start effect assigns `abortRef.current = controller`
*and* the manual "Run Comparison" button assigns it again (line 461). There is no per-run cleanup on
the auto-start effect itself (unlike `extraction/page.tsx` which returns
`() => { cancelled = true; controller.abort(); }`). On a deps-change re-run or fast navigation, the
previous in-flight stream is not aborted and can still call `setComparison`/`setError` after the new
run started — a torn-down-run state write. The extraction page already solved this correctly; the
comparison page should mirror it.
**Fix:** Move the abort into the auto-start effect's own cleanup and add a `cancelled` guard, as in
`extraction/page.tsx:254-288`. Then the separate `[]` unmount effect (line 352) is redundant.

### WR-02: Duplicated SSE-consumer logic in comparison page has already drifted

**File:** `apps/web/app/(buyer)/comparison/page.tsx:368-395` and `466-492`
**Issue:** The auto-start effect and the manual "Run Comparison" button each contain a full,
hand-copied SSE consumption loop. They have already diverged: the auto path sets the error to
`"Connection lost. Check the AI service is running."` (line 391) while the manual path sets
`"Connection lost."` (line 488). Two copies of streaming-state logic will keep drifting (one will
get the next bugfix, the other won't) — and CR-02's terminal-`break` fix would have to be applied in
two places. This is the duplication anti-pattern under CLAUDE.md §2 minimalism.
**Fix:** Extract one `runComparison(controller)` async function and call it from both the effect and
the button handler. Single source of truth for the consume loop, error strings, and state
transitions.

### WR-03: `pricing_status` is force-cast, silently dropping any unknown flag state

**File:** `apps/web/app/(buyer)/comparison/page.tsx:247`
**Issue:**
```ts
<FlagBadge status={offer.pricing_status as "present" | "missing" | "unclear" | "conflicting" | "unsupported"} />
```
`LineItemOffer.pricing_status` is typed as a bare `str` on the server
(`services/ai/schemas/domain.py:329`), not the `FlagStatus` enum. The `as` cast tells TypeScript to
trust it. `FlagBadge` then indexes `flagVariants[status]` (`flag-badge.tsx:17`); if the server ever
emits a value outside the five known statuses (e.g. `"not_applicable"`, `"bundled"`), `flagVariants`
returns `undefined`, `cn(...)` drops the class, and the badge renders an unstyled raw string with no
color — an absence/flag state silently degraded rather than surfaced (violates §8). The cast also
hides this at compile time.
**Fix:** Either tighten `pricing_status` to `FlagStatus` in the pydantic schema + regenerate
shared-types (the contract should be the enum, not `str`), or have `FlagBadge` fall back to a neutral
variant and render the literal status for unknown values instead of an unstyled badge. Do not paper
over it with `as`.

### WR-04: Extraction streaming `error` after `result` is not guarded — page can flip from rendered to error

**File:** `apps/web/app/(buyer)/extraction/page.tsx:265-279`
**Issue:** Same structural issue as CR-02 in the extraction loop: after a `result` event sets the
extraction and `streaming=false` (line 272), the loop keeps consuming. A subsequent `error` event
(or a late `error` on a flaky stream) sets `error` state (line 275), which the render gates on
`v.vendor_name === selectedVendor` (line 341) and shows the destructive alert *over* the just-cached
extraction. There is no `break` after the terminal `result`.
**Fix:** `break` after `result` (the extraction route appends exactly one `done`; the result is
terminal for display purposes). Mirror the terminal-break fix from CR-02.

### WR-05: `fetchRfq()` failure is silently swallowed, leaving comparison/extraction permanently idle with no user feedback

**File:** `apps/web/app/(buyer)/comparison/page.tsx:345-349`, `apps/web/app/(buyer)/extraction/page.tsx:222-226`
**Issue:** `fetchRfq().then(setRfq).catch(() => {/* non-fatal */})`. If the RFQ fetch fails (AI
service down, CORS, network), `rfq` stays `null` forever. On the extraction page the SSE will never
fire (effect guards on `!rfq`), and the page shows the vendor tabs with no streaming, no result, and
no error — a blank, stuck screen. On the comparison page auto-start never runs and the manual button
early-returns silently (`if (!rfq || streaming) return;`, line 459). The phase-5 Playwright spec
(`docs/qa/phase5-playwright.spec.ts:123-133`) only asserts the *no-vendors* empty state, so this
stuck-on-rfq-failure path is untested. CLAUDE.md §11 / D-25 require error states to be "explicit not
blank".
**Fix:** Set an error state on `fetchRfq` failure and render an alert ("Could not load the RFQ —
check the AI service is running"), and disable/guide the user instead of leaving an inert screen.

### WR-06: Input page upload/paste have no AbortController and no unmount guard — late `setLoadedVendors` after navigation

**File:** `apps/web/app/(buyer)/input/page.tsx:76-139`
**Issue:** Both `handlePasteSubmit` and `handleFileExtract` `await fetch(...)` then call
`setLoadedVendors` and `router.push("/extraction")`. There is no AbortController and no cancellation
guard. If the user navigates away (or the component unmounts) while the fetch is in flight, the
resolved promise still calls `setLoadedVendors`/`router.push`, producing a "set state on unmounted
component" path and a surprise navigation. The two streamed pages were hardened with AbortController
(T-05-06-C); the input fetches were not.
**Fix:** Add an AbortController per submit, pass `signal` to `fetch`, and ignore the resolution if
aborted. At minimum, guard the post-await `setLoadedVendors`/`router.push` behind a mounted ref.

### WR-07: File upload sends raw bytes to `/extract/file-text` with no client-side size guard — large files fail late with an opaque "HTTP 413"

**File:** `apps/web/app/(buyer)/input/page.tsx:101-139`
**Issue:** The server rejects files >20 MB with 413 (`services/ai/api/app.py:154`), but only after
the entire file is uploaded. The client appends `uploadFile` to FormData with no size pre-check, so a
large file uploads fully and then fails with the generic `throw new Error(\`HTTP ${extractRes.status}\`)`
(line 115) → the alert shows the bare string "HTTP 413" with no explanation. Poor UX and wasted
bandwidth on the exact path most likely to hit it (PDF/PPTX decks).
**Fix:** Check `uploadFile.size > 20_000_000` before upload and surface a clear message ("File too
large — max 20 MB"); map the 413 response to a human message rather than echoing the status code.

## Info

### IN-01: Unused `import pytest` in both test files will fail the repo's own ruff `F` lint gate

**File:** `services/ai/tests/test_file_extract.py:13`, `services/ai/tests/test_input_wrap.py:13`
**Issue:** Both files import `pytest` (line 13) but the docstrings say they were "strict-xfail" stubs
whose markers were removed in the GREEN phase. There is now no `pytest.` reference or decorator in
either file (verified: no `pytest.` usage). `pyproject.toml:36` selects ruff rule set `["E","F",...]`,
and `F401` (unused import) is in `F`. `ruff check` will flag both lines.
**Fix:** Remove the `import pytest` line from both files.

### IN-02: EvidenceSnippet "Show in context" is redundant — `snippet` and `sourcePassage` are always the same value

**File:** `apps/web/app/(buyer)/extraction/page.tsx:79-82`, `apps/web/components/evidence-snippet.tsx:13-32`
**Issue:** `FieldRow` passes `snippet={evidence?.snippet}` and `sourcePassage={evidence?.snippet}` —
the identical value. The Collapsible "Show in context" therefore expands to show the same text already
shown inline. The `Evidence` contract carries `char_start`/`char_end`/`source_id`
(`packages/shared-types/index.d.ts:243-248`) which would let the UI show the surrounding source
passage with the snippet highlighted, but none of that is used. The "Show in context" affordance is
currently dead weight.
**Fix:** Either drop the `sourcePassage` prop and the Collapsible (show snippet inline only), or wire
a real surrounding-passage source so "in context" adds information. Don't ship a disclosure that
reveals nothing new.

### IN-03: `RegenButton` ignores its only prop; `initialRfq` is dead

**File:** `apps/web/app/(buyer)/rfq/regen-button.tsx:12,7-9`
**Issue:** `RegenButton({ initialRfq: _ }: RegenButtonProps)` — the prop is destructured to `_` and
never used. `handleRegen` calls `fetchRfq()` purely to confirm success then `window.location.reload()`
to re-read the committed `rfq.json` (which the Server Component renders). The prop and the
`RegenButtonProps` interface are scaffolding with no consumer.
**Fix:** Remove the unused `initialRfq` prop and the interface; `<RegenButton />` with no props.

### IN-04: `BuyerContext.setLoadedVendors` "append" semantics are easy to misuse and double-append in practice

**File:** `apps/web/contexts/BuyerContext.tsx:81-90` vs `apps/web/app/(buyer)/input/page.tsx:69-71,90,131`
**Issue:** `setLoadedVendors` appends when passed an array but replaces-via-updater when passed a
function (the comment says "APPEND-BY-DEFAULT"). The input page always calls it with the *functional*
form `(prev) => [...prev, vendor]`, which means the context's array-append branch (line 88) is never
exercised by the real caller — the append is done twice in design (once in the helper for arrays,
once by the caller's spread). This split contract is confusing and the array branch is effectively
dead for current callers. A future caller passing a plain array expecting "set" will get a surprise
append.
**Fix:** Pick one semantic. Given callers all spread manually, simplify the setter to the standard
`React.Dispatch<SetStateAction<VendorResponse[]>>` and let callers decide append vs replace, or keep
append-only and have callers pass the bare array. Don't keep both branches.

### IN-05: Trace `displayName` hard-codes filename→label mapping; new trace files render with underscored raw names

**File:** `apps/web/app/(buyer)/trace/page.tsx:48-57,64-71`
**Issue:** Both the canonical `order` array and `displayName` enumerate the six known trace files by
literal name. A newly added trace file falls through to `base.replace(/_/g, " ")` and sorts to the
end — acceptable as a fallback, but the duplicated literal list (order + displayName) must be kept in
sync by hand. Minor maintainability smell for a demo artifact.
**Fix:** Optional — derive the label from a small `{prefix: label}` map keyed on filename prefix, or
accept the fallback and drop one of the two literal lists. Low priority for a 5-day prototype.

---

_Reviewed: 2026-06-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
