# Phase 3: Extraction Agent - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Per-vendor extraction reads one `VendorResponse.raw_text` and produces a structured
`ExtractionResult` (scope, pricing, commercial terms, timeline, compliance, assumptions,
exclusions, risks) where **every fact carries an evidence snippet that passes the Phase-2 grounding
gate**, absence is flagged in four states and **never filled**, structured output is handled safely
under strict mode (truncation/refusal = hard errors, never parsed), progress streams over SSE
(never buffer-and-return), and **3–5 complete prompt traces** are captured.

**In scope (EXTRACT-01/02/03/05, PROMPT-03):**
- Flesh out the `ExtractionResult` schema (currently a 3-field stub) into the real per-vendor shape.
- The extraction agent: the first real LangGraph `StateGraph` — call → ground → emit over SSE.
- The `extraction.v1.md` prompt (currently a TODO stub) authored in full (Prompt Pack).
- Code-enforced grounding wired per-fact onto extraction output (`ground_model`), with the
  downgrade report surfaced.
- Strict-mode safety: `finish_reason: length` (truncation) and `refusal` treated as hard errors.
- 3–5 captured traces (JSON + rendered Markdown) under `docs/traces/`.

**Out of scope (later phases):**
- Comparison / comparability / cross-vendor logic — Phase 4.
- **Clarification question generation** — Phase 4 (COMPARE-05); `clarification.v1.md` stays untouched.
- Buyer UI / Extraction Review screen / in-app trace viewer / file upload — Phase 5.
- CORS / deploy / proxy-buffering config — Phase 5.
</domain>

<decisions>
## Implementation Decisions

### Schema shape & RFQ-awareness (EXTRACT-01)
- **D-01:** **RFQ-aware hybrid extraction.** The extraction call receives the RFQ's 8 line items as
  scaffold. Per line item, extract pricing + scope-coverage as `Field[T]` — so a vendor that did not
  bid an item surfaces as `missing` **at extraction time** (the strongest "absence is first-class"
  signal; you cannot distinguish *missing* from *not-asked* without knowing the RFQ). Cross-cutting
  categories (commercial terms, timeline, compliance, assumptions, exclusions, risks) extracted at
  document level. Phase 4 then *compares* aligned structures + keeps originals visible — it does not
  do the initial structuring.
- **D-02:** **Bundled / cross-item pricing → document-level field + per-item `unclear`.** Keep a
  document-level `pricing_structure` (and/or stated grand `total_price`) `Field[T]` capturing the
  bundle verbatim with evidence, AND mark affected per-line-item pricing as `unclear`
  ("bundled, not separable"). **Never force a per-item split** (§24 no-heavy-normalization; splitting
  fabricates numbers the vendor never stated). Gives Phase 4 both views.
- **D-03:** **Per-claim grounding where natural.** Multi-claim categories — risks, assumptions,
  exclusions, compliance points — are `list[Field[T]]` so EACH claim carries its own evidence and
  can independently downgrade to `unsupported`. Narrative categories — scope_summary, timeline,
  commercial_terms — stay a single `Field[str]`. Strongest "every fact has evidence" (EXTRACT-02)
  without fragmenting prose or inflating output.
- **D-04:** **Schema uses `list[BaseModel]` / `list[Field]` shapes only — NO `dict[str, Field]`.**
  This is a hard constraint: it closes the carried-forward IN-04 gap (the grounding walker
  `_walk_and_ground` does not traverse dict-valued Field containers) *by design*, so no grounded
  field is ever silently bypassed. The planner must verify the final shape against the walker's
  coverage (nested model / `list[Field]` / `list[BaseModel]`).
- **D-05:** **`vendor_name` is plain `str` carried from provenance, NOT a grounded `Field`.** It is
  known metadata (`VendorResponse.vendor_name` / persona), not a fact extracted from messy text;
  grounding a known name against `raw_text` could spuriously fail. Correct the stub
  (`vendor_name: Field[str]` → `vendor_name: str`). Reserve `Field[T]`+grounding for actual extracted
  claims.

### Call strategy, streaming & strict-mode safety (EXTRACT-05)
- **D-06:** **Single grounded structured-output call per vendor.** One
  `get_llm("reasoning").with_structured_output(...)` call → cleanest trace, one grounding pass,
  simplest graph. The schema is compact enough (D-03 avoided over-fragmenting) to fit one gpt-5.4
  call for one vendor. **Sectioned 2-call split (line-items call + cross-cutting call, merged into
  one `ExtractionResult`) is a *researched contingency* — built ONLY if research/testing shows
  truncation, not speculatively** (§2 YAGNI).
