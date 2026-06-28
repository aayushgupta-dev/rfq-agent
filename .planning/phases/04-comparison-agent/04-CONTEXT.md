# Phase 4: Comparison Agent - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning

<domain>
## Phase Boundary

A LangGraph comparison agent consumes **only code-validated `ExtractionResult[]`** (one per
vendor) + the original `RFQ`, and produces a `ComparisonResult` that **establishes comparability
before any ranking**. The grounding boundary holds transitively — comparison never reads raw vendor
text (COMPARE-01).

**In scope (COMPARE-01..05):**
- Flesh out the `ComparisonResult` schema (currently a 2-field stub in `domain.py`) into the real
  shape: two surfaces (6-dimension comparability matrix + 8-line-item × vendor offer table),
  per-vendor readiness, buyer attention points, clarification questions.
- The comparison agent: a LangGraph `StateGraph` that aligns → judges comparability → compares →
  generates clarifications, streaming progress over SSE.
- A **code-side comparability guard** that clamps the model's per-dimension verdict to a
  flag-derived ceiling (can only downgrade, never upgrade).
- The `comparison.v1.md` prompt (currently a TODO stub) authored in full.
- The `clarification.v1.md` prompt (currently a TODO stub) authored in full — a **separate
  gpt-5.4-mini call** seeded by a code-collected set of flagged fields.
- ≥1 captured **comparison trace** (JSON + rendered MD under `docs/traces/`) showing the
  raw-model-verdict → code-clamped-verdict diff.

**Out of scope (later phases):**
- Buyer UI / Vendor Comparison screen / in-app trace viewer / file upload — Phase 5.
- CORS / deploy / proxy-buffering config — Phase 5.
- Any numeric leaderboard, weighted score, or should-cost engine — permanently out of scope
  (REQUIREMENTS Out of Scope; §24).
</domain>

<decisions>
## Implementation Decisions

### Comparability signal representation (COMPARE-02/05; closes carried-forward WR-01)
- **D-01:** **Hybrid representation.** Badge matrix is the headline (vendor × 6 dimensions, each
  cell = `comparable | partially | not_comparable` + a one-line reason), with a per-dimension
  **narrative** synthesis on drill-down, plus a **buyer attention-points panel**. The matrix is the
  scannable buyer-first surface (UI-06); narrative is secondary.
- **D-02:** **`not-comparable` lives at the comparison level — NOT on the field-level `FlagStatus`
  enum.** This closes the P2-review WR-01 carry-forward by design: the per-dimension verdict is a
  new `ComparisonResult`-level type (`comparable | partially | not_comparable`), never bolted onto
  `schemas/envelope.py`'s 5-state field enum.

### Comparability verdict authority — the reliability keystone (COMPARE-02)
- **D-03:** **Model judges, code guards (clamp-to-ceiling).** The model proposes a per-dimension
  verdict + reason; **code computes a comparability ceiling deterministically from the
  `ExtractionResult` flag states and can ONLY downgrade** the model's verdict, never upgrade it.
  This mirrors the EXTRACT-04 grounding gate ("code disproves the model", CLAUDE.md §2) at the
  comparison level — the phase's headline reliability move.
- **D-04:** **Ceiling rule (the clamp).** Per dimension, across the vendors being compared: any
  `missing` / `unsupported` on a contributing field caps the verdict at `not_comparable`;
  `unclear` / `conflicting` caps at `partially`; all contributing fields `present` + grounded
  allows `comparable`. The model's verdict is `min(model_verdict, code_ceiling)`. **Exact
  field→dimension contribution map and threshold tuning = planner/research detail** (within this
  rule). The agent **never aggregates over a field a vendor is missing** (COMPARE-02).

### Alignment vs normalization boundary (COMPARE-04)
- **D-05:** **Surface as-is, ZERO reconciliation.** Offers are already pinned to the 8 RFQ line
  items by `line_item_id` at extraction time (P3 D-01). Comparison **surfaces** each vendor's
  verbatim offer + evidence side by side. It does **NOT** convert currency, split bundles, reconcile
  units/labels, or compute a normalized unit price. Where offers aren't truly equivalent, it
  **flags non-equivalence** ("bundled — not separable", "quoted EUR vs USD") rather than forcing
  parity. Honors §24 (no heavy normalization) — the §21 differentiator.

