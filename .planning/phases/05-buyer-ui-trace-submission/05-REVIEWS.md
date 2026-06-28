---
phase: 5
reviewers: [codex, ollama-minimax-2.5-cloud, claude-opus-critic]
reviewed_at: 2026-06-28
plans_reviewed: [05-01, 05-02, 05-03, 05-04, 05-05, 05-06, 05-07, 05-08, 05-09]
---

# Cross-AI Plan Review — Phase 5 (Buyer UI, Trace & Submission)

Three independent reviewers: **Codex** (codex-cli 0.140.0), **Ollama MiniMax 2.5 Cloud** (`minimax-m2.5:cloud`), and a **Claude Opus adversarial critic** (subagent, grounded against the live Phase 1–4 codebase). Each received the same prompt (PROJECT context, roadmap, requirements, CONTEXT, RESEARCH, UI-SPEC, all 9 PLAN.md files).

---

## Codex Review

**Summary**

The plan set is directionally strong and well aligned to the assignment: it keeps AI/business logic server-side, prioritizes evidence/absence/comparability in the UI, covers prompt docs and submission artifacts, and explicitly plans deployment + UAT. The biggest risks are not product intent but execution correctness: several frontend plans assume schema/event shapes that may not match the generated TS types, some tests are scaffolded in ways that can pass without proving behavior, and deploy/CORS/SSE buffering details are shaky enough to threaten the live demo.

**Strengths**

- Strong rubric alignment: evidence snippets, gaps, non-comparability, Prompt Pack, traces, docs, demo script all map directly to grading criteria.
- Good thin-client boundary: Next.js consumes FastAPI/SSE and does not introduce AI SDKs or client-side “grounding” decisions.
- Buyer-first UI priorities are clear: gaps/risks first, matrix-first comparison, trace as reliability proof.
- Submission completeness is explicitly planned: README, write-up, diagrams, prompt docs, PROMPT-04 failure example, demo script/video.
- Good use of sample-load hero path while still preserving dynamic extraction/comparison.
- Session cache is appropriate for the prototype and protects the demo from accidental reruns.

**Concerns**

- **HIGH:** Plan 05-03/05-04/05-06 likely underestimates schema mismatch risk. The plans assume fields like `rfq.client_name`, `response_deadline`, `ExtractionResult.scope_summary`, `pricing_structure`, `total_price`, `ComparisonResult.vendor_readiness`, etc. If `packages/shared-types/index.d.ts` differs even slightly, the UI work will churn late. This is a blocker because UI rendering depends on exact generated schemas.

- **HIGH:** Plan 05-06 Comparison flow may not produce a meaningful comparison. The input plan’s sample-load path sets `loadedVendors([selectedVendor])`, replacing prior vendors. But comparison needs multiple vendors to demonstrate non-comparability. Plan 05-09 says load more vendors later, but unless `setLoadedVendors` appends or the UI supports multi-select/load-all, the demo can end up with one vendor only.

- **HIGH:** Plan 05-02 CORS config is probably wrong for Vercel previews. FastAPI `allow_origins=["https://*.vercel.app"]` does not generally treat `*` as a subdomain glob; it needs `allow_origin_regex` or exact origins. This can break deployed browser calls and SSE.

- **HIGH:** Plan 05-08 treats `X_ACCEL_BUFFERING=no` as a Render env var, but SSE buffering is usually controlled by an HTTP response header (`X-Accel-Buffering: no`) emitted on streaming responses. The plan only adds the header later “belt-and-suspenders”; make it required before deploy.

- **HIGH:** Plan 05-01’s “RED” tests are skipped/xfail, so they do not enforce TDD or fail when implementation is absent. This creates false confidence. Skipped tests also make later “GREEN” ambiguous unless the implementation plan explicitly removes all skips.

- **HIGH:** Playwright spec design in 05-01 is state-fragile. Separate tests won’t reliably share loaded vendors/session state. Tests that navigate directly to `/extraction` or `/comparison` may hit empty states instead of validating live behavior unless each test seeds its own state or uses `test.describe.serial`.

- **MEDIUM:** Plan 05-04 copies `data/` and `docs/traces/` into `apps/web/public/`, creating drift. If sample data/traces change after the copy, the app can render stale artifacts. A script or build step should own this copy.

