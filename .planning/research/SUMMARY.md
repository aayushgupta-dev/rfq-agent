# Project Research Summary

**Project:** Bid Desk (repo: `aerchain`)
**Domain:** Prompt-driven procurement RFQ extraction & vendor-comparison AI prototype (5-day assignment, graded 70% on prompts + AI reliability)
**Researched:** 2026-06-27
**Confidence:** HIGH

## Executive Summary

Bid Desk is a prompt-driven procurement copilot: it turns messy, inconsistent vendor proposals for a marketing-services bid into a grounded, evidence-backed, side-by-side comparison — **without inventing anything.** The way experts build this is exactly what mature procurement practice already does: *surface differences, flag non-comparability, and clarify before scoring* — minus the heavy normalization the assignment explicitly forbids. The research is unusually decisive because the stack is pre-decided (Next.js thin client + FastAPI/LangGraph Python service + pydantic->TS contract) and the "features" are a graded rubric, not a guess: prompts 30% · data-gen 20% · extraction 20% · comparison 15% · UI 10% · demo/docs 5%. **70% of the grade lives in `services/ai/`**, so the entire build must be sequenced AI-first, UI-last.

The recommended approach has one architectural keystone: an **"LLM proposes, code disposes" grounding gate**. The model extracts facts plus a verbatim evidence snippet and a tentative flag; then *pure code* (no LLM) verifies each snippet is actually present in the source text (normalized exact-match, falling back to high-threshold fuzzy ~0.90). If a snippet can't be located, code overrides the model — the field becomes `unsupported` and its value is suppressed from the fact view. This single mechanism is the headline reliability claim and the most important code in the repo. It depends on two foundational schema decisions made *before any agent exists*: (1) absence is a first-class enum state — every field is `{status: present|missing|unclear|conflicting|unsupported, value?, evidence?}`, never a nullable that collapses into a blank cell; and (2) pydantic schemas are the single source of truth, mechanically generating both the OpenAI structured-output schema and the `packages/shared-types` TS contract.

The dominant risks are all rubric-attacking and well-understood: fabricated facts/citations (LLMs invent plausible prices and fake "verbatim" quotes ~50% of the time), trusting a model-supplied `grounded:true` flag, silently filling missing fields, ranking non-comparable vendors, over-normalizing real differences away, generating test data that's too clean to test anything, and — the timeline trap — sinking days into UI polish, infra, or document-parsing rabbit holes while the 70% AI behavior stays weak. Every one of these is preventable by code-enforced grounding, the absence-enum schema, a comparability gate before any scoring, a deliberate "mess spec" for data generation, and disciplined phase sequencing. The Prompt Pack (7 documented prompts + >=1 full trace) is cross-cutting from day one because it alone is 30% of the grade.

## Key Findings

### Recommended Stack

The stack is pre-decided in `CLAUDE.md §5`; STACK.md pins **current June-2026 versions** and fills the gaps (SSE transport, OpenAI API surface, pydantic->TS tooling). Three load-bearing facts: GPT-5.4 is real (`gpt-5.4` / `gpt-5.4-mini`, GPT-5.5 forbidden on cost); LangChain/LangGraph are both past 1.0 with a stable v1 API (`init_chat_model`, `with_structured_output`); and **LangGraph 1.x streaming uses the v2 `StreamPart` format, not the legacy `(mode, chunk)` tuple** — the single riskiest copy-paste trap for the SSE wiring.

**Core technologies:**
- **LangChain 1.3.x + LangGraph 1.2.x (Python)** — agent/graph orchestration; `StateGraph` is the right abstraction for the extraction->comparison pipeline.
- **pydantic 2.13.x** — structured-output schemas; the single source of truth driving both OpenAI strict JSON-schema and the TS contract.
- **FastAPI 0.135.x + `sse-starlette`** — SSE streaming endpoints; `sse-starlette` gives more control over LangGraph stream re-shaping than the built-in.
- **`gpt-5.4` (reasoning-heavy) / `gpt-5.4-mini` (cheap tasks)** — env-configured model IDs; confirm API access day 1.
- **`pydantic-to-typescript` (`pydantic2ts >=2`)** — wired as a `gen:types` codegen script so the UI/AI contract is enforceable, not a hand-mirrored drift risk.
- **Next.js 16.2 (App Router) + pnpm 9.x + Turborepo 2.x** — thin buyer client; no AI SDKs or business logic.
- **pypdf / python-docx / openpyxl / python-pptx** — best-effort text extraction only (no OCR, per §11). `python-multipart` is a hidden FastAPI upload requirement.

