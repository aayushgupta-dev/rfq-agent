# Requirements: Bid Desk

**Defined:** 2026-06-27
**Core Value:** Evidence over assertion, absence made first-class — every shown fact carries a source snippet, and missing/unclear/conflicting/unsupported are explicit states; the AI never fabricates a number or claim.

> This is a 5-day assignment prototype graded on a fixed rubric (assignment §22). The rubric **is**
> the spec: every table-stakes requirement below is mandatory v1. Rubric weights are noted per
> category so phase planning keeps priorities honest (70% of the grade lives in `services/ai/`).

## v1 Requirements

### Platform & Contract (foundation)

- [x] **PLAT-01**: pydantic schemas define RFQ, VendorResponse, ExtractionResult, ComparisonResult, and the SSE event envelope — with absence as a first-class enum state per field (`{status: present|missing|unclear|conflicting|unsupported, value?, evidence?}`), never a nullable that collapses to a blank.
- [x] **PLAT-02**: pydantic schemas mechanically generate the `packages/shared-types` TS contract (pydantic2ts codegen) — the UI/AI contract is never hand-mirrored.
- [x] **PLAT-03**: env-configured LLM client (`gpt-5.4` reasoning-heavy / `gpt-5.4-mini` cheap tasks); GPT-5.4 API access verified by a live ping before anything is built on it.
- [x] **PLAT-04**: agent responses stream to the UI over SSE using a single `{type, payload}` envelope (FastAPI emits, Next.js consumes) — never buffer-and-return long agent work.
- [x] **FOUND-UPGRADE**: `apps/web` runs on the latest framework + agreed UI toolchain (Next.js 16 + React 19.2, Tailwind CSS v4, shadcn/ui substrate) before buyer screens land — set up once on the empty shell, not retrofitted under Phase 5 deadline. Foundation tech-debt item, not a rubric requirement.

### Prompt Pack (30%)

- [x] **PROMPT-01**: versioned prompt source in `services/ai/prompts/` for all 7 prompts (RFQ gen, vendor gen, messy-data gen, UI/UX gen, extraction, comparison, clarification/exception) — first-class source artifacts, never inline strings buried in code.
- [ ] **PROMPT-02**: each major prompt documented — what it does, why it is structured that way, and how it handles unreliable / missing / conflicting information.
- [x] **PROMPT-03**: ≥1 complete prompt trace captured and reproducible (input → prompt → model output → final structured/displayed output).
- [ ] **PROMPT-04**: ≥1 documented prompt failure example + the fix, plus prompt versioning/evaluation notes (§21 differentiator).

### Data Generation (20%)

- [ ] **DATA-01**: generate one realistic marketing-services RFQ via prompt — 8 line items, scope, timelines, item requests, commercial expectations, vendor questionnaire, compliance — feels like a real procurement event, not a clean sample.
- [ ] **DATA-02**: generate ≥3 deliberately messy vendor responses via prompt, each driven by an explicit per-vendor "mess spec" so they differ in pricing structure, completeness, scope coverage, timelines, assumptions, and clarity.
- [ ] **DATA-03**: generated vendors inject real-world complexity (missing/incomplete pricing, unclear tax/currency/assumptions/exclusions, partial scope, vague timelines, weak compliance); messiness is asserted in tests so the data is never too clean to test.
- [ ] **DATA-04**: the generated RFQ + ≥3 vendor responses are committed as sample data AND regenerable live in-app (dynamic, never hardcoded outputs).

### Vendor Input

- [ ] **INPUT-01**: buyer can provide a vendor response by pasting text, Markdown, or JSON.
- [ ] **INPUT-02**: buyer can upload a vendor file (PDF, Word, Excel, PPT); text is extracted best-effort (no production OCR, per §11).
- [ ] **INPUT-03**: buyer can load a pre-generated sample vendor in one click for an instant demo flow.
- [ ] **INPUT-04**: AI output is generated dynamically from whatever input is provided — never hardcoded to a fixed response.

### Extraction (20%)

- [x] **EXTRACT-01**: extraction agent produces a structured per-vendor extraction covering scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, and risks.
- [x] **EXTRACT-02**: every extracted fact carries an evidence snippet drawn from the vendor's response.
- [x] **EXTRACT-03**: missing / unclear / conflicting / unsupported information is flagged explicitly and prominently; the agent never fills missing information.
- [ ] **EXTRACT-04**: grounding is enforced in code — each evidence span is verified against the source text (normalized exact match → high-threshold fuzzy); facts whose evidence cannot be located are downgraded to `unsupported` and their value suppressed. No LLM-asserted `verified`/`grounded` flag is ever trusted to display a fact.
- [x] **EXTRACT-05**: structured output is handled safely under strict mode — `finish_reason: length` (truncation) and the `refusal` field are treated as hard errors, never parsed as valid output.

### Comparison (15%)

- [ ] **COMPARE-01**: comparison agent compares vendors across technical, commercial, scope, timeline, compliance, and risk — consuming only code-validated `ExtractionResult[]`, never raw vendor text.
- [ ] **COMPARE-02**: a comparability gate emits `comparable | partially | not_comparable` per dimension/line-item with reasons, *before* any scoring; the agent never aggregates over a field a vendor is missing.
- [ ] **COMPARE-03**: comparison surfaces buyer attention points and generates clarification questions for missing/unclear/conflicting information.
- [ ] **COMPARE-04**: light alignment of vendor offers to the 8 RFQ line items — surfaces differences and keeps originals visible; no heavy normalization (§21 differentiator; §24 normalization stays out).
- [ ] **COMPARE-05**: a qualitative comparability/readiness signal per dimension (not a numeric leaderboard or weighted score) (§21 differentiator).