- **MEDIUM:** Plan 05-04’s RFQ “Regenerate RFQ” design is underspecified. A client island calling `fetchRfq()` cannot update a server-rendered imported JSON parent just by `router.refresh()` unless the regenerated RFQ is stored in client state or served by a route whose data changes. As written, it may call the API but keep showing committed JSON.

- **MEDIUM:** Plan 05-06 says every extracted field shows evidence, but missing/unsupported fields may legitimately lack evidence. The UI must show “No verified source” or equivalent, not force `EvidenceSnippet(undefined)` or imply evidence exists.

- **MEDIUM:** Plan 05-06 says “No sort/rank/score logic” and checks `grep -c "sort|rank|score" returns 0`, but the required copy includes “Not a ranking or score”. That acceptance criterion will fail.

- **MEDIUM:** Plan 05-05 live `ui-ux-gen` run depends on OpenAI access and a guessed prompt registry return shape (`prompt['system']`, `prompt['user_template']`). If the local prompt loader API differs, this plan can stall. It needs a fallback using the existing prompt invocation pattern.

- **MEDIUM:** Plan 05-02 file-size guard checks `len(content)` after `await file.read()`, so it does not actually prevent memory pressure from large uploads. Prototype risk is moderate, but the threat model overclaims mitigation.

- **LOW:** Plan 05-02 dependency versions are hard-pinned to future/current exact floors from research. Fine, but if `uv sync --frozen` is required on Render, adding deps means the lockfile must be updated and committed.

- **LOW:** The docs plan is comprehensive but risks spending too much time on prose before the core UI is verified. The grading favors AI reliability; docs should not crowd out local E2E fixes.

**Suggestions**

- Add a Wave 1 schema audit task before UI implementation: inspect `packages/shared-types/index.d.ts`, `data/rfq.json`, one extraction trace, and one comparison trace; produce a field map used by all UI screens.

- Change sample loading to append by default and add a “Load all sample vendors” button. This directly supports the demo and comparison screen.

- Replace FastAPI Vercel wildcard CORS with either exact origins from env or `allow_origin_regex=r"https://.*\.vercel\.app"` plus localhost.

- Add `X-Accel-Buffering: no` headers directly in the existing SSE response constructors in Plan 05-02 or 05-08, not as an optional deploy fix.

- Make Wave 0 endpoint tests real failures initially, not skips, or mark them strict `xfail` and require 05-02 to remove all xfail/skip markers.

- Rewrite Playwright tests as serial or make each test independently seed state through UI actions. Add `data-testid`s during implementation, not only during failure repair.

- For static data/traces, add `scripts/sync-public-assets` or a package script so Vercel builds cannot drift from source files.

- Make RFQ regeneration client-state based: initial committed RFQ in state, button replaces state with `GET /data/rfq` result.

- In extraction UI, render absent evidence explicitly: `Source: No verified source available` for missing/unsupported fields.

- Fix brittle grep criteria, especially the comparison “score/rank” check.

**Risk Assessment**

Overall risk: **MEDIUM-HIGH**. The strategy is sound and covers the phase goal, but several details can break the final demo: schema assumptions, multi-vendor state, CORS/SSE deployment behavior, and fragile E2E tests. Addressing those before Wave 3 would reduce the risk to medium and make the plan much more likely to produce a strong submission.

---

## Ollama MiniMax 2.5 Cloud Review

# Phase 5 Plan Review — Bid Desk

## Summary

This Phase 5 plan set builds the buyer-facing UI (5 screens), wires it to the existing AI pipeline via SSE, deploys the stack to Vercel + Render, and produces the complete submission package. The architecture is sound: thin Next.js client consuming server-side AI via streaming SSE, no AI logic in the browser. The plan correctly prioritizes the "code disproves model" proof in the Trace screen as the rubric-differentiating demo arc. Execution risk is moderate—the 9-plan scope is aggressive for a 5-day window, but the foundation (Phases 1–4) is complete and the plan breaks work into correct wave dependencies.

---

## Strengths