### Expected Features

FEATURES.md derives "table stakes" directly from the graded rubric (§22) and the brief (§4–§24), organized along three axes: the 5 buyer screens, the AI agents/Prompt Pack, and the reliability layer.

**Must have (table stakes — the ~70% gradeable core):**
- **The Prompt Pack** — all 7 prompts (RFQ gen, vendor gen, messy-data gen, UI/UX gen, extraction, comparison, clarification), each documented with what/why/how-it-handles-unreliable-info. The single largest area (30%).
- **Extraction agent** — structured per-vendor extraction + evidence snippets + 4 flag types; never fills missing info (20%).
- **Code-enforced grounding** — validates every evidence span in code; the reliability headline.
- **RFQ-gen + vendor-gen with deliberate messy-data injection** — >=3 realistically messy responses; clean data fails the 20% data-gen purpose.
- **Comparison agent** — comparability-before-ranking + clarification questions, consuming only grounded extraction (15%).
- **Five buyer screens** rendering the above legibly, with a buyer-first information hierarchy (risks/gaps/comparability first) (10%).
- **>=1 prompt trace** (required §16, cheap, lifts 30% + 5%) and **dynamic processing** (live agent runs, never hardcoded).

**Should have (differentiators — §21, add when core is solid):**
- Comparability matrix / readiness signal (qualitative, not a numeric leaderboard) — lifts 15%.
- Per-RFQ-line-item alignment view (light alignment, not normalization) — lifts 15%.
- Prompt failure examples + the fix; prompt versioning/evaluation notes — strong 30% signal.
- Architecture diagram — cheap 5% lift.

**Defer / avoid (v2+ or anti-features):**
- OCR, stateful human-review workflow, built feedback loop — defer (low ROI for 5 days).
- Quantitative should-cost engine, weighted scoring over messy data, heavy normalization — **avoid** (hallucination + misleading-comparison risk, graded against you per §24).

### Architecture Approach

ARCHITECTURE.md keeps the decided monorepo topology and details the AI pipeline. The extraction agent is a **linear LangGraph `StateGraph` with a hard grounding gate**: `segment` (pure text, keeps character offsets) -> `extract` (LLM -> pydantic) -> `ground` (PURE CODE, verifies spans, overrides flags) -> `finalize`. The comparison agent is **comparability-first** and consumes *only* code-validated `ExtractionResult[]`, never raw vendor text — preserving the grounding boundary transitively. Graph-internal `TypedDict` state is deliberately separate from the pydantic contract that crosses the API boundary. Everything streams over a single `{type, payload}` SSE envelope (one emitter, one consumer).

**Major components:**
1. **`schemas/` (pydantic)** — single source of truth; drives OpenAI structured output AND the generated TS contract. A leaf dependency (nothing in it imports agents).
2. **`grounding/` (pure code, no LLM)** — physically separated from agents to make the "we don't trust the model" story legible and unit-testable in isolation.
3. **`agents/` (LangGraph)** — extraction (linear, grounding-gated) and comparison (comparability-gated), plus rfq_gen/vendor_gen.
4. **`prompts/` (the Prompt Pack)** — versioned code module, never inline strings; backs `/prompts` + `/traces` endpoints.
5. **`api/` (FastAPI SSE)** — thin routers re-shaping `graph.astream` chunks into the `{type, payload}` envelope.
6. **`apps/web` (thin client)** — consumes `@aerchain/shared-types`, parses SSE via `fetch`+`ReadableStream` (not native `EventSource`, which is GET-only).

### Critical Pitfalls

