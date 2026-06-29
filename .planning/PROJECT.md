# Bid Desk

## What This Is

Bid Desk is a prompt-driven procurement copilot that turns messy, inconsistent vendor proposals
into a grounded, evidence-backed, side-by-side comparison — so a procurement buyer running a
competitive marketing-services bid can see what each vendor offered, what is missing or risky, and
who is actually comparable, **without the AI inventing anything.**

It is a 5-day prototype for the *Generative AI Expert / Applied AI Engineer* assignment
(`docs/assignment.md`), built for submission to **Aerchain / Agillos**. The two audiences are (1)
the simulated **procurement buyer** the product serves, and (2) the **Aerchain evaluators** grading
the submission against a rubric that is 70% AI/prompts and only 10% UI.

## Core Value

**Evidence over assertion, absence made first-class:** every extracted fact carries a source
snippet from the vendor's response, and `missing` / `unclear` / `conflicting` / `unsupported` are
explicit, prominently surfaced states — never silently filled, never hidden. If everything else
fails, the AI must not hallucinate a number or a claim.

## Requirements

### Validated

All 31 v1 requirements shipped in v1.0 (2026-06-29). Full traceability in `milestones/v1.0-REQUIREMENTS.md`.

- ✓ Generate one realistic marketing-services RFQ (8 line items, scope, timelines, commercials, questionnaire, compliance) via prompt — feels like a real procurement event. — Phase 2 (DATA-01)
- ✓ Generate ≥3 deliberately messy vendor responses via prompt with real-world complexity, messiness asserted in tests. — Phase 2 (DATA-02/03)
- ✓ Grounding enforced in code (the gate): evidence spans validated against source text, model offsets recomputed, fabrications downgraded to `unsupported` — never the model's word. — Phase 2 (EXTRACT-04)
- ✓ Sample data committed AND live generation/upload in-app (dynamic, never hardcoded). — Phase 2 + 5 (DATA-04, INPUT-01..04)
- ✓ Vendor input via paste (text/Markdown/JSON) and file upload (PDF/Word/Excel/PPT), best-effort text extraction. — Phase 5 (INPUT-01/02)
- ✓ Extraction agent: per-vendor structured extraction across all 8 categories with evidence snippets and four absence flags; never fills missing info; truncation/refusal are hard errors. — Phase 3 (EXTRACT-01/02/03/05)
- ✓ Comparison agent: comparability-before-ranking over code-validated `ExtractionResult[]`, qualitative readiness signals, attention points + clarification questions; no normalization, no numeric leaderboard. — Phase 4 (COMPARE-01..05)
- ✓ Five buyer screens with buyer-first hierarchy and visible evidence. — Phase 5 (UI-01..06)
- ✓ The Prompt Pack: 7 versioned, documented prompts (what/why/how-it-handles-unreliable-info). — Phases 1–5 (PROMPT-01/02), + ≥1 trace (PROMPT-03) + a documented failure example (PROMPT-04)
- ✓ Stream agent responses over SSE (FastAPI emits, Next.js consumes) — never buffer-and-return. — Phase 1 (PLAT-04)
- ✓ Deploy: web → Vercel, AI → Render, env-configured base URL + CORS + disabled proxy buffering. — Phase 5 (SHIP-01), live 2026-06-28
- ✓ Submission package: README, 1–2 page write-up, architecture diagrams, prompt trace. — Phase 5 (SHIP-02/03/05)

### Active

(None — v1.0 shipped. Next milestone starts via `/gsd:new-milestone`.)

Carried as backlog (non-blocking): ≤5-min demo video recorded but stored outside the repo (SHIP-04 — link goes in the submission package); 2 cosmetic UI polish follow-ups (evidence drill-down, currency digit-grouping); fast-forward `main` to the shipped branch.

### Out of Scope

- Production-grade OCR / layout-aware document parsing — assignment §11 says not mandatory; best-effort text extraction is enough.
- Database, queue, or vector store — no feature in a 5-day prototype requires persistence beyond files/in-memory (CLAUDE.md §10).
- Heavy data normalization — assignment §24 explicitly warns against it; surface differences, don't normalize them away.
- Authentication / multi-user / RBAC — single-buyer prototype, not a product.
- GPT-5.5 — too expensive for this prototype (CLAUDE.md); GPT-5.4 family only.
- OpenAI Agents SDK — orchestration stays in LangChain/LangGraph.
- AWS / cloud infra beyond Vercel + Render/Railway.

## Context

- **Source of truth:** `docs/assignment.md` (the brief, graded on the §22 rubric) and `CLAUDE.md`
  (product vision, engineering principles, architecture — product-first, written for a fresh repo).