1. **SSE buffer-handling correctness**: The `lib/sse.ts` implementation (buf accumulation across read() calls) correctly avoids the Pitfall 1 failure mode (partial JSON from chunked SSE).
2. **Grounding enforcement is server-side**: The UI renders grounded ExtractionResult from SSE `result` events—no re-grounding or client-side fact-decision, which is the correct trust boundary.
3. **Evidence-first UI design**: D-07/D-08 mandate inline evidence snippets directly under each field value, with the "Source:" label always visible—a direct rendering of the reliability claim.
4. **Comparability-before-ranking enforcement**: The Comparison screen renders the matrix (with clamped verdicts) before any narrative, and D-13 explicitly prohibits sort/rank logic—this is the Phase 4 D-07 guardrail made visible.
5. **Prompt docs structure reuse**: Plan 05-05 correctly copies the extraction-prompt-doc.md structure for all 6 remaining prompts, ensuring consistency.
6. **Demo arc is rubric-driven**: D-19 ties the demo storyline directly to the reliability rubric (messy vendor → gaps → non-comparable → code-disproves-model trace).

---

## Concerns

**HIGH: Plan 05-01 Task 1 test count mismatch**
- The task creates `test_pdf_returns_text_and_chars`, `test_docx_returns_text`, `test_xlsx_returns_text`, `test_pptx_returns_text`, and `test_weak_extraction_not_an_error` (5 tests), but Plan 05-02 acceptance criteria checks for ≥6 tests.
- **Impact**: Test will fail at verification step.
- **Fix**: Add one more test case (e.g., `test_unsupported_format_returns_empty`) or rename a method if counting is off-by-one.

**HIGH: Missing explicit weak-extraction test in 05-02**
- Plan 05-01 creates `test_weak_extraction_not_an_error` but Plan 05-02 implementation verification doesn't assert the chars < 200 threshold is handled.
- **Impact**: The D-05 "weak-extraction Alert" requirement won't be validated.
- **Fix**: Add explicit assertion in the green test (not just that it returns 200) that `response.json()["chars"] < 200` is possible.

**MEDIUM: Tooltip component missing from shadcn add in 05-03**
- Plan 05-03 Task 1 lists 12 components to add but doesn't include Tooltip, which Plan 05-06 Task 2 uses for matrix cell reasons (D-11).
- **Impact**: Build failure when comparison/page.tsx imports Tooltip.
- **Fix**: Add `tooltip` to the shadcn add command in Task 1.

**MEDIUM: Playwright test may assert wrong text for "Source:" label**
- Plan 05-01 creates `test('Extraction Review — gaps panel visible with evidence (D-07, D-08, UI-06)')` asserting "Source:" text, but EvidenceSnippet renders `<span className="font-semibold">Source:</span>`—Playwright's `getByText` may not match the `<span>` wrapper.
- **Impact**: Test fails at runtime (not caught by --list).
- **Fix**: Use `page.getByRole("text", { name: /Source:/i })` or inspect the actual DOM in a debug run.

**LOW: Duplicate trace_vendor_cheap in trace tab list**
- Plan 05-07 mentions "6 unique names" but the list includes "trace_vendor_thorough, trace_vendor_cheap, trace_vendor_fluff, trace_adversarial_fixture" + 2 comparison traces = 6, not 7. This is fine, but the comment "not 7" suggests confusion. Minor.

**LOW: No timeout/infinite-stream handling in SSE**
- The UI handles error events but Plan 05-06 doesn't guard against an SSE stream that hangs. If the model never sends `done`, the UI shows Progress forever.
- **Impact**: Demo fails if AI service hangs mid-stream.
- **Fix**: Add a client-side AbortController with a timeout (e.g., 2 min) that shows an explicit error after timeout.

---

## Suggestions

1. **Clarify test count in 05-01**: Change acceptance criteria to `≥5` tests or add a sixth test case (e.g., `test_pdf_empty_file_returns_zero_chars`).

2. **Add Tooltip to shadcn add command** in 05-03 Task 1:
   ```bash
   npx shadcn@latest add badge card tabs separator textarea input progress skeleton alert tooltip collapsible scroll-area
   ```

3. **Verify EvidenceSnippet DOM matches Playwright assertion** before Task 1 in 05-09 runs—use a debug headed run to inspect exact HTML.

4. **Add SSE timeout guard** in extraction/page.tsx and comparison/page.tsx:
   ```typescript
   const controller = new AbortController();
   const timeout = setTimeout(() => controller.abort(), 120000);
   // ... streamSSE(..., controller.signal)
   // on abort: setError("Request timed out after 2 minutes")
   ```

5. **Pre-warm Render instance explicitly in demo script** (not just Task 2 in 05-08)—the script should start with `curl https://[render-url]/data/rfq` as the first step to guarantee no cold-start delay at the most visible moment.