- **D-07:** **Grounding runs server-side BEFORE the SSE boundary; only grounded data crosses.**
  Stream `status` events for phase progress (start → model call → grounding → done). The buyer
  receives the fully-grounded `result` event (with the downgrade report in the payload) — and, only
  if sectioned, grounded-section `partial`s. **Never stream ungrounded/partial facts** as if real
  (honors "evidence over assertion" — no flashing a number the gate later suppresses).
- **D-08:** **Truncation / refusal = hard error, never parsed.** `finish_reason: length` → `error`
  event `{code, message, recoverable: true}` (auto-retry sectioned once if the D-06 fallback exists,
  before surfacing). `refusal` → `error` `{recoverable: false}`, hard stop for that vendor. The
  vendor's extraction fails cleanly rather than yielding a half-parsed object. Uses the P1 D-10
  `error` event taxonomy.

### Prompt design — flag posture & evidence (PROMPT-03; 30%-of-grade prompt quality)
- **D-09:** **Humility-biased posture; model uses ONLY 4 states.** The prompt biases toward honesty:
  prefer `unclear` over a confident `present` on fuzzy/ambiguous values; `missing` over inventing;
  `conflicting` whenever two statements genuinely disagree (each side captured in `values[]`).
  Explicit decision rule + a few-shot example per state. **Critical division of labor: the model
  only ever assigns `present | missing | unclear | conflicting`. `unsupported` is the GATE's
  code-only verdict — the prompt never mentions it** (never trust a model "verified" flag, §2/§8).
  Never emit a value without a verbatim snippet (the envelope `model_validator` also enforces this).
- **D-10:** **Model supplies verbatim snippet + `source_id` only; the gate computes offsets.** A
  lean model-facing extraction schema asks for the snippet text + `source_id`, NOT
  `char_start`/`char_end` — the gate locates the snippet and computes real offsets anyway (P2 D-01,
  "search & recompute, never trust model offsets"). Saves output tokens on every snippet → lowers
  truncation risk (D-08). Implies a model-facing schema mapped into the canonical `ExtractionResult`
  (which keeps offsets for UI highlighting) during grounding. **The prompt hammers: quote VERBATIM,
  never paraphrase evidence** — so normalized-exact match succeeds and we rarely fall to fuzzy.
- **D-11:** **Extraction only flags; it does NOT author clarification questions.** Clarifications are
  Phase 4 (COMPARE-05, cross-vendor) — keeps the boundary clean (extraction = grounded facts + flags;
  comparison = comparability + clarifications) and avoids touching `clarification.v1.md` early.

### Prompt trace deliverable (PROMPT-03)
- **D-12:** **3–5 traces, not one.** Capture **one trace per sample vendor (3)** so the set
  collectively exhibits every flag type (cheap-but-incomplete → `missing`; polished-fluff →
  `conflicting`; thorough-but-pricey → bundled/`unclear`), **plus 1–2 traces specifically showcasing
  a real code-enforced downgrade to `unsupported`.** The submission presents a *body* of traces, not
  a single cherry-picked example.
- **D-13:** **Committed JSON (source) + rendered Markdown (human) under `docs/traces/`.** Phase 5's
  in-app trace viewer consumes the same JSON — no rework.
- **D-14:** **Each trace captures the full pipeline incl. the raw-vs-grounded diff:** (1) input
  (vendor `raw_text` + RFQ line items), (2) resolved prompt with id+version, (3) RAW model output —
  the ungrounded result as returned, (4) the grounding step + downgrade report, (5) final grounded
  `ExtractionResult`. Showing raw-vs-grounded side by side is the literal proof that *code*, not the
  model's word, decides what's shown.
- **D-15:** **≥1 trace MUST show a genuine downgrade** (from real runs on the committed messy
  samples — never staged/fabricated). Bonus: if NO natural downgrade ever occurs, that signals the
  fuzzy threshold (90) is over-accepting — so the trace set doubles as the carried-forward Phase-2
  **fuzzy-threshold calibration evidence**.

### Claude's Discretion
- Exact `ExtractionResult` / `LineItemExtraction` field names and the model-facing→canonical schema
  mapping (within D-01..D-05 + the D-04 no-dict constraint).