- **Rubric weighting drives priority:** Prompt quality & architecture 30% · Realistic data
  generation 20% · Extraction accuracy & reliability 20% · Product thinking in comparison 15% ·
  UI/UX prompt quality & buyer usability 10% · Demo & docs 5%. 70% of the grade lives in
  `services/ai/`.
- **Repo state:** v1.0 shipped (2026-06-29). Full pnpm+turbo monorepo built and deployed —
  `services/ai` (FastAPI + LangGraph, 7-prompt Prompt Pack, grounding gate, extraction +
  comparison agents, ~149 passing tests) and `apps/web` (Next.js 16, five buyer screens). Live on
  Vercel + Render. Local one-command Docker stack + gated CI/CD also in place (quick tasks).
- **Architecture (CLAUDE.md §5):** pnpm + turbo monorepo. `apps/web` (Next.js, App Router, thin
  client) + `services/ai` (FastAPI + LangChain/LangGraph, all AI + business logic) +
  `packages/shared-types` (TS mirror of pydantic schemas — the contract) + `data/` + `docs/`.
- **Anti-patterns to avoid (assignment §24):** hardcoded outputs, static dashboards, generic
  prompts, unrealistically clean test data, unsupported AI claims, heavy normalization, ignoring
  missing/contradictory info, misleading comparisons, UI polish without strong AI behavior.

## Constraints

- **Timeline**: 5-day prototype — favor correct + demonstrable over enterprise-grade. No
  over-engineering, no infra the prototype doesn't need.
- **Tech stack**: Frontend TypeScript (Next.js App Router); all backend + AI in Python (FastAPI +
  LangChain/LangGraph). Decided in CLAUDE.md §5.
- **LLM**: OpenAI GPT-5.4 for reasoning-heavy agents, GPT-5.4 mini for cheap tasks; never GPT-5.5.
  Model IDs env-configured — confirm exact strings before hardcoding.
- **Structured output**: pydantic schemas via OpenAI structured-output/JSON-schema path; extraction
  + comparison return validated objects, not free text.
- **Reliability**: grounding/flagging enforced in code, never delegated to an LLM-asserted "I
  didn't hallucinate." Never trust an LLM-supplied authorization/verified flag.
- **Contract discipline**: `services/ai/schemas/` (pydantic) is source of truth;
  `packages/shared-types` mirrors it. Change one → change both → list affected screens/agents.
- **Deployment split**: web → Vercel only; Python AI service → Render/Railway (long-running).
- **Git**: never include any AI tool as a commit co-author; human-authored commits only.
- **Workflow**: route non-trivial work through GSD; `.planning/` is the planning home.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hold the full Next.js + FastAPI/LangGraph monorepo (not a leaner single app) | Showcases the Python/LangGraph AI story the rubric rewards; CLAUDE.md §5 is the agreed plan | Phase 1 — scaffolded; pnpm+turbo workspace, Next.js shell, and services/ai uv env all build/lint clean; `@aerchain/shared-types` link proven end-to-end |
| Data strategy: commit pre-generated samples AND support live generation/upload | Satisfies both "generated sample data" deliverable and "dynamic processing, not hardcoded" requirement; strongest demo | ✓ Good — Phase 2 committed samples + live regen endpoints; Phase 5 added paste/upload/sample-load. (RFQ-screen regen button removed during audit — was a no-op; endpoint still live via API) |
| Deploy to Vercel + Render/Railway (not local-only) | More impressive submission; accepts the deploy/CORS/cold-start cost | Phase 5 — DONE 2026-06-28: web on Vercel (rfq-agent-web.vercel.app), AI on Render via render.yaml Blueprint (rfq-agent-ai.onrender.com); CORS via `*.vercel.app` regex; E2E verified on the live stack. Free-tier cold start (~50s) accepted; guide in docs/architecture/deployment.md |
| Support paste + PDF/Word/Excel/PPT via best-effort text extraction (no heavy OCR) | Assignment §11 permits "extracted text"; broad format coverage without over-investing in parsing | ✓ Good — Phase 5: `/extract/file-text` (pypdf/docx/openpyxl/pptx) + `/input/raw-text`; test_file_extract.py green |
| Grounding validated in code, not by the model | Hallucination control is the headline reliability requirement; LLM self-attestation is untrustworthy | Phase 1 — primitive landed: `Field[T]` absence envelope enforces all 5 grounding states (present/missing/unclear/conflicting/unsupported) via model_validator at the schema boundary; present/unclear/conflicting facts rejected without evidence (PLAT-01) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-29 after v1.0 MVP milestone — all 5 phases shipped, 31/31 requirements validated, deployed live; audit `tech_debt` (no blockers).*