---

## Risk Assessment

**MEDIUM** — Overall risk is medium, with the following breakdown:

| Risk | Likelihood | Severity | Mitigation Status |
|------|------------|----------|-------------------|
| Test count mismatch (05-01 → 05-02) | HIGH | MEDIUM | Not yet mitigated |
| Missing Tooltip component import | HIGH | HIGH | Not yet mitigated |
| Playwright DOM assertion mismatch | MEDIUM | MEDIUM | Not yet mitigated |
| SSE timeout/hang | MEDIUM | HIGH | Not yet mitigated |
| Render cold-start during demo | MEDIUM | HIGH | Partially mitigated (D-18, Task 2) |
| Scope creep (9 plans in 5 days) | HIGH | MEDIUM | Prior phases complete, reducing scope |

The phase is achievable because Phases 1–4 are complete and locked—the AI pipeline, grounding gate, and clamp logic are server-side and already tested. The UI work is thin-client rendering of pre-validated outputs. The primary execution risks are the test count mismatch, missing Tooltip component, and the SSE timeout edge case—all fixable in the first hour of execution.

**Recommendation**: Proceed with Phase 5, but address the HIGH concerns (test count, Tooltip) as pre-flight checks before Wave 1 execution. Add SSE timeout guard in Plan 05-06 Task 1 before implementing the streaming state.

---

## Claude Opus Critic Review

# Cross-AI Plan Review — Bid Desk Phase 5 (Buyer UI, Trace & Submission)

## 1. Summary

This is a strong, well-sequenced plan set: the wave structure is sound, the thin-client/grounding-on-the-server boundary is respected throughout, and the rubric-aligned deliverables (Prompt Pack docs, "code disproves model" trace, demo arc) are all present and correctly prioritized. However, the plans contain a **cluster of concrete, load-bearing API/SSE contract mismatches** between what the Phase 5 client is instructed to send/parse and what the Phase 1–4 backend actually exposes. These are not stylistic — left unfixed they will produce 422s and runtime crashes on the two AI-showcase screens that carry 35% of the grade, and they will only surface at Wave 5 (Playwright) or the live demo, which is the worst possible time. The interface blocks that the executor is told to "copy exactly" are themselves wrong, so a faithful executor will reproduce the bug. The biggest non-contract risk is that the headline reliability proof (evidence snippets, downgrade diff) depends on payload fields the client is told to access incorrectly. Fixing the contract details in the four affected plans (05-03, 05-04, 05-06, 05-07) is mandatory before execution; everything else is polish.

## 2. Strengths

- **Architecture discipline is real, not claimed.** No AI SDK leaks into `apps/web`; the grounding gate and comparability clamp stay server-side (Phase 3/4) and the UI is explicitly told to render clamped/grounded output as-is with "no client re-computation" (05-06 T-05-06-A/B). This directly protects the AI-reliability rubric.
- **Absence-first is wired into the UI contract, not aspirational.** 05-06 mandates a Gaps & Risks panel listing every non-`present` field first, `—` for absent values, severity ordering, and `unsupported` rendered with its own badge — the §8 "never silently filled" rule is enforced in the render plan.
- **Ranking-before-comparability is structurally blocked.** 05-06 acceptance criteria include `grep -c "sort\|rank\|score" … returns 0` and stable input order (D-13) with an explicit "Data readiness, not a ranking" affordance. Good adversarial self-check.
- **SSE is consumed as a true stream.** 05-03 mandates `fetch`+`ReadableStream` with `buf` accumulation across `read()` calls and an explicit anti-pattern note against buffering — the §5/§11 "never buffer-and-return" rule is honored on both ends.
- **The trace duplicate bug was already caught.** 05-07 correctly notes the prior "7 traces with `trace_vendor_cheap` twice" was a bug and pins the canonical 6-file set; I confirmed exactly 6 trace files exist.
- **Wave 0 RED-test scaffolding and the deferred-CORS/buffering note in `app.py`** show the plan inherited and respected prior-phase decisions cleanly.

## 3. Concerns

