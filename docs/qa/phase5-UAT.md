# Phase 5 — End-to-End UAT (Buyer Journey)

> Reference UAT for the Bid Desk prototype. Verifies the **whole product works end to
> end** against `docs/assignment.md` — not just that code runs, but that the AI behaviour
> the rubric grades is real: evidence-backed extraction, first-class absence, comparability
> before ranking, and **no fabrication**. Re-run this before every deploy / submission.

- **Run date:** 2026-06-28
- **Mode:** production build (`next build && next start`), live `gpt-5.4` / `gpt-5.4-mini`
- **Result:** ✅ **7/7 automated E2E tests pass** + manual verification of AI grounding
- **Automated spec:** `docs/qa/phase5-playwright.spec.ts` (run command below)
- **Evidence:** `docs/qa/uat-evidence/*.png`

## How to run

```bash
# 1. AI service (terminal A)
cd services/ai && uv run uvicorn api.app:app --host 0.0.0.0 --port 8000
# 2. Web — PRODUCTION build, the deploy artifact (terminal B)
cd apps/web && pnpm build && pnpm start -p 3000
# 3. E2E (terminal C) — defaults to http://localhost:3000, or set PLAYWRIGHT_BASE_URL
npx playwright test docs/qa/phase5-playwright.spec.ts --reporter=list
# Against the deployed stack:
PLAYWRIGHT_BASE_URL=https://<vercel-url> npx playwright test docs/qa/phase5-playwright.spec.ts
```

> **Cost note:** every `/data/rfq` call **live-regenerates** the RFQ via `gpt-5.4`, and each
> extraction/comparison is a live `gpt-5.4` call. A full suite run ≈ 2 extractions + 1
> comparison + several RFQ regens. Don't loop it; one pass verifies the journey.

> **Why production, not `next dev`:** dev runs React Strict Mode (double-invokes effects)
> and Fast Refresh, which make SSE/effect timing noisy and not representative of Vercel.
> Always UAT the production build — it is what deploys.

---

## Functional checklist (80% — does the AI actually work?)

Each row is asserted by the automated spec and/or manual observation this run.

| # | Requirement | What it proves | Status |
|---|---|---|---|
| F1 | **RFQ Overview** (UI-01) renders the procurement event: 8 line items, commercial expectations, questionnaire, compliance | Buyer sees what vendors respond to | ✅ |
| F2 | **Vendor Input** (UI-02, INPUT-01..04) — 3 sample vendors + paste + file upload; output generated dynamically, never hardcoded | Real input → real pipeline | ✅ |
| F3 | **Extraction runs live** against a vendor response via SSE (`POST /extract/vendor`) | Backend AI works, not a shell | ✅ |
| F4 | **Evidence over assertion** — every extracted fact carries a source snippet (`evidence-snippet`, "Source:") | No ungrounded claims (39 snippets on the thorough vendor) | ✅ |
| F5 | **Absence is first-class** — `missing` / `unclear` / `conflicting` / `unsupported` surfaced in a Gaps & Risks panel (UI-06) | Gaps not hidden (7 issues incl. a real `conflicting` price) | ✅ |
| F6 | **No fabrication** — the conflicting TVC Production price (USD 468,500 vs 488,500) is flagged `conflicting`, not silently resolved | Reliability keystone | ✅ |
| F7 | **Comparison runs live** (`POST /compare/vendors`) from ≥2 extracted vendors | Comparison agent works | ✅ |
| F8 | **Comparability before ranking** (UI-04, D-13) — matrix shows comparable / not-comparable per dimension; "Comparability determined in code from evidence — not a model verdict" | No misleading apples-to-oranges (6 attention points) | ✅ |
| F9 | **Buyer attention first** (D-12) — "Needs Attention" panel precedes the matrix | Buyer-first hierarchy | ✅ |
| F10 | **Prompt Trace** (UI-05, D-15) — per-trace tabs; "Code overruled the model on N verdict(s)" diff visible | Code-enforced grounding is demonstrable | ✅ |
| F11 | **Explicit empty state** (D-25) — `/extraction` with no vendor shows "Select or load a vendor", never a blank screen | No silent dead-ends | ✅ |
| F12 | **SSE streams incrementally** — status events drive a live progress bar before the result (not buffer-and-dump) | Streaming UX wired correctly | ✅ |
| F13 | **Grounding enforced in code** — evidence spans validated server-side; UI renders the validated envelope as-is | Trust boundary respected | ✅ (server) |

