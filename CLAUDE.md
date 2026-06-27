# CLAUDE.md

> **Bid Desk** (repo: `aerchain`) — a prompt-driven procurement copilot that turns messy,
> inconsistent vendor proposals into a grounded, evidence-backed, side-by-side comparison, so a
> buyer can see what each vendor offered, what is missing or risky, and who is actually comparable
> — **without the AI inventing anything.**

This is a 5-day prototype for the *Generative AI Expert / Applied AI Engineer* assignment (`docs/assignment.md`), built for submission to **Aerchain / Agillos**. The assignment is graded on prompt design and AI reliability, not UI polish.

**Read `docs/assignment.md` before any non-trivial work** — it is the source of truth for scope and the evaluation rubric.

---

## 1. What We Are Building (Product First)

The user is a **procurement buyer** running a competitive bid for marketing services (8 line items: strategy & creative, TVC development, TVC production, social organic, paid media planning, paid media buying, kids advertising & claims compliance, launch program management).

Vendors respond in wildly different formats — different pricing labels, missing fields, contradictory statements, vague timelines, bundled prices, marketing fluff. The buyer's real job is **sense-making under uncertainty**, not scoring. Our product does that sense-making for them.

The end-to-end flow:

```
RFQ Generation → Vendor Response Input/Upload → Extraction Agent → Comparison Agent → Buyer-Facing UI
```

### Product Principles (these override convenience — they are how we win the rubric)

- **Evidence over assertion.** Every extracted fact carries a source snippet from the vendor's response. If it can't be traced to the source, it doesn't get shown as fact.
- **Absence is first-class.** `missing` / `unclear` / `conflicting` / `unsupported` are explicit, prominently surfaced states — never silently filled, never hidden to make the UI look tidy.
- **Comparability before ranking.** Tell the buyer *who is even comparable* before any scoring. Refuse misleading apples-to-oranges comparisons; say "not yet comparable — needs clarification."
- **No hallucinated commercial or technical claims.** When information is missing or contradictory, the AI flags it and proposes a clarification question. It never fabricates a number or a claim.
- **Buyer-first information hierarchy.** Be opinionated about what the buyer sees first (risks, gaps, clarifications, comparability) versus what lives on drill-down (full extraction, raw evidence).
- **The Prompt Pack is the product.** Prompts are versioned, traceable, first-class source artifacts — not strings buried in code. Prompt quality is 30% of the grade.

### What to optimize for (the rubric, so priorities stay honest)

| Area | Weight | Where it lives |
|---|---|---|
| Prompt quality & architecture | 30% | `services/ai/prompts/` (the Prompt Pack) |
| Realistic data generation | 20% | RFQ + vendor generation agents |
| Extraction accuracy & reliability | 20% | Extraction agent + grounding/evidence |
| Product thinking in comparison | 15% | Comparison agent + buyer UX decisions |
| UI/UX prompt quality & buyer usability | 10% | `apps/web` + UI/UX generation prompts |
| Demo clarity & documentation | 5% | README, write-up, demo video, prompt trace |

### What to avoid (from assignment §24 — treat as hard constraints)

Hardcoded outputs · static dashboards · generic prompts · unrealistically clean test data · unsupported AI claims · heavy normalization work · ignoring missing/contradictory info · misleading comparisons · **UI polish without strong AI behavior.**

---

## 2. Engineering Principles

- **Simplicity.** Make every change as simple as possible. No over-engineering, no temporary fixes. This is a 5-day prototype — favor the correct, demonstrable path over the enterprise-grade one.
- **Minimal impact.** Only touch what's necessary. Find root causes. Senior-developer standards.
- **No unrequested behavior.** Implement ONLY what was explicitly asked. No escape hatches, feature toggles, "safety" parameters, defensive fallbacks, or future-proofing nobody requested. If a fix seems to need a new flag, mode, or branch that wasn't in the spec — **STOP and ask.**
- **Never trust an LLM-supplied authorization or "verified" flag.** In an agent runtime the model will happily fabricate whatever bypasses a guard. Grounding/evidence checks are enforced in code, not by asking the model to promise it didn't hallucinate.
- **No functionality breakage.** Before shipping, verify the change doesn't regress a working flow. If you change a shared schema, prompt, or agent contract, list every caller and confirm each works.
- **Git.** Never include any AI tool (Claude, Codex, Copilot, etc.) as a commit co-author. Commits are authored solely by the human developer.
- **Enforced by PonyTail.** These principles aren't left to memory — the **PonyTail** skill (`full` mode) injects a "laziest senior dev" YAGNI ladder into every turn, including GSD-spawned subagents. It drives the *kind* of code written (reuse → stdlib → native → minimal); it must **never** challenge the requirement set we're building. See **§16**.

