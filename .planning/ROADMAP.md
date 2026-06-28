# Roadmap: Bid Desk

## Overview

Bid Desk turns messy vendor proposals into a grounded, evidence-backed comparison without inventing
anything. The build is sequenced AI-first, UI-last because 70% of the grade lives in `services/ai/`.
Schemas and the pydantic→TS contract come first (everything is typed by them and absence must be a
first-class enum state). The code-enforced grounding gate — the headline reliability mechanism — is
built and unit-tested in isolation *before* any agent exists, alongside the deliberately messy data
that makes extraction worth testing. Extraction (with evidence + four flag types + SSE streaming)
lands next; comparison follows strictly after it, consuming only code-validated `ExtractionResult[]`
and gating on comparability before any scoring. The thin buyer UI, the in-app prompt trace, and the
deploy + submission package come last. The Prompt Pack is cross-cutting: each phase contributes its
documented prompt(s) rather than being a standalone phase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Schemas, pydantic→TS contract, env LLM client, SSE proof, Prompt Pack skeleton (completed 2026-06-27)
- [x] **Phase 2: Grounding Gate & Messy Data** - Code-enforced grounding (LLM-free, unit-tested) + RFQ/vendor generation with mess specs (completed 2026-06-27)
- [x] **Phase 3: Extraction Agent** - Grounding-gated extraction with evidence, four flag types, safe structured output, SSE streaming, first trace (completed 2026-06-27)
- [ ] **Phase 4: Comparison Agent** - Comparability-before-ranking over `ExtractionResult[]` with clarification questions
- [ ] **Phase 5: Buyer UI, Trace & Submission** - Five buyer screens, in-app prompt trace, deploy, and the full submission package

## Phase Details

### Phase 1: Foundation
**Goal**: The typed contract, model access, and streaming spine that everything downstream depends on are real and proven.
**Depends on**: Nothing (first phase)
**Requirements**: PLAT-01, PLAT-02, PLAT-03, PLAT-04, PROMPT-01
**Success Criteria** (what must be TRUE):
  1. Every contract field models absence as a first-class enum (`{status: present|missing|unclear|conflicting|unsupported, value?, evidence?}`) — there is no nullable that silently collapses to a blank.
  2. Running the codegen script regenerates `packages/shared-types` from the pydantic schemas — the TS contract is mechanically derived, never hand-mirrored.
  3. A live ping confirms the org/key has `gpt-5.4` / `gpt-5.4-mini` access before anything is built on it.
  4. A minimal LangGraph stream is observable end-to-end as `{type, payload}` SSE events via `curl -N` — proving the streaming spine before any agent uses it.
  5. The Prompt Pack registry exists in `services/ai/prompts/` as first-class versioned source (skeleton, not inline strings).
**Plans**: 5 plans (3 waves)
  - [x] 01-01-PLAN.md — Monorepo scaffold (relocate Python to services/ai, pnpm+turbo workspace, apps/web shell, shared-types pkg) + dev tooling spine (ruff/pytest, prettier/eslint)
  - [x] 01-02-PLAN.md — Contract primitives (generic Field[T] envelope, evidence, 5-state flag enum, SSE event envelope) + 4 domain stubs + pydantic2ts codegen + drift-check test
  - [x] 01-03-PLAN.md — LLM tier factory + live gpt-5.4/mini access ping + FastAPI startup check + trivial LangGraph {type,payload} SSE proof (curl -N)
  - [x] 01-04-PLAN.md — Prompt Pack registry skeleton + all 7 versioned prompt stubs
  - [x] 01-GAP — Evidence-grounding invariant enforcement (CR-01/CR-02/CR-03): TDD gap-closure (commits 9610284 + 0ebabb4); 85 tests green; phase fully verified
  - [x] 01-05-PLAN.md — Framework upgrade (Next 16.2.9 + React 19.2.7, exact pins, eslint . lint) + UI substrate (Tailwind v4 CSS-first + shadcn/ui init) + one Button proof component

### Phase 2: Grounding Gate & Messy Data
**Goal**: The reliability keystone — code that disproves the model — works in isolation, and there is realistically messy data worth testing it against.
**Depends on**: Phase 1
**Requirements**: EXTRACT-04, DATA-01, DATA-02, DATA-03, DATA-04, PROMPT-04
**Success Criteria** (what must be TRUE):
  1. A fabricated evidence span is downgraded to `unsupported` by code (normalized exact → high-threshold fuzzy) and its value is suppressed — no LLM-asserted `verified`/`grounded` flag can promote a fact for display.
  2. A genuine evidence span present in the source text passes grounding and keeps its value (the gate does not over-reject).
  3. The generated RFQ reads like a real procurement event (8 line items, scope, timelines, commercials, questionnaire, compliance) — not a clean sample.
  4. ≥3 generated vendor responses are deliberately messy per an explicit per-vendor mess spec (missing/incomplete pricing, unclear tax/currency, partial scope, vague timelines, weak compliance), and a test asserts the messiness so the data is never too clean.
  5. The RFQ + ≥3 vendor responses are committed as sample data AND regenerable live in-app.