## Wiring checklist (is it connected front-to-back?)

| # | Check | Status |
|---|---|---|
| W1 | Web → AI base URL via `NEXT_PUBLIC_AI_BASE_URL` (defaults to `http://localhost:8000`) | ✅ |
| W2 | CORS allows the web origin (`allow_origins` localhost + `allow_origin_regex` for `*.vercel.app`) | ✅ |
| W3 | SSE parsed correctly on the client (handles `\r\n\r\n` from `sse-starlette`) | ✅ (fixed this phase) |
| W4 | Session state (loaded vendors, extractions, comparison) persists across screens via `sessionStorage`, SSR-safe (no hydration mismatch) | ✅ (fixed this phase) |
| W5 | `pnpm tsc --noEmit` clean; `next build` succeeds; `uv run pytest` 144 passed | ✅ |

## UI checklist (20%)

| # | Check | Status |
|---|---|---|
| U1 | Stage rail navigation across all 5 screens | ✅ |
| U2 | Absence-first colour-coded flag badges (5 states) | ✅ |
| U3 | No hydration errors / console errors in production | ✅ |
| U4 | Responsive shell, shadcn components | ✅ (not deeply audited — functionality prioritised) |

---

## Bugs found & fixed during this UAT

1. **SSE never parsed on the client (keystone).** `lib/sse.ts` split events on `\n\n`, but
   `sse-starlette` delimits with `\r\n\r\n`. No event ever parsed → extraction/comparison
   results never rendered despite `200` responses. Fixed with a robust parser (handles both
   delimiters, multi-line `data:`, ignores `:` keep-alives).
2. **SSR hydration mismatch.** `BuyerContext` read `sessionStorage` in `useState`
   initializers → server rendered empty, client rendered stored data → React regenerated the
   tree and aborted in-flight SSE streams. Fixed: SSR-safe initial state + post-mount
   rehydrate + gated persistence.
3. **SSE effect lifecycle.** The extraction effect didn't own its `AbortController`; a
   separate unmount effect aborted it under Strict Mode. Fixed: effect owns the controller
   with cleanup + a `cancelled` guard.
4. **Test contract gaps.** Added `data-testid="rfq-line-item"` and `flag-badge` +
   `data-status`; rewrote the spec to share one browser context across serial tests, extract
   each vendor once (cache + reuse), and use generous timeouts for slow live inference.

## Known limitations / risks (carry into deploy)

- **Latency & cost:** `/data/rfq` regenerates the RFQ via `gpt-5.4` on *every* call, and
  extraction/comparison are live. A demo click-through costs several `gpt-5.4` calls and each
  screen has a real wait. Warm the service before recording; consider caching the RFQ if cost
  matters. (See PROJECT decisions D-18, D-21.)
- **Comparison latency varies** run-to-run (≈30–90s); the spec uses 180s expect timeouts.
- **UI polish** is intentionally secondary to AI behaviour per the rubric.

## Pending (human / deploy steps — not part of automated UAT)

- [ ] **05-08 deploy:** AI service → Render, web → Vercel; set `NEXT_PUBLIC_AI_BASE_URL` +
      add the exact Vercel URL to `allow_origins` in `services/ai/api/app.py`.
- [ ] **Re-run this UAT against the deployed stack** (`PLAYWRIGHT_BASE_URL=https://<vercel-url>`).
- [ ] **SHIP-04 demo video** (≤5 min) following `docs/demo/demo-script.md`.
