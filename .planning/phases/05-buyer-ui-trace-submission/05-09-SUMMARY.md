---
phase: "05"
plan: "09"
subsystem: buyer-ui-trace-submission
tags: [e2e, playwright, uat, sse-fix, hydration-fix, grounding, evidence, deployed-verification]
dependency_graph:
  requires: ["05-08"]
  provides: ["UI-01", "UI-02", "UI-03", "UI-04", "UI-05", "UI-06", "INPUT-01", "INPUT-02", "INPUT-03", "INPUT-04"]
  affects: []
tech_stack:
  added: []
  patterns:
    - "Robust SSE client parser: split on /\\r\\n\\r\\n|\\n\\n/ (sse-starlette uses CRLF), join multi-line data:, ignore ':' keep-alive comments"
    - "SSR-safe client state: BuyerContext initializes empty, rehydrates sessionStorage in a post-mount effect, gates persistence behind a `hydrated` flag (no hydration mismatch)"
    - "Data-fetching effect owns its AbortController with cleanup + cancelled guard (correct under React Strict Mode / remount)"
    - "Playwright serial suite shares ONE browser context (beforeAll) so session state carries across tests; each vendor extracted once then reused from cache"
key_files:
  created:
    - docs/qa/phase5-UAT.md
    - docs/qa/uat-evidence/01-rfq-overview.png
    - docs/qa/uat-evidence/03-extraction-review.png
    - docs/qa/uat-evidence/05-prompt-trace.png
    - docs/qa/uat-evidence/deployed-extraction.png
  modified:
    - apps/web/lib/sse.ts
    - apps/web/contexts/BuyerContext.tsx
    - apps/web/app/(buyer)/extraction/page.tsx
    - apps/web/components/flag-badge.tsx
    - apps/web/app/(buyer)/rfq/page.tsx
    - docs/qa/phase5-playwright.spec.ts
status: executed_not_verified
requirements: ["INPUT-01", "INPUT-02", "INPUT-03", "INPUT-04", "UI-01", "UI-02", "UI-03", "UI-04", "UI-05", "UI-06", "SHIP-04"]
bugs_found_and_fixed:
  - "KEYSTONE — lib/sse.ts split SSE events on '\\n\\n' but sse-starlette delimits with '\\r\\n\\r\\n'; NO event ever parsed → extraction AND comparison results never rendered despite HTTP 200. Fixed with a robust parser."
  - "SSR hydration mismatch — BuyerContext read sessionStorage in useState initializers (server empty, client populated) → React regenerated the tree and aborted in-flight SSE streams. Fixed: SSR-safe init + post-mount rehydrate + gated persistence."
  - "SSE effect lifecycle — the extraction effect didn't own its AbortController; a separate unmount effect aborted it under Strict Mode. Fixed: effect owns controller with cleanup + cancelled guard."
  - "Missing test anchors — added data-testid='rfq-line-item' (rfq page) and data-testid='flag-badge' + data-status (FlagBadge)."
  - "Spec reliability — serial tests now share one context; extract each vendor once and reuse cache; generous timeouts for slow live inference; evidence assertion uses data-testid='evidence-snippet'."
decisions:
  - "Always UAT the PRODUCTION build (next build && next start), not next dev: dev Strict Mode + Fast Refresh make SSE/effect timing unrepresentative of Vercel"
  - "Extract each vendor once (wait for completion → caches in sessionStorage) then reuse — reliable AND minimizes paid gpt-5.4 calls"
verification:
  - "Local prod build: 7/7 Playwright tests PASS against live gpt-5.4 (RFQ → input → extraction → 2nd vendor → comparison → trace → empty-state)"
  - "pytest: 144 passed, 1 xfailed; pnpm tsc --noEmit clean; next build clean"
  - "Extraction (thorough): 39 evidence snippets, 7 gaps incl. a real conflicting price flagged not resolved (no fabrication)"
  - "Comparison: comparability matrix + 'Needs Attention' panel + 'Comparability determined in code from evidence — not a model verdict'"
  - "Deployed stack (browser): extraction rendered 60 evidence snippets + 12 absence flags + 6 gaps (docs/qa/uat-evidence/deployed-extraction.png)"
open_items:
  - "SHIP-04 demo video (≤5 min) NOT yet recorded — human task (docs/demo/demo-script.md)"
  - "Human UAT sign-off pending"
  - "Optional: run the full Playwright suite against the deployed URL (PLAYWRIGHT_BASE_URL=https://rfq-agent-web.vercel.app) — costs several gpt-5.4 calls"
metrics:
  completed_date: "2026-06-28"
---

## Plan 05-09 — Playwright E2E + UAT (handoff gate)

Ran the end-to-end buyer journey in a real browser, found and fixed the bugs that blocked it,
and produced the reference UAT. The backend AI was always correct (a direct curl returned a full
grounded extraction); the breakage was entirely client-side SSE/SSR plus a transient OpenAI
quota wall (since resolved by adding credits).

### Outcome
- **7/7 Playwright tests pass** against the local production build with live gpt-5.4.
- The same flow **verified on the deployed Vercel + Render stack** (see 05-08).
- Reference UAT committed: `docs/qa/phase5-UAT.md` + `docs/qa/uat-evidence/`.

### Not done (phase intentionally left open)
- **SHIP-04 demo video** — still a human recording task.
- Human UAT sign-off, plus the GSD code-review and security gates.