**Plans**: 4 plans (3 waves)
  - [x] 02-01-PLAN.md — Test stubs + module stubs (grounding package + test_grounding_gate.py + test_sample_fixtures.py; all RED — imports resolve, implementations pending)
  - [x] 02-02-PLAN.md — Grounding gate implementation (rapidfuzz install, two-stage normalization, exact+fuzzy match, ground_field, ground_model walker; all 9 EXTRACT-04 tests GREEN)
  - [x] 02-03-PLAN.md — Schema flesh-out (RFQ + VendorResponse real fields, codegen drift-check) + three data-generation prompts authored (rfq-gen, vendor-gen, messy-data-gen)
  - [x] 02-04-PLAN.md — Generation agents (rfq_gen.py + vendor_gen.py) + sample fixtures committed (data/) + live-regen API endpoints + PROMPT-04 docs

### Phase 3: Extraction Agent
**Goal**: Per-vendor extraction produces grounded, evidence-backed structured output that streams to the client and never fabricates.
**Depends on**: Phase 2
**Requirements**: EXTRACT-01, EXTRACT-02, EXTRACT-03, EXTRACT-05, PROMPT-03
**Success Criteria** (what must be TRUE):
  1. Extraction returns a structured per-vendor object covering scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, and risks.
  2. Every extracted fact carries an evidence snippet drawn from the vendor response, and that snippet passes the Phase 2 grounding gate before being shown.
  3. Missing / unclear / conflicting / unsupported information is flagged explicitly; the agent never fills a missing field.
  4. Structured output under strict mode treats `finish_reason: length` (truncation) and the `refusal` field as hard errors — never parsed as valid output.
  5. The extraction agent streams progress over SSE as `{type, payload}` (never buffer-and-return), and ≥1 complete prompt trace (input → prompt → model output → final displayed output) is captured.
**Plans**: 4 plans (4 waves)
  - [x] 03-01-PLAN.md — Wave 1: RED test stubs (test_extraction_agent.py, 6 functions) + docs/traces/ directory
  - [x] 03-02-PLAN.md — Wave 2: ExtractionResult schema flesh-out (LineItemExtraction, D-01..D-05, D-05 vendor_name fix) + codegen drift-check
  - [x] 03-03-PLAN.md — Wave 3: Extraction agent (StateGraph, truncation/refusal handling) + POST /extract/vendor SSE route
  - [x] 03-04-PLAN.md — Wave 4: Full extraction prompt authored + 3+ pipeline traces captured (D-12..D-15) + human checkpoint

### Phase 4: Comparison Agent
**Goal**: Vendors are compared honestly — comparability is established before any scoring, differences are surfaced without normalization, and gaps become clarification questions.
**Depends on**: Phase 3
**Requirements**: COMPARE-01, COMPARE-02, COMPARE-03, COMPARE-04, COMPARE-05
**Success Criteria** (what must be TRUE):
  1. Comparison consumes only code-validated `ExtractionResult[]` — never raw vendor text (the grounding boundary holds transitively).
  2. Non-comparable vendors are flagged as `comparable | partially | not_comparable` per dimension/line-item with reasons *before* any scoring; the agent never aggregates over a field a vendor is missing.
  3. The buyer sees a qualitative comparability/readiness signal per dimension — not a numeric leaderboard or weighted score.
  4. Vendor offers are lightly aligned to the 8 RFQ line items with originals kept visible (differences surfaced, not normalized away).
  5. Missing/unclear/conflicting information produces explicit buyer attention points and generated clarification questions.
**Plans**: 4 plans (4 waves)
Plans:
- [ ] 04-01-PLAN.md — Wave 1: RED test stubs (test_comparison_agent.py, 13 functions) + conftest_comparison.py fixture builders
- [ ] 04-02-PLAN.md — Wave 2: ComparisonResult schema flesh-out (ComparabilityVerdict, ClampReport, DimensionComparison, etc.) + codegen drift-check
- [ ] 04-03-PLAN.md — Wave 3: Comparison agent (StateGraph + verdict clamp + flag collector) + POST /compare/vendors SSE route
- [ ] 04-04-PLAN.md — Wave 4: Full comparison + clarification prompts authored + comparison trace captured + human checkpoint

### Phase 5: Buyer UI, Trace & Submission
**Goal**: A thin, buyer-first UI renders the live AI behavior across five screens, the prompt trace is visible, and the project is deployed with the full submission package.
**Depends on**: Phase 4
**Requirements**: INPUT-01, INPUT-02, INPUT-03, INPUT-04, UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, PROMPT-02, SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05
**Success Criteria** (what must be TRUE):
  1. The buyer can provide a vendor via paste (text/Markdown/JSON), file upload (PDF/Word/Excel/PPT, best-effort text), or one-click sample load — and output is generated dynamically, never hardcoded.
  2. All five screens render legibly with a buyer-first information hierarchy: risks/gaps/comparability/clarifications surfaced first, full extraction and raw evidence on drill-down.
  3. Every fact shown in Extraction Review has a visible evidence snippet, and non-comparable vendors are visibly flagged as such before any scoring on the Comparison screen.
  4. The web app (Vercel) reaches the deployed AI service (Render/Railway) via an env-configured base URL with CORS and disabled proxy buffering so SSE streams live in the demo.
  5. The submission package is complete: each Prompt Pack prompt is documented (what/why/how-it-handles-unreliable-info), plus README, 1–2 page write-up, ≤5-min demo video, and a system + AI-pipeline architecture diagram.
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 5/5 | Complete   | 2026-06-27 |
| 2. Grounding Gate & Messy Data | 4/4 | Complete   | 2026-06-27 |
| 3. Extraction Agent | 4/4 | Complete   | 2026-06-27 |
| 4. Comparison Agent | 0/4 | Not started | - |
| 5. Buyer UI, Trace & Submission | 0/TBD | Not started | - |