- The extraction `StateGraph` node structure, function signatures
  (`generate_extraction(vendor_response, rfq)` shape), and the SSE endpoint surface (a per-vendor
  endpoint taking `(vendor_response, rfq)` is the assumed contract; multi-vendor orchestration is a
  loop, likely driven by the P5 UI).
- Whether a stated grand `total_price` is its own doc-level grounded `Field[Decimal]` distinct from
  `pricing_structure` (assumed yes).
- Prompt few-shot example selection, ordering of instructions, and exactly how the RFQ line items are
  injected (structured titles+descriptions, not the whole RFQ doc, to save tokens — assumed).
- Code-level test structure (must assert: no fabricated fields — every `present` fact has locatable
  evidence; missing/unclear/conflicting surfaced; truncation/refusal raise, never parse).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of truth (the brief & rubric)
- `docs/assignment.md` — §22 rubric (Extraction accuracy & reliability 20%, Prompt quality 30%),
  §24 anti-patterns (no unsupported claims, no heavy normalization, never ignore
  missing/contradictory info), §11 (best-effort extraction).

### Product vision & reliability rules
- `CLAUDE.md` §1 — product principles (evidence over assertion, absence first-class, no hallucinated
  claims, comparability before ranking).
- `CLAUDE.md` §8 — AI reliability: every fact marked present/missing/unclear/conflicting/unsupported,
  surfaced never silently filled.
- `CLAUDE.md` §2 — never trust an LLM-supplied `verified`/`grounded` flag; grounding enforced in code.
- `CLAUDE.md` §5 — LLM tier discipline (gpt-5.4 reasoning, never 5.5), structured output via pydantic
  JSON-schema, SSE streaming, LangChain/LangGraph only.
- `CLAUDE.md` §7 — Prompt Pack & traceability (per-prompt what/why/failure-handling; ≥1 reproducible
  trace).

### Planning inputs
- `.planning/PROJECT.md` — product framing, constraints, key decisions.
- `.planning/REQUIREMENTS.md` — EXTRACT-01/02/03/05 + PROMPT-03 are this phase's mandated reqs
  (EXTRACT-04 grounding gate already landed in Phase 2).
- `.planning/ROADMAP.md` §"Phase 3" — the 5 success criteria this phase must make TRUE, and the
  research note (strict structured-output edge cases + LangGraph v2 stream→SSE mapping).
- `.planning/STATE.md` — carried-forward Phase-2 review concerns that come due here (IN-04 walker
  coverage; fuzzy-threshold calibration; FlagStatus/`not-comparable` is a Phase-4 concern, NOT a
  per-field status).
- `.planning/phases/02-grounding-gate-messy-data/02-CONTEXT.md` — the grounding-gate contract
  (D-01 search-&-recompute, D-05/06/07 gate API + dict[source_id]→text input) extraction plugs into;
  the 3 personas (D-10) extraction must produce flags for.
- `.planning/phases/01-foundation/01-CONTEXT.md` — envelope (D-04..D-07), SSE taxonomy (D-09/D-10
  error event), LLM tier factory (D-15), prompt format (D-11/D-12).

### Existing code the phase builds on / extends
- `services/ai/schemas/domain.py` — `ExtractionResult` stub to flesh out (D-01..D-05); `RFQ` /
  `VendorResponse` (read-only inputs: `RFQ.line_items`, `VendorResponse.raw_text` / `source_id` /
  `vendor_name`).
- `services/ai/schemas/envelope.py` — `Field[T]`, `Evidence`, `ConflictingValue`, `FlagStatus`; what
  extraction emits and what the gate enforces (`unsupported` forbids value/evidence).
- `services/ai/schemas/events.py` — `EventEnvelope` `{type, payload}`, closed `EVENT_TYPES`,
  `ErrorPayload` `{code, message, recoverable}` (D-08 maps here).
- `services/ai/grounding/gate.py` — `ground_field`, `ground_model`, `_walk_and_ground` (the seam
  extraction calls post-model; verify D-04 shape coverage). `services/ai/grounding/report.py` —
  `DowngradeReport` / `DowngradeEntry` (rides in the result payload + the trace).