The top failure modes all attack the rubric directly; every grounding prevention is **code-enforced, not prompt-promised**.

1. **Fabricated facts & fake evidence** — LLMs invent plausible prices and reword/stitch "verbatim" quotes (~50% citation failure rate). *Avoid:* schema requires an evidence field on every fact; code verifies the span exists in source (normalized + high-threshold fuzzy); unmatched -> `unsupported`, value suppressed.
2. **Trusting an LLM-asserted `verified`/`grounded` flag** — the model will set `true` next to a fabrication. *Avoid:* grounding status is computed in code only; grep for any branch reading a model boolean to display a fact — expect zero.
3. **Silently filling missing fields** — absence collapses into null/blank/zero, indistinguishable from "vendor said none." *Avoid:* model absence as an explicit enum state, never a nullable; distinguish "didn't mention" (`missing`) from "explicitly zero" (`present`, value=0, has evidence).
4. **Misleading comparisons / ranking non-comparable vendors** — a tidy score over 5/8-item or different-currency bids. *Avoid:* a comparability gate emits `comparable | partially | not_comparable` with reasons *before* any scoring; never aggregate over fields any vendor is missing.
5. **Over-normalization** — flattening bundled/multi-currency/partial bids into one clean baseline reintroduces hallucination via inference. *Avoid:* surface differences, keep originals visible, flag bundled as `unclear`; scope normalization OUT.
6. **Data too clean + structured-output failures** — clean test data proves nothing (drive from an explicit per-vendor "mess spec" and assert messiness); and strict-mode truncation/refusals corrupt output (treat `finish_reason: length` as a hard error, check the `refusal` field, all-fields-required + no defaults, split large schemas).
7. **Timeline traps** — UI polish, infra, and document-parsing rabbit holes while AI behavior stays weak. *Avoid:* sequence AI-behavior-before-polish-before-infra; best-effort text only; no DB/queue/vector store/Docker/CI until a feature demands it.

## Implications for Roadmap

The dependency chain is strict and the research is unanimous: **schemas/contract first -> grounding + tests early -> extraction -> comparison (strictly after extraction) -> UI last -> deploy last.** The Prompt Pack is cross-cutting from day one (it is 30% of the grade and every agent imports from it). Suggested phase structure:

### Phase 1: Foundation — Schemas, Contract, LLM Access & Day-1 De-risking
**Rationale:** Everything downstream is typed by the schemas; they drive OpenAI structured output AND the TS contract. The absence-enum schema state is foundational and everything depends on it. Front-load the three day-1 unknowns before building on them.
**Delivers:** pydantic schemas (RFQ, VendorResponse, ExtractionResult with `{status, value?, evidence?}` field model, ComparisonResult, SSEEvent envelope); `pydantic2ts` codegen wired to `packages/shared-types`; `llm/` client with env-configured `gpt-5.4`/`mini`; the Prompt Pack registry skeleton.
**Addresses:** Structured schemas (FEATURES §21), the contract discipline (CLAUDE §15).
**Avoids:** Pitfall 4 (absence not first-class), Pitfall 8 (strict-mode schema design: all-required, no defaults), pydantic->TS drift.
**De-risking (must happen here):** (1) live "ping" call confirming the org/key has `gpt-5.4` access; (2) `pydantic2ts` codegen producing real TS; (3) a minimal LangGraph `.stream(version="v2")` -> SSE -> `curl -N` proof.

### Phase 2: The Grounding Gate (pure code) + Data Generation
**Rationale:** Grounding is LLM-free, so it can be built and fully unit-tested *before* any agent works — front-load the reliability keystone. Data-gen is the first content phase; its messiness is what makes extraction worth testing, and it has no upstream dependency beyond the RFQ spine.
**Delivers:** `grounding/verify.py` (normalize -> exact -> high-threshold fuzzy -> flag downgrade) with `test_grounding.py` (real span passes; fabricated span downgraded to `unsupported`); RFQ-gen + vendor-gen agents with an explicit per-vendor "mess spec" and a messiness assertion; committed sample data (1 RFQ + >=3 messy vendors).
**Addresses:** Code-enforced grounding (the reliability headline), data-gen 20%.
**Avoids:** Pitfall 1/2/3 (the entire fabrication surface), Pitfall 7 (clean data).
**Uses:** schemas from Phase 1; the rfq_gen/vendor_gen + messy_data prompts.