- **HIGH — Request-body field-name mismatch will 422 the extraction screen (Plan 05-03 Task 2 + Plan 05-06).** The actual endpoint `POST /extract/vendor` takes `ExtractionRequest{vendor_response: VendorResponse, rfq: RFQ}` (confirmed `app.py:103-119`), but 05-03 instructs `api.ts` to call `streamSSE("${BASE}/extract/vendor", {vendor, rfq})` — wrong key (`vendor` vs `vendor_response`). FastAPI will reject this with a 422 before any SSE byte streams. This is the first thing the demo does after "Load Sample." It must be `{vendor_response: vendor, rfq}`.

- **HIGH — The `result` event payload is NOT a bare `ExtractionResult`; the plan tells the client to cast it as one (Plan 05-06 Task 1, line 197).** `extraction.py:225-231` emits `payload = {**grounded.model_dump(), "downgrade_report": report}` — the ExtractionResult fields are spread at the **top level alongside** an extra `downgrade_report` sibling key. The plan's interface block (05-06 lines 140-145) wrongly documents `"result" → ExtractionResult` and instructs `setExtraction(name, event.payload as ExtractionResult)`. The cast will *appear* to work (the fields are present) but: (a) the cached object now carries a stray `downgrade_report` that is re-POSTed to `/compare/vendors` — which validates `extractions: list[ExtractionResult]` and may reject the extra field depending on model config, and (b) the comparison `result` payload is, by contrast, a **bare** `ComparisonResult` (`comparison.py:896-897`). This asymmetry is undocumented in every plan and is exactly the kind of thing that passes `tsc` and fails at runtime.

- **HIGH — Status-event payload shape is wrong in the plan, breaking the progress bar (Plan 05-06 Task 1; Plan 05-03 stream-progress).** Real status events are `{"message": ..., "phase": ...}` (`extraction.py:109-114`), but the plan documents `"status" → {message: string}` and drives progress by "advance progress.value by ~20%" per event. There's no total-event count to compute a percentage from, and the `phase` field (`model` / `grounding`) — which is the *natural* progress signal — is ignored. The progress bar (D-25, a graded "stream progress" gate) will either jump arbitrarily or stall. Recommend deriving progress from the known `phase` sequence, not an invented counter.

- **HIGH — Single-vendor sample-load hero path cannot reach the Comparison screen (Plans 05-04 / 05-06).** `ComparisonRequest` enforces `_MIN_VENDORS = 2` and **422s on a single vendor** (`app.py:185,193-200`). But D-04's hero path and 05-04 Task 2 both do `setLoadedVendors([selectedVendor])` (a single vendor) and the demo arc (05-07 demo-script 00:30-01:30) loads *one* Fluff vendor first. The plans never state that Comparison requires ≥2 vendors loaded, and 05-06's empty-state only guards `Object.keys(extractions).length > 0` (i.e. ≥1), not ≥2. A buyer who loads one sample and clicks through to Comparison gets a 422 with no specific empty-state. Needs an explicit "load at least 2 vendors to compare" state and a demo-script note. The Playwright comparison test (05-01 test 4) navigates to `/comparison` without guaranteeing 2 vendors are loaded — it will flake or fail.

- **MEDIUM — The "interface" blocks instruct the executor to copy the wrong contract (systemic).** 05-03 says copy `lib/sse.ts` "verbatim" and 05-06 says follow the interface block; but those blocks encode the field-name and payload-shape errors above. Because GSD executors treat these as authoritative, the bug is *guaranteed* to be reproduced rather than caught. The fix isn't just one screen — every plan that references the extract/compare request body or the result/status payload (05-03, 05-04, 05-06) needs its interface block corrected against `app.py` and the two agent files. Recommend a single "API contract" appendix derived from the real code, referenced by all three.

- **MEDIUM — Plan 05-05 Task 1's live `ui-ux-gen` run snippet will not execute as written.** The inline Python calls `prompt['system']`, `prompt['user_template']`, and `prompt['user_template'].format(...)`, but `registry.load(id)` returns whatever the Phase 1 registry actually returns (frontmatter + body), not a dict with `system`/`user_template` keys — this is unverified and flagged only as "Claude's Discretion." If the executor runs it blindly it errors; if it improvises, the "one real run" provenance claim (the honesty hook for the 10% UI/UX deliverable) is at risk. The plan should require reading `registry.py`'s actual return contract first and adapt, and should pin the model env var (`MODEL_CHEAP`) explicitly so the run is reproducible.