- `services/ai/llm/factory.py` — `get_llm("reasoning")` + `.with_structured_output(..., method="json_schema")`.
- `services/ai/agents/_demo.py` — the LangGraph `StateGraph` + `get_stream_writer()` +
  `astream(stream_mode="custom")` pattern extraction follows (it's the first *real* such graph).
- `services/ai/agents/rfq_gen.py` / `vendor_gen.py` — the prompt-load + chain-invoke pattern (plain
  chains, no graph — extraction differs by being a streaming graph).
- `services/ai/api/app.py` — the `EventSourceResponse` SSE route pattern (validate each chunk through
  `EventEnvelope` before serializing; append final `done`).
- `services/ai/prompts/extraction.v1.md` — the TODO stub to author in full.
  `services/ai/prompts/registry.py` — `load("extraction")` by id, filename versioning.

### Contract discipline
- Fleshing out `ExtractionResult` MUST regenerate `packages/shared-types` and pass the codegen
  drift-check test (P1 D-14 / PLAT-02). Generic `Field[T]` needs the `# noqa: UP046` pattern for
  pydantic2ts (see envelope.py).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Field[T]` / `Evidence` / `ConflictingValue` / `FlagStatus` (`envelope.py`) — extraction emits
  these; the `model_validator` already forbids `unsupported`+value/evidence, so the gate's downgrade
  is just setting `status=unsupported`.
- `ground_model(obj, sources)` (`gate.py`) — schema-agnostic walker; extraction calls it post-model
  with `sources={vendor_response.source_id: vendor_response.raw_text}`. Returns
  `(grounded_obj, DowngradeReport)`.
- `get_llm("reasoning").with_structured_output(Schema, method="json_schema")` — returns a validated
  pydantic instance directly (see `rfq_gen.py`).
- `_demo.py` graph + `get_stream_writer()` + `EventSourceResponse` route (`api/app.py`) — the
  end-to-end SSE spine extraction reuses.
- Prompt registry `load(id)` (`registry.py`) + `extraction.v1.md` frontmatter scaffold.

### Established Patterns
- pydantic schemas are the contract source; any `ExtractionResult` change regenerates
  `shared-types` + passes the drift-check (P1 D-14).
- `# ponytail:` comments mark deliberate kept-complexity; `# noqa: UP046` on generic pydantic models.
- Every chunk from the graph is validated through `EventEnvelope(**chunk)` BEFORE serialization —
  a malformed emit fails at validation, never streams to the client.

### Integration Points
- Extraction is the seam between Phase 2 (gate + messy data it consumes) and Phase 4 (comparison
  consumes `ExtractionResult[]` only — never raw text; the grounding boundary holds transitively).
- The extraction SSE endpoint is consumed by the P5 Extraction Review screen; the trace JSON feeds
  the P5 in-app trace viewer.
- Inputs: the committed sample RFQ + the 3 committed sample vendor responses (Phase 2 `data/`), and
  live-generated equivalents.
</code_context>

<specifics>
## Specific Ideas

- "Code disproves the model" is the phase's headline: the raw-vs-grounded diff in each trace (D-14)
  and a real `unsupported` downgrade (D-15) are the literal proof for the rubric.
- The 3 Phase-2 personas were designed to exercise every flag type — extraction's traces should make
  that visible across the set (D-12): cheap→`missing`, fluff→`conflicting`, thorough→bundled/`unclear`.
- The single most important prompt instruction is **verbatim quoting of evidence** (D-10) — it is
  what makes the grounding gate's normalized-exact match succeed and keeps fuzzy a rare fallback.
- The trace set doubles as fuzzy-threshold calibration evidence — the carried-forward Phase-2 task
  closes here as a by-product (D-15).

</specifics>

<deferred>
## Deferred Ideas

- **Sectioned multi-call extraction** — held as a *researched contingency* (D-06), built only if
  single-call truncation is observed; not a separate phase.
- **Clarification question generation** — Phase 4 (COMPARE-05); extraction only flags (D-11).
- **`not-comparable` representation** — comparison-level, Phase 4 (carried Phase-2 review WR-01); do
  NOT bolt it onto the field-level `FlagStatus` enum.
- **Extraction Review screen / in-app trace viewer / file upload** — Phase 5 (UI-03, PROMPT-02,
  INPUT-02); Phase 3 produces the data + the committed trace artifacts they render.
- **Streaming token-level partial fields to the UI** — rejected on reliability grounds (D-07); could
  revisit only if a grounded-section streaming model is designed.

None of the above is lost; each is anchored to its owning phase.

</deferred>

---

*Phase: 3-Extraction Agent*
*Context gathered: 2026-06-27*
