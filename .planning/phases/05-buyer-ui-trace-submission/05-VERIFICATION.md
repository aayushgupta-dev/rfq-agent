---
phase: 05-buyer-ui-trace-submission
verified: 2026-06-28T14:30:00Z
status: human_needed
score: 4/5
overrides_applied: 0
gaps:
  - truth: "Submission package includes a ≤5-min demo video"
    status: failed
    reason: "SHIP-04 demo video has not been recorded. Only the script (docs/demo/demo-script.md) exists. No .mp4/.mov/.webm file is present in the repo."
    artifacts:
      - path: "docs/demo/"
        issue: "Contains demo-script.md only; no video file present"
    missing:
      - "Record the ≤5-min demo video per docs/demo/demo-script.md and add it to the submission package"
human_verification:
  - test: "Load a sample vendor → extraction screen → verify evidence snippets are visible and Gaps & Risks panel shows flagged fields"
    expected: "Gaps panel (data-testid=gaps-panel) visible with ≥1 non-present flag badge; at least one evidence snippet with 'Source:' text visible; no fabricated values in extraction"
    why_human: "Requires running the live app with a real gpt-5.4 extraction; SSE streaming behavior and AI grounding cannot be verified programmatically without incurring API cost"
  - test: "Load two vendors → comparison screen → verify comparability matrix and 'Comparability determined in code from evidence' note"
    expected: "comparability-matrix visible; at least one dimension shows a non-comparable badge; 'Needs Attention' panel appears before the matrix; 'Comparability determined in code from evidence — not a model verdict' text present"
    why_human: "Requires a live gpt-5.4 comparison call; verdict behavior is non-deterministic and cannot be statically verified"
  - test: "Trace screen → select a comparison trace → verify amber-highlighted clamp rows are visible"
    expected: "trace-diff card visible; at least one amber row (bg-amber-50) indicating model verdict overruled by code; 'Code overruled the model on N verdict(s)' heading present"
    why_human: "Although the trace page is static-data (no AI call needed), verifying the amber diff rows actually render correctly requires browser inspection"
  - test: "Deployed stack (https://rfq-agent-web.vercel.app): verify SSE streams incrementally — not buffer-and-dump"
    expected: "Chrome DevTools Network tab shows multiple incremental data: chunks arriving on the /extract/vendor request (not a single large response after a long wait)"
    why_human: "SSE streaming behavior on the Render+Vercel stack can only be confirmed in a real browser with DevTools; grep cannot observe network-level chunk delivery"
  - test: "OPENAI_API_KEY rotation: confirm the key exposed during Render dashboard entry has been revoked and replaced"
    expected: "Old key revoked in OpenAI platform; new key active on Render; no 401 errors on deployed extraction calls"
    why_human: "Security action required by a human (platform.openai.com key management); cannot be automated"
---

# Phase 5: Buyer UI, Trace & Submission — Verification Report

**Phase Goal:** A thin, buyer-first UI renders the live AI behavior across five screens, the prompt trace is visible, and the project is deployed with the full submission package.
**Verified:** 2026-06-28T14:30:00Z
**Status:** human_needed (4/5 automated truths verified; 1 gap — SHIP-04 demo video absent; 5 items need human confirmation)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Buyer can provide vendor via paste / file upload / one-click sample; output generated dynamically | VERIFIED | `/input/raw-text`, `/extract/file-text` endpoints in `app.py`; 3 sample cards with `data-testid="vendor-card-{thorough|cheap|fluff}"`; extraction SSE wired through `streamExtract` in `lib/api.ts`; pytest 144 passed |
| SC2 | All five screens render with buyer-first hierarchy (risks/gaps first, evidence on drill-down) | VERIFIED | All 5 screen files substantive (rfq 357 LOC, extraction 357 LOC, comparison 503 LOC, trace 199 LOC + trace-tabs.tsx, input 184 LOC); `data-testid="gaps-panel"` precedes extraction categories; Attention panel at line 53 precedes comparison matrix |
| SC3 | Every fact in Extraction Review has a visible evidence snippet; non-comparable vendors flagged before scoring | VERIFIED | `data-testid="evidence-snippet"` on EvidenceSnippet component; `data-testid="comparability-matrix"` and exact text "Comparability determined in code from evidence — not a model verdict" in comparison page; comparison clamp enforced in `agents/comparison.py` |
| SC4 | Web (Vercel) reaches deployed AI service (Render) via env-configured URL; CORS and SSE streaming work | VERIFIED | Both services live (rfq-agent-web.vercel.app, rfq-agent-ai.onrender.com documented in README + deployment.md); `allow_origin_regex=r"https://.*\.vercel\.app"` covers production URL; `X-Accel-Buffering: no` set on both SSE endpoints at lines 344, 367 in app.py; deployed stack manually verified (docs/qa/uat-evidence/deployed-extraction.png — 60 evidence snippets, 12 absence flags) |
| SC5 | Submission package: prompt docs, README, write-up, demo video, system+pipeline diagram | FAILED | All items present EXCEPT demo video — SHIP-04 gap (see below) |