### Output surfaces (COMPARE-04/05)
- **D-06:** **Two complementary surfaces.** (1) the 6-dimension comparability matrix (headline,
  D-01), and (2) an **8-line-item × vendor offer table** showing each vendor's verbatim
  pricing/scope-coverage per item with missing/unclear/bundled badges. Surface (2) is where
  COMPARE-04 "surface differences" visibly pays off.
- **D-07:** **Per-vendor readiness summary — qualitative, with an X/N count, never sorted.** A
  per-vendor readiness descriptor (e.g. "4 of 6 dimensions currently comparable; blocked on
  commercial, compliance") is included. **Guardrail (mandatory):** the count is framed as a
  *data-readiness* indicator, weights all dimensions equally (no implied priority), is **NOT** a
  weighted quality score, and **vendors are NEVER sorted or ordered by readiness** — render order is
  always stable (input order). Ordering by readiness = the leaderboard §24 forbids.
  > Note: the user chose the X/N count over the leaner "dimension-list, no count" recommendation,
  > accepting the residual implicit-rank risk; the never-sort + data-readiness framing is the
  > guardrail that keeps it defensible against §24/COMPARE-05.

### Buyer attention points (COMPARE-03)
- **D-08:** **Code-triggered, model phrases.** Code deterministically detects attention triggers
  from flags + extraction (comparability blockers, fields conflicting across vendors, missing
  critical pricing, weak/absent compliance); the model only writes the buyer-facing phrasing. Same
  posture as the verdict guard — **code decides WHAT matters, model decides HOW to say it.** The
  panel cannot surface a point the data doesn't support.

### Clarification questions (COMPARE-03/05)
- **D-09:** **Separate cheap-tier call, code-seeded.** Code collects the flagged fields
  (`missing | unclear | conflicting | unsupported`) from the `ExtractionResult[]` **deterministically**,
  then a **gpt-5.4-mini** `clarification.v1.md` call drafts the questions. The model never invents
  the input set; it only phrases questions for code-supplied flagged fields. Reuses the reserved
  `clarification.v1.md` stub.
- **D-10:** **One grounded question per flagged field, buyer-prioritized.** Each question names the
  vendor, line item, and exact ambiguity (per `clarification.v1.md`'s design); **no arbitrary cap**
  (dropping gaps violates "absence is first-class"). Questions are ordered comparability-blockers
  first and grouped by vendor for sending. Generic questions ("please clarify pricing") are
  rejected.

### Trace deliverable (PROMPT-03 continuation)
- **D-11:** **≥1 comparison trace capturing the verdict-clamp diff.** JSON + rendered Markdown under
  `docs/traces/` (same shape as P3): input `ExtractionResult[]` → resolved prompt (id+version) →
  RAW model verdicts → **code-clamped verdicts (the downgrade diff)** → final `ComparisonResult` +
  clarification set. This is the phase's literal "code disproves the model" proof and feeds the P5
  in-app trace viewer with no rework. Must be **compelling to an Aerchain reviewer**, not just
  structurally valid (carried-forward P3-UAT quality gate).

### Claude's Discretion (within the decisions above)
- **Call strategy:** single structured-output comparison call over **all vendors at once** (true
  side-by-side reasoning needs every extraction in one context) is the assumed approach; a
  **sectioned / per-dimension split is a researched contingency built ONLY if truncation is
  observed** — not speculatively (mirrors P3 D-06, §2 YAGNI).
- **Dimension derivation:** mapping the 6 dimensions onto `ExtractionResult` fields (e.g. technical
  capability ← `scope_summary` + per-item `scope_coverage`; commercial ← `commercial_terms` +
  pricing; risk ← `risks[]`; compliance ← `compliance_points[]`; timeline ← `timeline`).
- **Streaming:** reuse the P3 SSE spine — `status` events (`align → comparability → compare →
  clarify → done`) + a final grounded `result` event. **Never stream a pre-clamp verdict** as if
  final (honors evidence-over-assertion; the guard runs server-side before the SSE boundary, like
  P3 D-07).
- **Exact `ComparisonResult` / sub-model field names**, the field→dimension contribution map, and
  the attention-trigger detection thresholds — within D-01..D-11.
- **Number of comparison traces** (≥1 required; capture more if a richer set tells the story better,
  per P3 D-12 precedent).
- **Code-level test structure** — must assert: the clamp only downgrades (a model "comparable" over
  a missing field becomes `not_comparable`); no aggregation over missing fields; clarification set
  is derived from code-collected flags (not model-invented); attention points trace to a real
  trigger; vendors never reordered by readiness.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of truth (the brief & rubric)
- `docs/assignment.md` — §22 rubric (Product thinking in comparison 15%, Prompt quality 30%),
  §24 anti-patterns (no misleading comparisons, no heavy normalization, never ignore
  missing/contradictory info, no unsupported claims), §21 differentiators (light-vs-heavy
  normalization, qualitative comparability signal).

### Product vision & reliability rules
- `CLAUDE.md` §1 — product principles (**comparability before ranking**, evidence over assertion,
  absence first-class, refuse misleading apples-to-oranges comparisons).
- `CLAUDE.md` §2 — never trust an LLM-supplied `verified`/authorization flag; grounding/guards
  enforced in code (the basis for D-03 verdict clamp, D-08 attention triggers, D-09 clarification
  seeding).
- `CLAUDE.md` §5 — comparison agent job (establish comparability first, surface attention points +
  clarifications, never mislead); LLM tier discipline (gpt-5.4 reasoning / gpt-5.4-mini cheap,
  never 5.5); structured output via pydantic JSON-schema; SSE streaming; LangChain/LangGraph only.
- `CLAUDE.md` §7 — Prompt Pack & traceability (per-prompt what/why/failure-handling; ≥1 trace).
- `CLAUDE.md` §8 — absence states surfaced never silently filled.

### Planning inputs
- `.planning/PROJECT.md` — product framing, constraints, Out of Scope (no weighted/numeric scoring,
  no should-cost engine, no heavy normalization).
- `.planning/REQUIREMENTS.md` — COMPARE-01..05 are this phase's mandated reqs (Comparison = 15%);
  Out of Scope table (quantitative should-cost, weighted scoring, heavy normalization).
- `.planning/ROADMAP.md` §"Phase 4" — the 5 success criteria this phase must make TRUE, and the
  research note (comparability-signal representation + light-vs-heavy normalization boundary — both
  resolved above in D-01/D-05/D-06).
- `.planning/STATE.md` — carried-forward concerns that come due here:
  - **WR-01** (`not-comparable` representation) — resolved by D-02.
  - **Prompt-quality peer review** carry-forward — applies to `comparison.v1.md` +
    `clarification.v1.md` (30% of grade).
  - **Trace/demo readability** carry-forward — applies to the D-11 comparison trace.
- `.planning/phases/03-extraction-agent/03-CONTEXT.md` — the `ExtractionResult` shape comparison
  consumes (D-01 per-line-item `LineItemExtraction`, D-02 bundled-pricing handling, D-03 multi-claim
  `list[Field]`), the grounding boundary (D-07), the single-call + SSE patterns comparison mirrors
  (D-06, D-07), the trace shape (D-13/D-14).
- `.planning/phases/02-grounding-gate-messy-data/02-CONTEXT.md` — the grounding-gate contract and the
  3 messy personas whose flag states drive the comparability ceiling (D-04) and clarification
  seeding (D-09).

### Existing code the phase builds on / extends
- `services/ai/schemas/domain.py` — `ComparisonResult` stub (2 fields) to flesh out (D-01/D-06/D-07);
  read-only inputs `ExtractionResult` (incl. `LineItemExtraction`, all `Field[T]` / `list[Field]`
  shapes), `RFQ.line_items`. **No `dict[str, Field]` shapes** (P3 D-04 constraint holds).
- `services/ai/schemas/envelope.py` — `Field[T]`, `FlagStatus` (5-state field enum — read to compute
  the D-04 ceiling; **do NOT add `not-comparable` here**, per D-02), `Evidence`, `ConflictingValue`.
- `services/ai/schemas/events.py` — `EventEnvelope` `{type, payload}`, closed `EVENT_TYPES`,
  `ErrorPayload` (truncation/refusal handling mirrors P3 D-08).
- `services/ai/grounding/gate.py` / `report.py` — the gate contract + `DowngradeReport` pattern the
  D-03 verdict clamp parallels (a comparison-level downgrade report rides the result payload + trace).
- `services/ai/llm/factory.py` — `get_llm("reasoning")` (comparison call) and `get_llm("cheap")`
  (D-09 clarification call) + `.with_structured_output(..., method="json_schema")`.
- `services/ai/agents/extraction.py` (P3 `StateGraph`) + `services/ai/agents/_demo.py` — the
  LangGraph + `get_stream_writer()` + `astream(stream_mode="custom")` pattern the comparison graph
  follows.
- `services/ai/api/app.py` — the `EventSourceResponse` SSE route pattern (validate each chunk through
  `EventEnvelope` before serializing; append final `done`). The comparison endpoint takes
  `(ExtractionResult[], RFQ)`.
- `services/ai/prompts/comparison.v1.md` + `clarification.v1.md` — the TODO stubs to author in full;
  `services/ai/prompts/registry.py` — `load("comparison")` / `load("clarification")` by id.
- `docs/traces/` — existing P3 trace JSON+MD shape the D-11 comparison trace matches.

### Contract discipline
- Fleshing out `ComparisonResult` MUST regenerate `packages/shared-types` and pass the codegen
  drift-check test (PLAT-02). Generic `Field[T]` needs the `# noqa: UP046` pattern for pydantic2ts.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ExtractionResult` (`domain.py`) — the sole input; all values already carry grounded evidence, so
  comparison cites them transitively without re-grounding (COMPARE-01).
- `FlagStatus` (`envelope.py`) — read per contributing field to compute the D-04 comparability
  ceiling in code.
- `get_llm("reasoning")` (comparison) + `get_llm("cheap")` (clarification) with
  `.with_structured_output(Schema, method="json_schema")` (`factory.py`).
- P3 extraction `StateGraph` + `get_stream_writer()` + `EventSourceResponse` route — the SSE spine
  the comparison graph reuses.
- `DowngradeReport` / `DowngradeEntry` (`report.py`) — the pattern for a comparison-level
  verdict-clamp report (rides the result payload + the D-11 trace).
- Prompt registry `load(id)` + the reserved `comparison.v1.md` / `clarification.v1.md` frontmatter.

### Established Patterns
- pydantic schemas are the contract source; any `ComparisonResult` change regenerates
  `shared-types` + passes the drift-check (PLAT-02).
- Code-enforced guards over LLM self-attestation (grounding gate → here, the verdict clamp,
  attention triggers, and clarification seeding all decide in code).
- Every SSE chunk validated through `EventEnvelope(**chunk)` BEFORE serialization.
- `# ponytail:` comments mark deliberate kept-complexity; `# noqa: UP046` on generic pydantic models.

### Integration Points
- Comparison is the seam between Phase 3 (`ExtractionResult[]` it consumes) and Phase 5 (the Vendor
  Comparison screen renders the matrix + line-item table; the in-app trace viewer renders the D-11
  comparison trace JSON).
- Inputs: the 3 committed sample vendors' extractions + live-generated equivalents, plus the RFQ.
- The comparison SSE endpoint `(ExtractionResult[], RFQ)` is consumed by the P5 Comparison screen.
</code_context>

<specifics>
## Specific Ideas

- The phase's headline rubric story is the **verdict-clamp diff** (D-03/D-11): the raw model verdict
  vs the code-downgraded verdict is the literal proof that *code*, not the model, decides
  comparability — the comparison-level echo of the grounding gate.
- "Comparability before ranking" is enforced structurally: there is **no ranking at all** — no
  numeric score, no weighted total, and vendors are never sorted (D-07). The qualitative signal IS
  the product.
- The 8-line-item × vendor table (D-06) is where the §21 "light alignment, differences surfaced"
  differentiator is visible: bundled/missing/EUR-vs-USD cells are flagged, never reconciled (D-05).
- Both prompts (`comparison.v1.md`, `clarification.v1.md`) carry the deferred **prompt-quality peer
  review** gate (30% of grade) and the comparison trace carries the **trace/demo readability** gate.

</specifics>

<deferred>
## Deferred Ideas

- **Sectioned / per-dimension comparison call** — held as a *researched contingency* (Claude's
  Discretion), built only if single-call truncation over all vendors is observed; not a separate
  phase.
- **Vendor Comparison screen / line-item table UI / in-app comparison-trace viewer** — Phase 5
  (UI-04, UI-05); Phase 4 produces the `ComparisonResult` data + the committed trace artifact they
  render.
- **Weighted/numeric scoring, should-cost engine, currency reconciliation** — permanently out of
  scope (REQUIREMENTS Out of Scope; §24). Not deferred to a later phase — excluded by design.
- **Stateful clarification → re-extraction feedback loop** (buyer sends clarifications, vendor
  replies, re-run) — v2 (FLOW-01/FLOW-02), not this prototype.

None of the above is lost; each is anchored to its owning phase or explicitly excluded.

</deferred>

---

*Phase: 4-Comparison Agent*
*Context gathered: 2026-06-28*