---

## 3. Engagement Protocol

- **Business first.** Before code, identify what's being solved against the *buyer's* needs and the rubric. Product impact first, implementation second.
- **Discuss before build.** For non-trivial work, talk through the goal with the user before routing to GSD. Don't invent missing context — if the brief is thin, ask.
- **Explore before implement.** First phase is always exploration: what exists, reuse vs. extend vs. build. Query the codebase knowledge graph first (§13) when one is built; until then use Glob/Grep/Read.
- **Stop and ask when uncertain.** Ambiguity, a risk to an existing flow, or a decision that belongs to the user → stop, present findings and open questions, then continue.
- **Think as an architect.** For every non-trivial feature: what's the right abstraction? What are the failure modes (especially hallucination + ungrounded claims)? Recommend the right trade-off for a 5-day prototype — correct and demonstrable, not the most sophisticated.
- **Delegate to preserve context.** Default to delegating discrete, parallelizable, or context-heavy work to subagents rather than doing it inline — exploration, multi-file search, research, code review, and isolated implementation. Use the right agent for the job: GSD agents/skills for planning/execution/review, and native Claude Code agents (`Explore` for broad read-only search, `Plan`, `general-purpose`, `fork` for context inheritance, etc.) otherwise. Spawn independent agents in parallel in one message. The main thread stays the orchestrator: it keeps the conclusions, not the raw file dumps. Only do work inline when it's trivial or genuinely sequential.

### Branch setup (per task)
1. Confirm `main` is checked out and up to date.
2. Merge conflicts → stop; user resolves manually.
3. Branch from `main`: `feat/{3-5-word-desc}` or `fix/{3-5-word-desc}` — lowercase, hyphenated.
4. Keep the branch focused on one coherent change.

