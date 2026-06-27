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

### Code minimalism — PonyTail (enforced)

The **PonyTail** skill makes the principles above operational, not aspirational. It runs at `full` mode by default and is injected into every GSD-spawned subagent (a `SubagentStart` hook), so it reaches `gsd-executor`/`gsd-planner` — where the code is actually written.

Before writing code, climb the ladder and stop at the first rung that holds: **(1)** does this need to exist at all (YAGNI)? → **(2)** already in this repo (reuse a helper / type / pattern)? → **(3)** stdlib does it? → **(4)** native platform feature? → **(5)** already-installed dependency? → **(6)** one line? → **(7)** only then, the minimum code that works.

- **Governs the *kind* of code, never the *scope*.** GSD owns *what* we build and *whether* it's in scope (ROADMAP / REQUIREMENTS / CONTEXT.md). PonyTail never re-argues a locked requirement or decision — when they appear to conflict, **scope wins**.
- **`full` or `lite` only — never `ultra`.** `ultra` challenges the requirement itself; ours is the graded rubric, so it stays off.
- **Never simplify away the reliability machinery in §1 / §8** — the absence-enum envelope, evidence grounding, the four flag types, the prompt-pack stubs — even when a piece reads as single-use today (the contract precedes the agents that fill it). Mark deliberate kept-complexity with a `# ponytail:` comment naming why, so review reads intent, not slop.
- **Review gates:** `/ponytail-review` (a diff) and `/ponytail-audit` (the repo) are **complexity-only** passes that *list, never apply* — they complement `gsd-code-reviewer` (correctness/security), never replace it.

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

**Anchor every lifecycle action on `docs/assignment.md`.** It is the PRD and source of truth —
discussion, planning, execution, and verification/UAT each read it (alongside the phase's
CONTEXT.md) so plans, tests, and UAT scripts stay tailored to the original use case and the §22
rubric. Nothing drifts from the brief.

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

The bar is set in §1 (evidence over assertion, absence first-class, no hallucinated claims) and §2
(grounding enforced in code, never on the model's word). The one rule to keep explicit: every fact
is marked **present / missing / unclear / conflicting / unsupported / not-comparable** — surfaced,
never silently filled.

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

### Docker Compose (placeholder)
Not built yet — run the two apps directly (above). A `infrastructure/docker-compose.yml` for
one-command local setup (`docker compose up`) **will be added and expanded here as the compose infra
lands**; don't pre-build it before a feature needs it (§2).

---

## 11. Testing

Two layers, both required: **code-level tests** (the agent runs them) **and functional UAT**
(end-to-end verification of the buyer flow).

### Code-level tests (agent runs before handoff — never ask the user)
- **AI service (Python):** `uv run pytest` from `services/ai/`. Prioritize tests on schema validation, extraction grounding (no fabricated fields — every fact has an evidence span), and comparison comparability logic.
- **Web (TypeScript):** vitest from `apps/web/` when there's logic worth covering.
- **Streaming APIs:** verify SSE with `curl -N <url>`; events are `data: {"type": ..., "payload": ...}`.

### Functional UAT testing (the buyer flow, end-to-end via Playwright)
Code-level tests don't prove the *product* works. Design each UAT against `docs/assignment.md` (the
PRD + §22 rubric) so it verifies the original use case, not just that code runs. **Before handing a
phase/plan off to the user, the agent drives the full buyer journey end-to-end in a real browser
using the Playwright browser tool** — don't just assert with curl/unit tests, actually click through
the running app:
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

## 15. Gotchas (quick reference — full rules in the linked sections)

- **Vercel = Next.js only;** the long-running Python service goes to Render/Railway (§12).
- **Schemas are the contract** — change pydantic and regenerate `shared-types` together (§5).
- **Model tier:** GPT-5.4 / 5.4-mini, **never 5.5**; fix the prompt before upgrading a model (§5).
- **Never buffer-and-return** — stream agent work over SSE (§5, §11).
- **Grounding is code-enforced** — validate the evidence span exists; never trust a model "verified" flag (§2, §8).
- **Don't over-build infra** — no DB/queue/vector/CI until a feature needs it (§2, §10).

---

## Notes
- This document is product-first by design; the architecture in §5 is the agreed plan for a fresh repo (no code exists yet). Refine it as phases get planned — keep this file the single high-level source of truth and push detail into GSD phase artifacts.
