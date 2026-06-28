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

- ✓ Generate one realistic marketing-services RFQ (8 line items, scope, timelines, commercials, questionnaire, compliance) via prompt — feels like a real procurement event, not a clean sample. — Phase 2 (DATA-01)
- ✓ Generate ≥3 deliberately messy vendor responses via prompt — differ in pricing structure, completeness, scope, timelines, assumptions, clarity; inject real-world complexity (missing pricing, unclear tax/currency, partial scope, vague timelines, weak compliance). — Phase 2 (DATA-02/03)
- ✓ Grounding enforced in code (the gate): evidence spans validated against source text, model-supplied offsets ignored and recomputed, fabricated spans downgraded to `unsupported` — not taken on the model's word. Mechanism built + unit/functionally proven (full per-fact wiring lands with extraction/UI). — Phase 2 (EXTRACT-04)

### Active

- [ ] Commit the generated RFQ + ≥3 vendor responses as sample data AND support live generation/upload in-app (dynamic processing, never hardcoded outputs). — generation + live-regen done (Phase 2, DATA-04); in-app upload pending (Phase 5).
- [ ] Accept vendor responses via paste (text/Markdown/JSON) and file upload (PDF, Word, Excel, PPT) using best-effort text extraction — full OCR not required (assignment §11).
- [ ] Extraction agent: per-vendor structured extraction (scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, risks) with evidence snippets and missing/unclear/conflicting/unsupported flags. Never fills missing info.
- [ ] Comparison agent: side-by-side across technical, commercial, scope, timeline, compliance, risk; establishes comparability first; surfaces buyer attention points + clarification questions; never misleads.
- [ ] Five buyer screens: RFQ Overview, Vendor Upload/Input, Extraction Review (with evidence), Vendor Comparison, Prompt Trace / Prompt Pack view.
- [ ] The Prompt Pack: versioned, first-class prompt source for RFQ gen, vendor gen, messy-data gen, UI/UX gen, extraction, comparison, clarification/exception handling — each documented (what/why/how it handles unreliable info).
- [x] ≥1 complete prompt trace (input → prompt → model output → final structured/displayed output). — Prompt Trace screen + docs/traces/
- [x] Stream agent responses to the UI over SSE (FastAPI emits, Next.js consumes) — never buffer-and-return long agent work.
- [x] Deploy: web → Vercel, AI service → Render/Railway, wired via env-configured base URL. — Live 2026-06-28 (rfq-agent-web.vercel.app + rfq-agent-ai.onrender.com)
- [ ] Submission deliverables: working prototype, sample data, Prompt Pack, UI/UX output, extraction + comparison outputs with evidence/clarifications, prompt trace, ≤5-min demo video, 1–2 page write-up, README. — all present EXCEPT the ≤5-min demo video (pending recording)

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
- **Repo state:** fresh — only docs + empty scaffolding (`main.py`, `pyproject.toml`, empty
  `README.md`/`.env`). No real code yet.
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
| Data strategy: commit pre-generated samples AND support live generation/upload | Satisfies both "generated sample data" deliverable and "dynamic processing, not hardcoded" requirement; strongest demo | — Pending |
| Deploy to Vercel + Render/Railway (not local-only) | More impressive submission; accepts the deploy/CORS/cold-start cost | Phase 5 — DONE 2026-06-28: web on Vercel (rfq-agent-web.vercel.app), AI on Render via render.yaml Blueprint (rfq-agent-ai.onrender.com); CORS via `*.vercel.app` regex; E2E verified on the live stack. Free-tier cold start (~50s) accepted; guide in docs/architecture/deployment.md |
| Support paste + PDF/Word/Excel/PPT via best-effort text extraction (no heavy OCR) | Assignment §11 permits "extracted text"; broad format coverage without over-investing in parsing | — Pending |
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
*Last updated: 2026-06-28 — Phase 5 deployed (Vercel + Render) & E2E-verified; phase verification human_needed (demo video pending).*