**Score:** 4/5 truths verified

---

### Deferred Items

None — all phase-5 gaps are either verified or require current-phase closure.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/web/app/(buyer)/rfq/page.tsx` | RFQ Overview screen (UI-01) | VERIFIED | Substantive (116 LOC with `data-testid="rfq-line-item"`); renders committed RFQ data |
| `apps/web/app/(buyer)/input/page.tsx` | Vendor Upload/Input screen (UI-02, INPUT-01..04) | VERIFIED | 184 LOC; 3 sample cards with correct testids; paste + file upload wired |
| `apps/web/app/(buyer)/extraction/page.tsx` | Extraction Review screen (UI-03, UI-06) | VERIFIED | 357 LOC; gaps-panel, extraction-result, evidence-snippet testids; FlagBadge with data-status; empty state at line 300 |
| `apps/web/app/(buyer)/comparison/page.tsx` | Vendor Comparison screen (UI-04) | VERIFIED | 503 LOC; comparability-matrix testid; "Needs Attention" panel; 6-dimension rendering; "Comparability determined in code from evidence" |
| `apps/web/app/(buyer)/trace/page.tsx` | Prompt Trace screen (UI-05) | VERIFIED | 199 LOC + trace-tabs.tsx; `data-testid="trace-diff"` present in trace-tabs; "Code overruled the model" text; bg-amber-50 for overridden rows; Prompt Pack list section |
| `services/ai/api/app.py` | CORS + `/extract/file-text` + `/input/raw-text` + X-Accel-Buffering | VERIFIED | CORSMiddleware at line 83; `allow_origin_regex` at line 85; `/extract/file-text` at line 142; `/input/raw-text` at line 161; X-Accel-Buffering at lines 344, 367 |
| `services/ai/prompts/ui-ux-gen.v1.md` | Full ui-ux-gen prompt (256 LOC) | VERIFIED | Contains "buyer screens"; substantive (256 lines) |
| `docs/traces/ui-ux-gen-run.md` | Live run artifact for ui-ux-gen | VERIFIED | 19,006 bytes; dated 2026-06-28; non-empty run output |
| `docs/prompts/rfq-gen-doc.md` | PROMPT-02 doc for rfq-gen | VERIFIED | Contains "## What It Does", "## Why It Is", "## How It Handles" (3 required sections) |
| `docs/prompts/comparison-doc.md` | PROMPT-02 doc for comparison | VERIFIED | 3 required sections present |
| `docs/prompts/extraction-prompt-doc.md` | PROMPT-02 doc for extraction | VERIFIED | 3 required sections; 97 lines |
| `docs/prompts/prompt-04-failure-example.md` | PROMPT-04 failure example | VERIFIED | File exists with "failure" content per 05-05-SUMMARY |
| `README.md` | SHIP-02: setup, run, env vars, sample flow (OPENAI_API_KEY, pnpm dev) | VERIFIED | Has "OPENAI_API_KEY", "pnpm dev", "MODEL_REASONING", "NEXT_PUBLIC_AI_BASE_URL", live demo URLs |
| `docs/write-up.md` | SHIP-03: 1–2 page write-up | VERIFIED | 1,686 words; contains "prompt architecture" section |
| `docs/demo/demo-script.md` | SHIP-04 storyboard (precondition for demo video) | VERIFIED | Script exists with "code disproves" arc (3 matches); behavioral narration |
| `docs/demo/` video file | SHIP-04: ≤5-min demo video | MISSING | No .mp4/.mov/.webm present — only demo-script.md |
| `docs/architecture/system-diagram.md` | SHIP-05 system diagram (Mermaid) | VERIFIED | 1 mermaid block present |
| `docs/architecture/ai-pipeline-diagram.md` | SHIP-05 AI pipeline diagram (Mermaid) | VERIFIED | 1 mermaid block present |
| `render.yaml` | Render Blueprint (SHIP-01) | VERIFIED | File exists; rfq-agent-ai service defined; uv build + uvicorn start |
| `docs/qa/phase5-playwright.spec.ts` | Playwright E2E spec (7 tests, serial) | VERIFIED | `--list` shows 7 tests; `describe.serial` present; 23 `data-testid` locators; 0 skip/fixme markers |
| `services/ai/tests/test_file_extract.py` | File extract unit tests (GREEN) | VERIFIED | No `@pytest.mark.xfail` decorators; pytest 144 passed confirms these pass |
| `services/ai/tests/test_input_wrap.py` | Raw text wrap unit test (GREEN) | VERIFIED | No `@pytest.mark.xfail` decorators; pytest 144 passed |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `apps/web/app/(buyer)/extraction/page.tsx` | `services/ai/api/app.py /extract/vendor` | `streamExtract` in `lib/api.ts` | WIRED | Import at line 6; called at line 256 in a for-await loop |
| `apps/web/app/(buyer)/comparison/page.tsx` | `services/ai/api/app.py /compare/vendors` | `streamCompare` in `lib/api.ts` | WIRED | `streamCompare` exported from `lib/api.ts` line 17; imported and called in comparison page |
| `apps/web/app/(buyer)/trace/page.tsx` | `apps/web/public/traces/*.json` | `/api/traces/[name]` Route Handler | WIRED | trace-tabs.tsx fetches trace data; Route Handler from 05-04 serves public/traces/ |
| `services/ai/api/app.py` | `services/ai/schemas/domain.py` | `VendorResponse` model import | WIRED | `from schemas.domain import.*VendorResponse` confirmed in grep |
| `apps/web` (Vercel) | `services/ai` (Render) | `NEXT_PUBLIC_AI_BASE_URL` env var | WIRED | `process.env.NEXT_PUBLIC_AI_BASE_URL ?? "http://localhost:8000"` in lib/api.ts; Vercel env var set to https://rfq-agent-ai.onrender.com |
| `CORSMiddleware` | Vercel origin | `allow_origin_regex` | WIRED | `r"https://.*\.vercel\.app"` covers rfq-agent-web.vercel.app; CORS OPTIONS verified on deployed stack (05-08 SUMMARY) |
| `POST /extract/file-text` | `_extract_text` dispatcher | suffix routing | WIRED | `_extract_text(content, suffix)` called at line 157 of app.py |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `extraction/page.tsx` | `result` (ExtractionResult) | `streamExtract` → `POST /extract/vendor` → LangGraph extraction agent → GPT-5.4 | Yes (live SSE, 144 tests passing, 39 evidence snippets on Thorough vendor documented) | FLOWING |
| `comparison/page.tsx` | `comparison` (ComparisonResult) | `streamCompare` → `POST /compare/vendors` → LangGraph comparison agent | Yes (live, documented 6 attention points) | FLOWING |
| `trace/page.tsx` | trace JSON | static files in `public/traces/` via `/api/traces/[name]` Route Handler | Yes (6 JSON files present) | FLOWING |
| `rfq/page.tsx` | RFQ data | `fetchRfq` → `GET /data/rfq` → RFQ gen agent | Yes (live regeneration via GPT-5.4) | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Python test suite | `cd services/ai && uv run pytest -q` | 144 passed, 1 xfailed, 2 warnings in 6.51s | PASS |
| TypeScript check | `cd apps/web && pnpm tsc --noEmit` | Exit 0, no errors | PASS |
| Playwright spec lists 7 tests | `npx playwright test docs/qa/phase5-playwright.spec.ts --list` | 7 tests listed, serial describe | PASS |
| CORS allow_origin_regex present | `grep allow_origin_regex services/ai/api/app.py` | `r"https://.*\.vercel\.app"` at line 85 | PASS |
| X-Accel-Buffering headers | `grep -c "X-Accel-Buffering" services/ai/api/app.py` | 2 (both SSE endpoints) | PASS |
| Playwright 7/7 against prod build | documented in 05-09-SUMMARY.md | 7/7 PASS with live gpt-5.4 (2026-06-28) | PASS (not re-run — would cost gpt-5.4 calls) |

---

### Probe Execution

No probe scripts found at `scripts/*/tests/probe-*.sh`. Phase plans do not declare probe-based verification. Skipped.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INPUT-01 | 05-01, 05-02, 05-04, 05-09 | Buyer can paste text/Markdown/JSON | SATISFIED | `/input/raw-text` endpoint + input page textarea; test_input_wrap.py GREEN |
| INPUT-02 | 05-01, 05-02, 05-04 | Buyer can upload file (PDF/Word/Excel/PPT) | SATISFIED | `/extract/file-text` endpoint with pypdf/docx/openpyxl/pptx; test_file_extract.py 5 tests GREEN |
| INPUT-03 | 05-04, 05-09 | One-click sample vendor load | SATISFIED | 3 sample cards with `data-testid="vendor-card-{thorough|cheap|fluff}"` in input page |
| INPUT-04 | 05-02, 05-06, 05-09 | AI output generated dynamically, never hardcoded | SATISFIED | Extraction and comparison via live SSE to gpt-5.4 agents; no hardcoded outputs |
| UI-01 | 05-03, 05-04, 05-09 | RFQ Overview screen | SATISFIED | `apps/web/app/(buyer)/rfq/page.tsx` substantive; `data-testid="rfq-line-item"`; 8 items rendered |
| UI-02 | 05-03, 05-04 | Vendor Upload/Input screen | SATISFIED | `apps/web/app/(buyer)/input/page.tsx` with paste/upload/sample |
| UI-03 | 05-03, 05-06 | Extraction Review with evidence and absence flags | SATISFIED | 357 LOC; gaps-panel, extraction-result, evidence-snippet, flag-badge with data-status all present |
| UI-04 | 05-03, 05-06 | Vendor Comparison side-by-side | SATISFIED | 503 LOC; comparability-matrix; Attention panel; 6 dimensions |
| UI-05 | 05-07 | Prompt Trace / Prompt Pack screen | SATISFIED | trace page with trace-tabs.tsx; data-testid="trace-diff"; "Code overruled the model"; Prompt Pack list |
| UI-06 | 05-04, 05-06, 05-09 | Buyer-first information hierarchy | SATISFIED | Gaps panel before extraction categories; Attention panel before matrix; empty state explicit |
| PROMPT-02 | 05-05 | Each major prompt documented (what/why/failure handling) | SATISFIED | 7 docs in `docs/prompts/` each with "## What It Does", "## Why It Is Structured This Way", "## How It Handles" sections |
| SHIP-01 | 05-08 | Web on Vercel + AI on Render, wired via env URL, CORS, SSE | SATISFIED | Both live (rfq-agent-web.vercel.app, rfq-agent-ai.onrender.com); allow_origin_regex covers Vercel; X-Accel-Buffering in code |
| SHIP-02 | 05-07 | README with setup, run, env vars, sample flow, assumptions | SATISFIED | README has OPENAI_API_KEY, pnpm dev, MODEL_REASONING, NEXT_PUBLIC_AI_BASE_URL, live demo URLs |
| SHIP-03 | 05-07 | 1–2 page write-up | SATISFIED | docs/write-up.md 1,686 words; has "Prompt Architecture" section |
| SHIP-04 | 05-07 | ≤5-min demo video | FAILED | Only docs/demo/demo-script.md exists; no video file recorded |
| SHIP-05 | 05-07 | Architecture diagram (system + AI pipeline) | SATISFIED | docs/architecture/system-diagram.md and ai-pipeline-diagram.md both contain mermaid blocks |

**Coverage note:** REQUIREMENTS.md traceability table still shows UI-03/04/05 as "Pending" — this reflects the file not having been updated after execution, not the actual implementation state. The screens are verified SATISFIED above. This is a docs-only staleness, not a functional gap.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `services/ai/agents/vendor_gen.py` | 105–106 | `"TBD"` string literal | INFO | Intentional: instructs the vendor-gen LLM to write "TBD" in the vendor response text to simulate real-world messiness. Not a code debt marker. |
| `services/ai/prompts/extraction.v1.md` | 113 | `"TBD"` | INFO | Intentional: example text in prompt showing how to handle conditional pricing. Not a debt marker. |
| `docs/demo/demo-script.md` | 60 | `'TBD'` | INFO | Intentional: demo narration quoting the vendor's "TBD" value. Not a debt marker. |
| `services/ai/tests/test_file_extract.py` | 4–5 | References to xfail in docstring comment | INFO | Legacy comment explaining the pre-execution RED state; actual `@pytest.mark.xfail` decorators have been removed. Tests are GREEN. |

No `FIXME` or `XXX` markers found anywhere in phase-5 modified files. No unreferenced debt markers. No stub patterns in buyer screens (no `return null`, no placeholder divs, no empty handlers in production paths).

**API key security note:** 05-08-SUMMARY documents that `OPENAI_API_KEY` was briefly exposed in plaintext during Render dashboard entry. Key rotation is flagged as an open security item requiring human action before submission.

---

### Human Verification Required

#### 1. Live extraction: evidence snippets and absence flags

**Test:** Run the app (`next build && next start` + uvicorn), load the Thorough sample vendor from /input, navigate to /extraction, wait for SSE completion.
**Expected:** Gaps & Risks panel shows ≥1 non-present flag badge; ≥1 evidence snippet with visible "Source:" text; no fabricated values (e.g. the conflicting TVC Production price is flagged `conflicting`, not silently resolved).
**Why human:** Requires live gpt-5.4 extraction call (API cost); SSE streaming behavior and AI grounding assertions cannot be verified by grep.

#### 2. Live comparison: comparability matrix and buyer-first framing

**Test:** Load two vendors, navigate to /comparison, run comparison.
**Expected:** "Needs Attention" panel appears before the comparability matrix; matrix shows at least one `not_comparable` or `partially` badge; "Comparability determined in code from evidence — not a model verdict" note visible.
**Why human:** Requires live gpt-5.4 comparison call; verdict non-determinism means static assertions are unreliable.

#### 3. Trace screen: amber clamp-diff rows visible in browser

**Test:** Navigate to /trace → select comparison_trace_1 tab → verify amber-highlighted rows.
**Expected:** `data-testid="trace-diff"` card visible; ≥1 amber row indicating model verdict overruled; "Code overruled the model on N verdict(s)" heading matches actual count.
**Why human:** Although trace page uses static JSON (no AI call), rendering of amber highlights requires browser inspection; server-component + client-tab-switch interaction is not testable by grep.

#### 4. Deployed SSE streaming verification

**Test:** Open https://rfq-agent-web.vercel.app in Chrome with DevTools → Network tab open, load a sample vendor, navigate to /extraction.
**Expected:** /extract/vendor request shows `event-stream` content type with multiple incremental `data:` chunks arriving progressively (not one large response after a long pause); `X-Accel-Buffering: no` visible in response headers.
**Why human:** Network-level SSE chunk delivery can only be confirmed in a real browser; grep on code proves the header is set but not that Render's proxy respects it under real load.

#### 5. OPENAI_API_KEY rotation (security gate)

**Test:** Verify the OPENAI_API_KEY exposed during Render dashboard entry (flagged in 05-08-SUMMARY open_items) has been revoked at platform.openai.com and replaced with a new key on the Render service.
**Expected:** Old key shows as "Revoked" in OpenAI platform key list; new key active; deployed extraction call succeeds with new key.
**Why human:** Requires access to platform.openai.com and Render dashboard; cannot be automated.

---

### Gaps Summary

**One gap blocking SC5:**

**SHIP-04 (demo video)** — The `docs/demo/demo-script.md` storyboard is authored and complete, but no video file has been recorded. The REQUIREMENTS.md and ROADMAP.md both list SHIP-04 as a hard deliverable for the submission package. This was explicitly acknowledged as a pending human task in 05-09-SUMMARY.md (`open_items: ["SHIP-04 demo video (≤5 min) NOT yet recorded — human task"`). No video file (`.mp4`, `.mov`, `.webm`) exists anywhere under `docs/`.

**Action required:** Record the demo following `docs/demo/demo-script.md`. The pre-demo checklist (warm Render instance, pre-load comparison_trace_1 for known amber rows, Fluff vendor first) is documented. Target ≤5 minutes covering: RFQ overview → messy vendor → extraction with gaps/evidence → comparison with comparability signal → trace with code-disproves-model moment → Prompt Pack list.

**No other gaps.** All other requirements are satisfied in the codebase. The REQUIREMENTS.md traceability table still marks UI-03/04/05 and SHIP-01..05 as "Pending" — this is stale documentation, not a functional gap.

---

_Verified: 2026-06-28T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