### Buyer UI (10%)

- [ ] **UI-01**: RFQ Overview screen — scope, timelines, item requests, commercial expectations, questionnaire, compliance; makes clear what vendors must respond to.
- [ ] **UI-02**: Vendor Upload/Input screen — paste / upload / load-sample, processed dynamically.
- [ ] **UI-03**: Extraction Review screen — per-vendor extracted fields with highlighted important fields, missing/unclear/conflicting data, risks, and visible evidence snippets.
- [ ] **UI-04**: Vendor Comparison screen — side-by-side across the 6 dimensions; shows who is comparable, where they differ, and what needs further review.
- [ ] **UI-05**: Prompt Trace / Prompt Pack screen — the prompts used plus ≥1 full trace.
- [ ] **UI-06**: buyer-first information hierarchy — risks / gaps / comparability / clarifications surfaced first; full extraction and raw evidence on drill-down.

### Deploy & Submission (5%)

- [ ] **SHIP-01**: web deployed to Vercel and AI service deployed to Render/Railway, wired via env-configured base URL (CORS + disabled proxy buffering so SSE streams).
- [ ] **SHIP-02**: README — setup, run instructions, model/API requirements, env vars, sample flow, assumptions.
- [ ] **SHIP-03**: 1–2 page write-up — problem, assumptions, prompt architecture, product thinking, UI/UX decisions, extraction approach, comparison approach, limitations, what's next.
- [ ] **SHIP-04**: ≤5-min demo video covering system flow, how prompts are used, data generation, extraction, comparison, and messy/exception-case handling.
- [ ] **SHIP-05**: architecture diagram (system + AI pipeline) in `docs/` (§21 differentiator).

## v2 Requirements

Deferred — acknowledged but low-ROI for a 5-day prototype; not in the current roadmap.

### Input & Parsing

- **INPUT-05**: production-grade OCR / layout-aware parsing of scanned or image-heavy documents.

### Workflow

- **FLOW-01**: stateful human-review / approval workflow over extractions and clarifications.
- **FLOW-02**: feedback loop — buyer corrections feed back to improve extraction/comparison.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep — the §24 items would actively *hurt* the rubric.

| Feature | Reason |
|---------|--------|
| Quantitative should-cost engine | Confident numbers over messy/missing data = misleading comparison (§24); reintroduces hallucination via inference. |
| Weighted / numeric vendor scoring | A tidy score over partial, multi-currency, bundled bids misleads the buyer (§24). Use a qualitative comparability signal instead. |
| Heavy normalization | §24 explicitly warns against it; flattening bundled/multi-currency/partial bids fabricates values vendors never gave. Surface differences instead. |
| Database / queue / vector store | No feature in a 5-day prototype requires persistence beyond files/in-memory (CLAUDE.md §10). |
| Authentication / multi-user / RBAC | Single-buyer prototype, not a product. |
| GPT-5.5 | Too expensive for this prototype (CLAUDE.md); GPT-5.4 family only. |
| OpenAI Agents SDK | Orchestration stays in LangChain/LangGraph (CLAUDE.md §5). |
| AWS / cloud infra beyond Vercel + Render/Railway | Out of scope for the prototype. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | Phase 1 | Complete |
| PLAT-02 | Phase 1 | Complete |
| PLAT-03 | Phase 1 | Complete |
| PLAT-04 | Phase 1 | Complete |
| FOUND-UPGRADE | Phase 1 | Complete |
| PROMPT-01 | Phase 1 | Complete |
| EXTRACT-04 | Phase 2 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| PROMPT-04 | Phase 2 | Pending |
| EXTRACT-01 | Phase 3 | Complete |
| EXTRACT-02 | Phase 3 | Complete |
| EXTRACT-03 | Phase 3 | Complete |
| EXTRACT-05 | Phase 3 | Complete |
| PROMPT-03 | Phase 3 | Complete |
| COMPARE-01 | Phase 4 | Pending |
| COMPARE-02 | Phase 4 | Pending |
| COMPARE-03 | Phase 4 | Pending |
| COMPARE-04 | Phase 4 | Pending |
| COMPARE-05 | Phase 4 | Pending |
| INPUT-01 | Phase 5 | Pending |
| INPUT-02 | Phase 5 | Pending |
| INPUT-03 | Phase 5 | Pending |
| INPUT-04 | Phase 5 | Pending |
| UI-01 | Phase 5 | Pending |
| UI-02 | Phase 5 | Pending |
| UI-03 | Phase 5 | Pending |
| UI-04 | Phase 5 | Pending |
| UI-05 | Phase 5 | Pending |
| UI-06 | Phase 5 | Pending |
| PROMPT-02 | Phase 5 | Pending |
| SHIP-01 | Phase 5 | Pending |
| SHIP-02 | Phase 5 | Pending |
| SHIP-03 | Phase 5 | Pending |
| SHIP-04 | Phase 5 | Pending |
| SHIP-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 31 ✓
- Unmapped: 0

---
*Requirements defined: 2026-06-27*
*Last updated: 2026-06-27 after roadmap creation*