### Phase 3: Extraction Agent + SSE Plumbing
**Rationale:** Extraction needs schemas (1), grounding (2), and its prompt; it is the input to everything in comparison. SSE plumbing needs at least one working graph to stream, so it lands here.
**Delivers:** extraction `StateGraph` (segment -> extract -> ground -> finalize); `api/sse.py` + `/extract` route mapping LangGraph v2 stream chunks to the `{type, payload}` envelope; truncation/refusal handling; extraction prompt documented; >=1 captured trace.
**Addresses:** Extraction 20%, evidence snippets + 4 flags, SSE streaming requirement.
**Avoids:** Pitfall 8 (truncation/refusal), Anti-pattern 3 (buffer-and-return).

### Phase 4: Comparison Agent + Comparability Gate
**Rationale:** **Strictly after extraction** — comparison consumes only `ExtractionResult[]`, never raw text. The comparability gate is its core 15% deliverable.
**Delivers:** comparison `StateGraph` (comparability_gate -> dimension_compare -> attention_points); `/compare` route; clarification-question generation; comparability verdict per dimension/line-item.
**Addresses:** Comparison 15%, comparability-before-ranking, clarification questions (§15.7).
**Avoids:** Pitfall 5 (ranking non-comparable), Pitfall 6 (over-normalization).

### Phase 5: Buyer UI (thin client) + Prompt Trace view
**Rationale:** UI is last — it's a 10% thin client that needs the contract types and live routes to be real, so the demo is dynamic (§24), not mocked.
**Delivers:** Screens 1–4 (RFQ Overview, Vendor Upload, Extraction Review with evidence highlighting via grounding offsets, Vendor Comparison) + Screen 5 (Prompt Trace); buyer-first information hierarchy (risks/gaps/comparability first); UI/UX-generation prompt as an artifact.
**Addresses:** UI 10%, the 5 screens, in-app trace.
**Avoids:** Pitfall 9 (hiding absence to look tidy), Pitfall 11 (polish over behavior).

### Phase 6: Deploy + Submission Package
**Rationale:** Deploy last (CORS/cold-start cost accepted for a stronger submission); docs are the 5% capstone.
**Delivers:** web -> Vercel, AI -> Render/Railway with env-configured base URL + CORS + disabled proxy buffering; README, 1–2 page write-up, demo video, architecture diagram, full Prompt Pack docs.
**Addresses:** Demo/docs 5%, all §20 deliverables.

### Phase Ordering Rationale

- **Schemas before everything** because they are the contract for OpenAI structured output, the TS types, and every agent's I/O.
- **Grounding early and in isolation** because it is LLM-free and is the rubric's headline reliability mechanism — proving it before agents exist de-risks the 70% AI grade.
- **Extraction before comparison is non-negotiable** — comparison literally cannot be built or tested without `ExtractionResult[]`.
- **UI last and deploy last** because UI is a thin 10% client and §24 penalizes polish/infra over AI behavior; building against live routes keeps the demo dynamic.
- **Prompt Pack is cross-cutting**, not a phase — each phase contributes its documented prompt + (where it makes sense) a trace.

### Research Flags