- **MEDIUM — RFQ Overview is a Server Component importing `data/rfq.json` from `public/`, but the regen path and shape are inconsistent (Plan 05-04 Task 1).** The plan both `import rfqData from "../../../../public/data/rfq.json"` (build-time static) and offers a RegenButton calling `fetchRfq()` → `GET /data/rfq`. `GET /data/rfq` makes a **live OpenAI call** (`app.py:68-77`) on the demo's opening screen — D-21 explicitly wanted to *avoid* a cold-start there, yet the regen button reintroduces exactly that latency with no loading/disabled state specified. Also, the committed `data/rfq.json` shape must match the `RFQ` interface the page casts to; nothing in the plan verifies the committed fixture conforms to the current schema (it was generated in an earlier phase). A one-line assert/typecheck against the fixture would prevent a silent render gap.

- **MEDIUM — CORS preview-wildcard is an unverified assumption on the critical demo path (Plans 05-02 / 05-08; Assumption A2).** `allow_origins=["https://*.vercel.app", ...]` — Starlette's `CORSMiddleware` matches `allow_origins` by **exact string**, not glob; wildcard subdomains require `allow_origin_regex`. As written, `*.vercel.app` will match nothing, and the only reason the demo works is the exact URL added in 05-08. That's fine for production, but the plan presents the wildcard as functional (it's dead config) and a preview deploy will silently fail CORS. Either use `allow_origin_regex=r"https://.*\.vercel\.app"` or drop the wildcard and document that only the exact URL works.

- **MEDIUM — `X_ACCEL_BUFFERING=no` as a Render env var is doubly speculative (Plan 05-08, Assumption A1).** Disabling SSE buffering is controlled by the **response header** `X-Accel-Buffering: no`, not an arbitrary env var; Render does not document an env var by that name reading into nginx. The belt-and-suspenders header in 05-08 Step 1 is the *actual* mitigation and should be the **primary**, not the fallback — set the header on both SSE responses unconditionally in 05-02, so live streaming doesn't hinge on an unverified platform behavior discovered at demo time. Buffered SSE silently destroys the single most important demo beat.

- **LOW — No client-side AbortController wiring on screen unmount despite the threat register claiming it (Plan 05-06 T-05-06-C).** The threat table says "AbortController tied to component unmount," but neither 05-03's `streamSSE(url, body, signal?)` callers nor 05-06's `for await` loops are instructed to create/pass a signal or abort on unmount. A user navigating away mid-extraction leaves a dangling reader. Low impact for a single-buyer demo, but the plan claims a mitigation it doesn't implement — close the gap or drop the claim.

- **LOW — `line_items[].scope_coverage` / `pricing` sub-fields are referenced but not in the documented `LineItemExtraction` interface (Plan 05-06 line 146-154, "Category layout").** The category map routes `line_items[].scope_coverage` and `line_items[].pricing` into the scope/pricing sections. `shared-types` confirms `scope_coverage: FieldStr` exists, but `pricing` on the line item is not shown in the plan's interface block — the executor may guess. Pin the exact `LineItemExtraction` field names from `shared-types` in the plan to avoid an invented field that renders blank.

- **LOW — Demo script bakes in specific factual outcomes that the live model may not produce (Plan 05-07 demo-script; 05-09 acknowledges variance).** The script narrates "Vendor A is not_comparable on commercial," "model proposed 'partially' … clamped to 'not_comparable' because timeline.status = missing," etc. Extraction/comparison are live (D-02), so these exact verdicts can drift run-to-run. 05-09 correctly makes Playwright assert *behavioral* properties, but the demo script and the recorded video are committed artifacts — recommend the script say "find a clamped row and narrate it" rather than hard-coding a verdict that may not appear, or pre-select a trace fixture known to contain the clamp.

## 4. Suggestions

1. **Create one authoritative `05-API-CONTRACT.md`** (or a corrected interface block) generated by reading `app.py`, `agents/extraction.py:225-231`, and `agents/comparison.py:896-897`, stating verbatim: request bodies (`{vendor_response, rfq}`, `{extractions, rfq}`), the **asymmetric** result payloads (extraction = spread fields + `downgrade_report`; comparison = bare `ComparisonResult`), and status payload `{message, phase}`. Reference it from 05-03, 05-04, 05-06, 05-07. This single fix neutralizes the three HIGH contract concerns.
2. **In `api.ts`, normalize the extraction result** before caching: strip/separate `downgrade_report` so what's stored in `extractions[name]` is a clean `ExtractionResult` safe to re-POST to `/compare/vendors`. Keep `downgrade_report` only for the Extraction screen's optional display.
3. **Add a `< 2 vendors` empty state to the Comparison screen and the demo flow:** "Load at least 2 vendors to compare." Update the demo arc to load all 3 vendors before the Comparison beat, and make the Playwright comparison test seed 2 vendors first.
4. **Drive `StreamProgress` off the known `phase` sequence** (`model` → `grounding` → done for extraction; the comparison node sequence align→comparability→compare→clarify) rather than a `+20%` counter — it's both more accurate and matches what the backend actually emits.
5. **Make `X-Accel-Buffering: no` a response header set unconditionally in 05-02** on both SSE endpoints; demote the env var to a "may also help" note. Switch CORS to `allow_origin_regex` for the wildcard.
6. **In 05-05, require reading `registry.py`'s return shape first** and pin the model via the env-configured `MODEL_CHEAP`; add an assertion that the captured artifact is non-trivial (already have the `>500 chars` check — also assert it's not an error string).
7. **Add a fixture-conformance check** (Python, cheap) asserting `data/rfq.json` and `data/vendor_*.json` still validate against the current `RFQ`/`VendorResponse` schemas, run in Wave 0 or 05-04 — catches drift between committed samples and the frozen schema before the UI renders them.
8. **Specify the RegenButton loading/disabled state** in 05-04 (it triggers a live OpenAI call) so the opening screen never appears frozen.