### Worktrees (prefer for isolation)
- **Use git worktrees wherever possible** — especially for parallel plans/phases and for any agent that mutates files. Isolated worktrees prevent concurrent edits from colliding and keep `main` clean.
- Spawn file-mutating subagents with worktree isolation (`isolation: "worktree"` on the Agent tool, or GSD's worktree-backed execution) so parallel work doesn't conflict; the worktree is auto-cleaned if nothing changed.
- One coherent change per worktree, mirroring the branch rule above. Merge back to the task branch when the plan is verified.

---

## 4. Workflow Routing — GSD Entry Points

Route non-trivial work through GSD so planning artifacts and state stay in sync. This project is
fresh, so the lifecycle commands matter early.

| Situation | GSD Command |
|---|---|
| New project / set up roadmap & requirements | `/gsd:new-project` |
| Plan a phase | `/gsd:plan-phase [N]` |
| Capture decisions before planning | `/gsd:discuss-phase [N]` |
| Execute planned phase work | `/gsd:execute-phase [N]` |
| Small fix (1–3 files) | `/gsd:fast <description>` |
| Ad-hoc task / config change | `/gsd:quick <description>` |
| Bug report or error | `/gsd:debug` |
| UAT / verify completed work | `/gsd:verify-work [N]` |
| Check progress / what's next | `/gsd:progress` or `/gsd:next` |
| Ship / create PR | `/gsd:ship` |

**Don't make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it**
("just do it" / "skip GSD" = explicit bypass). When something goes sideways mid-execution, STOP and
re-plan via `/gsd:plan-phase --gaps-only` rather than manual recovery.

GSD planning artifacts live in `.planning/` and are **tracked in git** (committed alongside the
code): `PROJECT.md`, `STATE.md` (source of truth for position/decisions/blockers), `config.json`,
and phase folders once planning begins.

---

## 5. Architecture

**Monorepo (pnpm + turbo).** Two deployable apps + shared contracts. Frontend is TypeScript;
**all backend and all AI is Python.**

```
aerchain/
├─ apps/
│  └─ web/                     Next.js (App Router) — buyer-facing UI only. Deploys to Vercel.
│     └─ app/(buyer)/          the 5 screens (see §6)
├─ services/
│  └─ ai/                      FastAPI + LangChain/LangGraph. All AI + business logic. Python.
│     ├─ agents/               rfq_gen · vendor_gen · extraction · comparison (LangGraph graphs)
│     ├─ prompts/              THE PROMPT PACK — versioned prompt source (see §7)
│     ├─ schemas/              pydantic models: RFQ, VendorResponse, Extraction, Comparison
│     └─ api/                  FastAPI routers, SSE streaming endpoints
├─ packages/
│  └─ shared-types/            TS types generated/mirrored from the pydantic schemas (the contract)
├─ data/                       generated sample data: 1 RFQ + ≥3 messy vendor responses
└─ docs/                       assignment.md, write-up, prompt trace, architecture notes
```

- **Frontend — `apps/web` (Next.js, Vercel).** App Router only. Renders the buyer experience,
  consumes the AI service over HTTP/SSE. No AI SDKs and no business logic here — it is a thin,
  well-designed client. Use design-system primitives + tokens; no third-party UI kits.
- **Backend / AI — `services/ai` (FastAPI + LangGraph, Python).** Owns every agent, every prompt,
  every structured-output schema, all OpenAI calls. Deploys to **Render or Railway** (Vercel is for
  the Next.js app only — the Python service is long-running). This is where 70% of the grade lives.
- **Contract — `packages/shared-types`.** The pydantic schemas in `services/ai/schemas/` are the
  source of truth; the TS types mirror them so the UI and AI never drift. Change a schema → update
  both sides → list affected screens/agents.

### The AI pipeline (LangGraph)

| Agent / module | Job | Key reliability rule |
|---|---|---|
| **RFQ Generation** | Generate one realistic marketing-services RFQ (scope, timelines, items, commercials, questionnaire, compliance). | Must feel like a real procurement event, not a clean sample. |
| **Vendor Response Generation** | Generate ≥3 *deliberately messy* vendor responses that differ in pricing structure, completeness, scope, timelines, assumptions, clarity. | Inject real-world complexity (missing pricing, unclear taxes/currency, partial scope, vague timelines, weak compliance). No screen needed; prompt goes in the Prompt Pack. |
| **UI/UX Generation** | Prompt-guided buyer UI structure, dashboard sections, comparison views, UX copy. | Output captured as artifacts/prompts, reflecting buyer product thinking. |
| **Extraction** | Read a vendor response → structured extraction (scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, risks) + evidence snippets + flags for missing/unclear/conflicting/unsupported. | **Never fill missing info.** Every fact links to a source snippet. Flag, don't fabricate. |
| **Comparison** | Compare vendors across technical / commercial / scope / timeline / compliance / risk, grounded in extracted facts + evidence. | Establish comparability first; surface buyer attention points and clarification needs; never mislead. |

### LLM & framework
- **Provider:** OpenAI, **GPT-5.4 model family.** Default to **GPT-5.4** for the reasoning-heavy
  agents (extraction, comparison, RFQ/vendor generation); use **GPT-5.4 mini** for cheaper/easier
  tasks (classification, short rewrites, clarification-question drafting). **Do not use GPT-5.5** —
  too expensive for this prototype. Model IDs are env-configured; confirm the exact string before
  hardcoding it.
- **Framework:** **LangChain + LangGraph** for all agent/graph orchestration and prompt chaining.
  Do **not** use the OpenAI Agents SDK. The plain `openai` Python library is allowed only as a
  low-level model client (e.g. one-off structured calls) when LangChain doesn't fit — orchestration
  always stays in LangChain/LangGraph.
- **Structured output:** pydantic schemas with the OpenAI structured-output / JSON-schema path —
  extraction and comparison return validated objects, not free text.
- **Streaming:** agent responses stream to the UI over **SSE** (FastAPI emits, Next.js consumes).
  Never buffer-and-return long agent work.
- **Grounding:** evidence snippets and missing/conflict flags are validated in code against the
  source text — not taken on the model's word.

---

## 6. The Five Buyer Screens

Build these (or equivalent flows). Each must reflect the product principles in §1.

1. **RFQ Overview** — the procurement event: scope, timelines, item requests, commercial
   expectations, questionnaire, compliance. Makes clear what vendors must respond to.
2. **Vendor Upload / Input** — paste, upload, or otherwise provide vendor responses (PDF, PPT, Excel,
   Word, text, Markdown, JSON). Output is generated **dynamically** from input — never hardcoded.
3. **Extraction Review** — per-vendor extracted fields with highlighted important fields, missing /
   unclear / conflicting data, risks, and **evidence snippets**.
4. **Vendor Comparison** — side-by-side across technical, commercial, scope, timeline, compliance,
   risk. Shows who is comparable, where they differ, and what needs further review.
5. **Prompt Trace / Prompt Pack (optional but valuable)** — the prompts used, plus ≥1 full trace:
   input → prompt → model output → final structured/displayed output. May live in app, README, or docs.

---

## 7. Prompt Pack & Traceability

Prompts are the highest-weighted deliverable. Treat `services/ai/prompts/` as a first-class,
versioned source tree. The Prompt Pack must include prompts for: **RFQ generation, vendor response
generation, complex/messy data generation, UI/UX generation, extraction, comparison, and
clarification/exception handling.**

For each major prompt, document (inline or in `docs/`): what it does, why it's structured that way,
and how it handles unreliable / missing / conflicting information.

Keep at least **one complete prompt trace** (input → prompt → model output → final output)
reproducible and captured in `docs/` or the app.

---

## 8. AI Reliability (non-negotiable)

- The system is designed to avoid hallucination and unsupported claims.
- It explicitly identifies when information is missing, unclear, conflicting, unsupported, not
  comparable, or needs buyer review.
- Important outputs are backed by evidence from the vendor response wherever possible.
- Grounding/flagging is enforced in code, never delegated to an LLM-asserted "I didn't hallucinate."

---

## 9. Deliverables (what we owe at the end — assignment §20)

Working prototype · generated sample data (1 RFQ + ≥3 messy vendor responses) · Prompt Pack ·
UI/UX output · extraction & comparison outputs (with evidence + clarification questions) ·
≥1 prompt trace · ≤5-min demo video · 1–2 page write-up · README (setup, run, model/API reqs,
env vars, sample flow, assumptions).

---

## 10. Local Development

Everything runs locally; no cloud dependency for dev beyond the OpenAI API.

- **AI service (`services/ai`, Python):** `uv` for deps; run FastAPI with uvicorn (hot reload).
- **Web (`apps/web`, Next.js):** `pnpm dev`.
- **Env:** `OPENAI_API_KEY` (+ model IDs) for the AI service; the web app gets the AI service URL. Keep secrets in `.env` (gitignored); document every required var in the README.

### Docker Compose (placeholder — evolves with the code)
A `infrastructure/docker-compose.yml` is the intended one-command local setup (`docker compose up`
brings up the AI service + web together). **It does not exist yet** — add and grow it as the code
lands (start with the two app services; add anything else only when a feature actually needs it).
Until it exists, run the two apps directly as above. **Don't pre-build infra the prototype doesn't
need** — no database, queue, or vector store unless a feature requires one.

---

## 11. Testing

Two layers, both required: **code-level tests** (the agent runs them) **and functional UAT**
(end-to-end verification of the buyer flow).

### Code-level tests (agent runs before handoff — never ask the user)
- **AI service (Python):** `uv run pytest` from `services/ai/`. Prioritize tests on schema validation, extraction grounding (no fabricated fields — every fact has an evidence span), and comparison comparability logic.
- **Web (TypeScript):** vitest from `apps/web/` when there's logic worth covering.
- **Streaming APIs:** verify SSE with `curl -N <url>`; events are `data: {"type": ..., "payload": ...}`.

### Functional UAT testing (the buyer flow, end-to-end via Playwright)
Code-level tests don't prove the *product* works. **Before handing a phase/plan off to the user, the
agent drives the full buyer journey end-to-end in a real browser using the Playwright browser tool**
— don't just assert with curl/unit tests, actually click through the running app:
- Generate RFQ → input ≥3 messy vendor responses → run extraction → view comparison → view trace.
- Assert the AI behaviors that win the rubric: missing/unclear/conflicting fields are surfaced (not
  hidden), every shown fact has a visible evidence snippet, non-comparable vendors are flagged as
  such, and **no fabricated** numbers or claims appear.
- Use Playwright to navigate, fill/upload vendor inputs, wait for SSE-streamed results, read the
  rendered DOM, and capture screenshots of each screen for the demo/write-up.
- Capture the UAT script + expected outcomes (and Playwright steps) under `docs/qa/` so it's
  repeatable and demoable.
Provide the UAT steps + regression scenarios as the handoff after every change.

### Completion checklist (before handoff)
- [ ] Change implemented via the appropriate GSD workflow
- [ ] Relevant test suite passing (run by the agent)
- [ ] **Playwright end-to-end pass of the buyer flow on the running app** (not just unit/curl checks)
- [ ] No hallucination / ungrounded-claim regression introduced
- [ ] Prompt changes reflected in the Prompt Pack + a trace if behavior changed
- [ ] UAT handoff: (1) steps to verify end-to-end, (2) regression scenarios for affected flows

---

## 12. Deployment

- **`apps/web` → Vercel** (Next.js native).
- **`services/ai` → Render or Railway** (long-running Python service; not Vercel).
- The web app reaches the AI service via an env-configured base URL. AWS is out of scope for now.

---

## 13. Knowledge Graph — Query Before Exploring

A `graphify` codebase knowledge graph is the intended dev-time intel layer for cross-file/cross-app
questions, dependency traces, and impact analysis.

> **Not built yet** — the repo is fresh. Build it once there's meaningful code:
> `graphify update .` (incremental, SHA256-cached, no API cost). It writes to `graphify-out/`;
> read `graphify-out/GRAPH_REPORT.md` for the current node/edge counts and build commit — don't
> trust a hardcoded number. Until the graph exists, use Glob/Grep/Read.

Once built, **query it before grepping or spawning an Explore agent** for any cross-app question
(e.g. web → SSE → FastAPI → agent → prompt):

```bash
graphify query "<question>"            # BFS — broad context, nearest neighbours first
graphify query "<question>" --dfs      # DFS — trace one specific call path
```

Queries anchor on **node labels / entity names** — name the real symbol, file, or component
(`extraction_graph`, `ComparisonResult`, `sse_emitter`), not a vague sentence. If a query returns
nothing useful, say so and fall back to Grep — don't burn turns re-phrasing.

**Use the graph for:** "where is X defined/used?", tracing a call chain, impact analysis before
touching a shared schema/endpoint/prompt contract, finding all callers/importers.
**Not for:** regex/literal string search (use Grep), or files newer than the last build (Glob/Grep
or rebuild first). Keep it current after significant changes (`git rev-parse HEAD` vs the build
commit in `GRAPH_REPORT.md`).

---

## 14. Documentation — the `docs/` Folder

`docs/` is dual-purpose: (1) **the submission package** sent to Aerchain when the repo is ready, and
(2) **our own working reference.** Keep it clean, current, and broken out folder-wise — treat stale
docs as a bug. Update the relevant doc in the same change that alters behavior.

```
docs/
├─ assignment.md              the brief (source of truth — do not edit)
├─ write-up.md                1–2 page submission write-up (problem, assumptions, prompt
│                             architecture, product thinking, limitations, what's next)
├─ architecture/             system + AI-pipeline diagrams, schema/contract notes, decisions
├─ prompts/                  Prompt Pack docs: per-prompt intent, rationale, failure handling
├─ traces/                   ≥1 full prompt trace (input → prompt → model output → final output)
├─ qa/                       functional UAT scripts + expected outcomes (see §11)
├─ samples/                  generated RFQ + ≥3 messy vendor responses (with notes on the messiness)
└─ demo/                     demo script / storyboard for the ≤5-min video
```

Deliverables (§9) map directly onto these folders. Anything relevant to the submission goes here,
written as if a reviewer at Aerchain will read it — not buried in code comments or chat.

---

## 15. Gotchas

- **Vercel hosts the Next.js app only.** The Python AI service is long-running → Render/Railway.
  Don't try to run FastAPI/LangGraph on Vercel.
- **Schemas are the contract.** `services/ai/schemas/` (pydantic) is the source of truth;
  `packages/shared-types` mirrors it. Change one → change both → list affected screens/agents, or
  the UI and AI silently drift.
- **`openai` lib ≠ OpenAI Agents SDK.** Orchestration stays in LangChain/LangGraph; the `openai`
  library is only a low-level model client when LangChain doesn't fit.
- **Model tier discipline.** GPT-5.4 for reasoning-heavy agents, GPT-5.4 mini for cheap tasks,
  **never GPT-5.5.** Don't silently upgrade a model to "fix" a quality issue — fix the prompt first.
- **Never buffer-and-return agent work.** Long agent steps stream over SSE.
- **Grounding is enforced in code, not by the model.** Don't accept the model's word that a fact is
  supported — validate the evidence span exists in the source.
- **Don't over-build infra.** No DB/queue/vector store, no Docker service, no CI stage until a
  feature actually requires it (see §10).

---

## 16. PonyTail — Code-Minimalism Guardrail

**GSD runs the show.** GSD owns the entire lifecycle (discuss → plan → execute → verify → ship)
and, with the planning artifacts in `.planning/`, owns *what* we build and *whether* it's in scope.
**PonyTail is a guardrail, not a decision-maker:** a "laziest senior dev" that challenges the *kind*
of code being written — never the requirement set. The line is absolute:

> PonyTail governs **implementation shape**. GSD CONTEXT.md / locked requirements govern **scope**.
> When they ever appear to conflict, **scope wins** — PonyTail does not re-argue a locked decision.

### How it reaches our work
PonyTail (`full` mode, the default) injects its YAGNI ladder on every turn **and into every
GSD-spawned subagent** via a `SubagentStart` hook — so it reaches `gsd-executor`/`gsd-planner`,
which is where nearly all real code is written. The ladder: *does this need to exist? → already in
the codebase? → stdlib? → native platform feature? → installed dependency? → one line? → only then,
minimal code.* This is just §2's Engineering Principles, enforced instead of hoped for.

### Where it's used across the workflow
| GSD stage | PonyTail role |
|---|---|
| `/gsd:plan-phase`, `/gsd:execute-phase` | `full` ladder active in the executor subagents — biases reuse/stdlib/native/minimal as code is written |
| After execute, before `/gsd:verify-work` | `/ponytail-review` on the phase diff — a **complexity-only** gate that runs *alongside* `gsd-code-reviewer` (correctness/security), never instead of it |
| Phase 5, pre-submission | `/ponytail-audit` — one whole-repo over-engineering sweep so reviewers see a lean codebase |
| Anytime | `/ponytail-debt` — harvests `ponytail:` comments into a deferral ledger; mirrors CONTEXT.md "Deferred Ideas" |

### Operating rules
- **`full`, never `ultra`.** `ultra` "challenges the rest of the requirement" — forbidden here; our
  requirements are the graded rubric. `lite`/`full` only.
- **What PonyTail must never trim:** anything in §1 (product principles), §8 (reliability), or a
  locked CONTEXT.md decision — the absence-enum `Field[T]` envelope, evidence offsets, the
  code-enforced grounding gate, the four flag types, the full SSE taxonomy, the 7 prompt stubs, the
  codegen drift-check. These are deliverables, not bloat, even when they read as single-use today.
- **Mark deliberate "kept complexity"** with a `ponytail:` comment naming why
  (`# ponytail: this exists — PLAT-01 contract, filled in P3`). Then `/ponytail-review` reads intent,
  not slop, and `/ponytail-debt` tracks it.
- **Review/audit are advisory** — they *list*, they never auto-apply. A human or GSD verify decides.
- Its own "When NOT to be lazy" rule already protects validation at trust boundaries, error handling,
  security, accessibility, and **anything explicitly requested**, and it requires (never deletes) one
  minimal runnable check per non-trivial logic path — consistent with §11.

---

## Notes
- This document is product-first by design; the architecture in §5 is the agreed plan for a fresh repo (no code exists yet). Refine it as phases get planned — keep this file the single high-level source of truth and push detail into GSD phase artifacts.