Phases likely needing deeper research during planning (`/gsd:plan-phase --research-phase`):
- **Phase 3 (Extraction):** OpenAI strict structured-output edge cases (truncation/refusal handling, schema-splitting when 8 line items x fields x evidence strains limits) and LangGraph v2 stream-mode -> SSE mapping warrant a focused look; these are the highest-novelty, highest-risk integration points.
- **Phase 4 (Comparison):** The comparability-signal *representation* (matrix vs. narrative vs. per-dimension badge) and the precise "light alignment vs. heavy normalization" boundary are open product-thinking decisions worth resolving with research.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** pydantic + `pydantic2ts` + env config are well-documented; STACK.md already pinned versions and gotchas.
- **Phase 2 (Grounding/Data-gen):** grounding is straightforward string-matching (no DB/embeddings); the mess-spec approach is fully specified in PITFALLS.md.
- **Phase 5 (UI):** thin Next.js client consuming SSE — patterns are established; STACK.md resolved the `EventSource` vs `fetch`-stream choice.
- **Phase 6 (Deploy):** standard Vercel + Render/Railway split; gotchas already catalogued.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI/npm/official docs as of June 2026 (not training data); only open variable is account-specific GPT-5.4 access. |
| Features | HIGH | Table stakes derived directly from the graded rubric §22 and the brief §4–§24 (the source of truth); differentiators are §21 verbatim. |
| Architecture | HIGH | Topology pre-decided in CLAUDE.md §5; pipeline design verified against current LangGraph/FastAPI docs (Context7). Fuzzy-threshold tuning is MEDIUM (a project decision). |
| Pitfalls | HIGH | Assignment §17/§23/§24 + CLAUDE.md §8/§15 are explicit; structured-output and citation-hallucination failure modes verified against current OpenAI docs and 2025–26 grounding research. |

**Overall confidence:** HIGH

### Gaps to Address

- **GPT-5.4 API access (account-specific):** the model exists, but the org/key's access isn't verified. *Handle:* a single live ping call in Phase 1 before building on it.
- **Grounding fuzzy threshold (~0.90):** the value is an educated default; PDF-extraction reflow could cause false downgrades or fabrications could squeak through if mis-tuned. *Handle:* tune against the real messy sample data in Phase 2, with `test_grounding.py` as the guardrail.
- **Extraction schema size:** 8 line items x many fields x evidence may strain strict-mode truncation/refusal limits. *Handle:* test the single-call schema against the messy samples in Phase 3; split per-section if it strains.
- **Comparability signal representation & the "light alignment vs. heavy normalization" line:** product-thinking decisions, not technical unknowns. *Handle:* resolve explicitly during Phase 4 planning (touches the 15% grade).
- **Screen 5 location (in-app vs. docs):** §6 marks it optional, §16 requires a trace somewhere. *Handle:* default to in-app for demo value; allow slip to docs if time-pressed.

## Sources

### Primary (HIGH confidence)
- `docs/assignment.md` §4–§24 — table stakes, differentiators (§21), anti-features (§24), rubric weights (§22), reliability (§17/§23).
- `CLAUDE.md` (§1 product principles, §2 never-trust-LLM-flag, §5 architecture, §8 reliability, §10/§11/§15 infra/testing/gotchas) and `.planning/PROJECT.md` (decisions).
- OpenAI docs — `gpt-5.4`/`gpt-5.4-mini` (released 2026-03-05); Structured Outputs (strict mode all-required, no defaults, truncation->invalid JSON, `refusal` field).
- Context7 `/websites/langchain_oss_python_langchain`, `/langchain-ai/langgraph`, `/fastapi/fastapi` — `init_chat_model`, `with_structured_output`, LangGraph v2 `StreamPart` streaming, FastAPI SSE/`EventSourceResponse`.
- PyPI/npm/official releases — LangChain 1.3.11, LangGraph 1.2.6, pydantic 2.13.4, FastAPI 0.135.x, Next.js 16.2, pypdf 6.14.2, `sse-starlette` (May 2026), `pydantic-to-typescript >=2`.

### Secondary (MEDIUM confidence)
- Procurement-practice sources (bid tabulation, responsive-vs-non-responsive bids, cure letters, normalization, TCO/should-cost) — establish that Bid Desk's principles *are* mature procurement practice minus heavy normalization.
- LLM citation-grounding / hallucination research (2025–26 arXiv) — models lack faithful citation support ~50% of the time; code-side verification is the reliable check.

### Tertiary (LOW confidence)
- Grounding fuzzy-match threshold (`rapidfuzz partial_ratio` ~0.90) — standard pattern; exact threshold is a project tuning decision, not an external claim.

---
*Research completed: 2026-06-27*
*Ready for roadmap: yes*