## 5. Risk Assessment

**Overall: MEDIUM (trending HIGH if the contract issues aren't fixed pre-execution).**

The plan's *structure, sequencing, and rubric alignment are low-risk and genuinely good* — the reliability machinery, absence-first UI, and no-rank framing are all correctly specified. The risk is concentrated and specific: a cluster of API/SSE contract mismatches (request body key, asymmetric result payload, status shape, 2-vendor minimum) that are (a) confirmed against the real Phase 1–4 code, (b) embedded in the very "interface" blocks executors are told to copy, and (c) latent until Wave 5 / the live demo. Because they land on the two AI-showcase screens that carry 35% of the grade and on the demo's first interaction, an unaddressed failure here would block a strong submission even though the AI behavior underneath is correct. None of the issues are architectural or require re-planning — they are precise corrections to four plans plus one normalization helper. Fix the three HIGH contract concerns and the two MEDIUM deploy-assumption concerns (CORS regex, SSE header) before execution, and overall risk drops to LOW.

---

## Consensus Summary

All three reviewers independently rate the plan set **structurally sound and rubric-aligned** (thin-client boundary respected, grounding/absence/comparability machinery correctly specified, submission package complete) with risk concentrated in **execution-correctness details** — chiefly the **client↔backend API/SSE contract** and the **deploy path**. No reviewer recommends re-architecting; all recommend targeted corrections to a handful of plans before execution. Overall risk: **MEDIUM, trending LOW once the HIGH items below are fixed.**

### Agreed Strengths (2+ reviewers)
- Thin-client discipline is real: no AI SDK / no client-side grounding in `apps/web`; UI renders server-grounded output as-is (Codex, Ollama, Opus).
- Absence-first + evidence-first UI is wired into the render contract, not aspirational (Ollama, Opus).
- Comparability-before-ranking is structurally enforced — matrix-first, no sort/rank/score (Ollama, Opus).
- SSE consumed as a true stream via `fetch`+`ReadableStream` with buffer accumulation; "never buffer-and-return" honored (Codex, Ollama, Opus).
- Submission completeness (Prompt Pack docs, README, write-up, diagrams, "code-disproves-model" trace + demo arc) maps directly to the rubric (Codex, Ollama, Opus).

### Agreed Concerns — prioritized for the `--reviews` replan

**HIGH (block a strong submission; fix before execution):**
1. **API/SSE contract mismatches** between Phase 5 client and Phase 1–4 backend (Opus, code-grounded; Codex flags as schema-mismatch risk):
   - Request body key: `POST /extract/vendor` expects `{vendor_response, rfq}` — plans send `{vendor, rfq}` → **422**.
   - Extraction `result` event is **spread ExtractionResult fields + a sibling `downgrade_report`**, NOT a bare `ExtractionResult`; comparison `result` IS a bare `ComparisonResult`. This asymmetry is undocumented and the stray field is re-POSTed to `/compare/vendors`.
   - Status events are `{message, phase}`, not `{message}`. → **Fix: author one authoritative API-contract block (from `app.py`, `extraction.py:225-231`, `comparison.py:896-897`) referenced by 05-03/05-04/05-06/05-07; normalize the extraction result in `api.ts` before caching.**
2. **Single-vendor hero path cannot reach Comparison** — `ComparisonRequest` enforces `_MIN_VENDORS=2` and 422s on one vendor, but the sample-load hero path / demo loads a single vendor and the empty-state only guards ≥1 (Opus, Codex). → **Fix: append-by-default loading + "Load ≥2 vendors to compare" empty-state + demo loads all 3 + Playwright seeds 2.**
3. **Deploy: CORS Vercel wildcard is dead config** — Starlette matches `allow_origins` by exact string; `*.vercel.app` matches nothing without `allow_origin_regex` (Codex, Opus). → **Fix: `allow_origin_regex=r"https://.*\.vercel\.app"` + localhost.**
4. **Deploy: SSE buffering** — `X_ACCEL_BUFFERING=no` env var is speculative; the real control is the `X-Accel-Buffering: no` **response header** (Codex, Opus). → **Fix: set the header unconditionally on both SSE responses in 05-02 (primary), demote env var to a note.**
5. **Wave 0 tests are skipped, not failing**, and **test-count mismatch (05-01 produces 5, 05-02 asserts ≥6)** (Codex; Ollama). → **Fix: align the count and make RED tests fail (strict xfail/assert), with 05-02 removing all skips on GREEN.**
6. **Playwright spec is state-fragile** — separate tests don't share loaded-vendor/session state; direct navigation to `/extraction` or `/comparison` hits empty states (Codex; Ollama DOM-assertion variant). → **Fix: `test.describe.serial` or per-test UI seeding; verify the `Source:` DOM assertion against real markup; add `data-testid`s during implementation.**

**MEDIUM:**
7. **StreamProgress** should be driven by the known `phase` sequence, not an invented `+20%` counter (Opus). 
8. **Missing `tooltip`** in the 05-03 shadcn add list, used by the comparison matrix (Ollama) → build failure.
9. **Absent/unsupported fields legitimately lack evidence** — UI must render "No verified source" rather than imply evidence exists or pass `undefined` to `EvidenceSnippet` (Codex).
10. **`grep -c "sort\|rank\|score"` acceptance criterion conflicts with the required on-screen copy "Not a ranking or score"** (Codex) → criterion will fail on its own copy.
11. **`ui-ux-gen` live-run snippet guesses the registry return shape** (`prompt['system']`, `prompt['user_template']`) — read `registry.py`'s real contract first; pin `MODEL_CHEAP`; assert artifact is non-trivial and not an error string (Opus, Codex).
12. **RFQ RegenButton** can't update a server-rendered imported JSON parent and triggers a live OpenAI call on the opening screen with no loading/disabled state — make it client-state-based with explicit loading (Opus, Codex).
13. **Static `data/`/`traces/` copy into `public/` can drift** from source — own it with a sync script/build step + a fixture-conformance check against current schemas (Codex, Opus).

**LOW:**
14. **SSE timeout / AbortController** — no hang guard and the threat register claims an AbortController that isn't wired; add a timeout + abort-on-unmount or drop the claim (Ollama, Opus).
15. **Demo script hard-codes specific live-model verdicts** that may drift run-to-run — narrate "find a clamped row" or pin a known trace fixture (Opus).
16. **Pin exact `LineItemExtraction` field names** (`scope_coverage`, pricing sub-fields) from `shared-types` so the executor doesn't invent a blank-rendering field (Opus).

### Divergent / single-reviewer Views
- Opus is the only reviewer that grounded the contract claims in exact file:line references (most actionable) — treat its API-contract findings as authoritative.
- Ollama uniquely caught the concrete **test-count (5 vs ≥6)** and **missing-tooltip** build-break details.
- Codex uniquely flagged the **`score|rank` grep-vs-copy contradiction** and the **upload file-size guard checking `len(content)` after full read** (threat-model overclaim).
- No HIGH-severity disagreement: where reviewers overlap they agree on direction; differences are depth/specificity, not conflict.
