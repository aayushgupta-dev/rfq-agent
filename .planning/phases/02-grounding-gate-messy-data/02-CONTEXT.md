# Phase 2: Grounding Gate & Messy Data - Context

**Gathered:** 2026-06-27
**Status:** Ready for planning

<domain>
## Phase Boundary

The reliability keystone — **code that disproves the model** — built and unit-tested in
isolation (no LLM, no extraction agent), plus deliberately messy RFQ/vendor data realistic
enough to be worth testing it against.

**In scope:**
- **Grounding gate (EXTRACT-04):** a pure, LLM-free module that verifies every `Evidence` snippet
  actually exists in the vendor source text; locates it (normalized exact → high-threshold fuzzy),
  recomputes real offsets, and downgrades unlocatable facts to `unsupported` with value + evidence
  suppressed. Unit-tested directly.
- **RFQ generation (DATA-01):** structured marketing-services RFQ (8 line items, scope, timelines,
  commercial expectations, questionnaire, compliance) + a rendered Markdown doc. Flesh out the
  `RFQ` schema from its Phase-1 stub.
- **Vendor response generation (DATA-02/03):** 3 deliberately messy vendor responses, one-pass from
  a persona + a hand-authored mess spec, emitted as raw messy text + provenance metadata. Flesh out
  the `VendorResponse` schema to carry raw text + provenance (not pre-extracted fields).
- **Sample data + live regen (DATA-04):** commit the generated RFQ + 3 vendor responses as sample
  fixtures AND keep them regenerable live in-app.
- **Messiness tests (DATA-03):** assert each persona's declared issue types are detectable in the
  committed samples.
- **Prompt work (PROMPT-04):** author the `rfq-gen`, `vendor-gen`, `messy-data-gen` prompts;
  capture ≥1 documented prompt failure + fix + versioning/eval notes.

**Out of scope (later phases):** the extraction agent itself (P3 — only the gate's *contract* lands
here), comparison (P4), buyer UI / RFQ Overview rendering / file upload (P5). `ExtractionResult` and
`ComparisonResult` schemas stay Phase-1 stubs.
</domain>

<decisions>
## Implementation Decisions

### Grounding match strategy (EXTRACT-04)
- **D-01:** **Search & recompute, never trust model offsets.** The gate ignores the model-supplied
  `char_start`/`char_end`, searches the source text for the snippet, and on a hit recomputes the
  REAL offsets and overwrites the model's. Makes D-04 ("offsets validated in code, never trusted")
  literally true and guarantees the UI highlight always points at a span that exists.
- **D-02:** **Moderate normalization** before matching: collapse whitespace/newlines, case-fold,
  Unicode NFKC, normalize smart quotes & dashes — but keep letters/digits/currency symbols intact.
  Deliberately NOT aggressive (no full punctuation/symbol stripping), which would let `$1,200`≈`1200`
  or `Q3`≈`Q 3` collapse and let a fabricated value match a real one.
- **D-03:** **Fuzzy fallback = `rapidfuzz.partial_ratio` (substring-aware) over a sliding window,
  accept only at ~90/100.** Fires only when normalized-exact misses. Exact threshold is tuned in
  tests against the real messy samples. `rapidfuzz` is a new `services/ai` dependency (MIT, the
  de-facto Python fuzzy lib) — assumed fine.
- **D-04 (flagged for research):** recomputing offsets means mapping a match found in *normalized*
  space back to *original* source indices — a known implementation wrinkle the planner/researcher
  must solve (normalization changes string length). Not a user decision.

### Grounding gate contract (the seam Phase 3 plugs into)
- **D-05:** **Pure single-field core + schema-agnostic walker.** `ground_field(field, sources)`
  handles ONE `Field[T]` (including the `conflicting` `values[]` case); a separate walker
  recursively finds & re-grounds every `Field[T]` in any pydantic object. The walker works without
  knowing `ExtractionResult`'s shape (undefined until P3), so the gate is unit-testable in isolation
  now.
- **D-06:** **Pure function — return new + downgrade report.** Returns a NEW object with failed
  fields set to `status=unsupported, value=None, evidence=[]` (the envelope already forbids
  `unsupported`+value/evidence), AND a structured downgrade report (field path, original status,
  reason). Report feeds tests now and the prompt-trace/UI later. No in-place mutation.
- **D-07:** **Source supplied as `dict[str, str]` keyed by `Evidence.source_id`.** Honors the
  multi-source design already baked into the schema; a single vendor is a one-entry map.

### Vendor-gen pipeline (DATA-02/03)
- **D-08:** **One-pass generation.** `vendor-gen(RFQ, persona, mess_spec)` emits the messy response
  directly — real vendors are organically messy, not clean docs that got vandalized; fewer LLM
  calls. `messy-data-gen` is repurposed as the shared **issue-type taxonomy/reference** the prompt
  embeds (keeps the Prompt Pack slot meaningful + documented for PROMPT-04), NOT a second transform
  pass.
- **D-09:** **Mess specs are hand-authored in code** (one per persona, e.g.
  `[{line_item, issue_type, instruction}]`). Because we know exactly what was injected, DATA-03
  tests can assert each issue type is present. Deterministic & reproducible (vs. LLM-chosen, which
  can't be asserted).
- **D-10:** **Exactly 3 complementary personas** (ROADMAP minimum), each a distinct failure profile
  so extraction/comparison demos hit every flag type:
  1. thorough-but-pricey — bundled / over-scoped pricing,
  2. cheap-but-incomplete — missing line items + vague timelines,
  3. polished fluff — internal CONFLICTS + weak compliance.

### Generated document shape (DATA-01/02/04)
- **D-11:** **RFQ = structured + rendered.** `rfq-gen` emits a STRUCTURED `RFQ` (pydantic: 8 line
  items, scope, timelines, commercial expectations, questionnaire, compliance) via structured
  output, AND we render it to a readable Markdown doc. The RFQ is our own clean artifact (never
  grounded against), so structure powers the P5 Overview screen and comparison line-item alignment
  for free. **Flesh out the `RFQ` schema this phase.**
- **D-12:** **Vendor response = raw messy text + provenance.** `VendorResponse` carries the raw
  messy document TEXT (Markdown/plain prose) plus metadata (`vendor_name`, `persona`, `mess_spec`,
  `source_id`, `format_label`) — NOT pre-extracted structured fields. The raw text IS the extraction
  input we ground against. The 3 vendors deliberately differ in format (letter/email vs tabular
  proposal vs deck-style outline).

### Messiness testing (DATA-03)
- **D-13:** **Assert on committed samples.** Tests run against the COMMITTED sample fixtures
  (deterministic, fast, CI-safe) and assert each persona's declared issue types are detectable
  (a missing-price line item really has no number; a conflicting field really has two values). Live
  regeneration is a separate smoke path, NOT content-asserted (avoids LLM-nondeterminism flake +
  CI API cost).

### Prompt Pack (PROMPT-04)
- **D-14:** Capture ≥1 documented prompt failure example + the fix by harvesting a real failure
  encountered while authoring `vendor-gen`/`rfq-gen`, documented in the Prompt Pack docs alongside
  versioning/eval notes. (Assumed approach — open to refinement at planning.)

### Claude's Discretion
- Module layout within `services/ai` for the gate (e.g. `services/ai/grounding/`), exact function
  names/signatures beyond the contract shape in D-05–D-07, and the report data structure.
- The precise normalization pipeline ordering and the exact fuzzy threshold (tuned in tests, D-03).
- Persona prose styles / format-divergence details beyond the 3 failure profiles in D-10.
- How sample fixtures are stored under `data/` and the live-regen API surface (within DATA-04).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of truth (the brief & rubric)
- `docs/assignment.md` — the brief; §22 rubric (Data generation 20%, Extraction reliability 20%),
  §24 anti-patterns (no unrealistically clean data, no heavy normalization, never ignore
  missing/contradictory info), §11 (best-effort extraction).

### Product vision & reliability rules
- `CLAUDE.md` §1 — product principles (evidence over assertion, absence first-class, no hallucinated
  claims).
- `CLAUDE.md` §8 — AI reliability: grounding enforced in code, never on the model's word.
- `CLAUDE.md` §2 — engineering principles; never trust an LLM-supplied `verified`/`grounded` flag.
- `CLAUDE.md` §7 — Prompt Pack & traceability (PROMPT-04 failure example + versioning notes).

### Planning inputs
- `.planning/PROJECT.md` — data strategy decision (commit samples AND live-regenerable), constraints.
- `.planning/REQUIREMENTS.md` — EXTRACT-04, DATA-01..04, PROMPT-04 are this phase's mandated reqs.
- `.planning/ROADMAP.md` §"Phase 2" — the 5 success criteria this phase must make TRUE.
- `.planning/phases/01-foundation/01-CONTEXT.md` — Phase-1 decisions carried forward (D-04 evidence
  offsets validated in code; D-05/D-07 envelope; D-11 prompt `.md` format).

### Existing code the phase builds on / extends
- `services/ai/schemas/envelope.py` — `Field[T]`, `Evidence`, `ConflictingValue`, `FlagStatus`; the
  gate's INPUT contract and what it must produce on downgrade (`unsupported` forbids value/evidence).
- `services/ai/schemas/domain.py` — `RFQ` and `VendorResponse` stubs to flesh out this phase
  (`ExtractionResult`/`ComparisonResult` stay stubs).
- `services/ai/prompts/{rfq-gen,vendor-gen,messy-data-gen}.v1.md` — the prompt stubs to author.
- `services/ai/prompts/registry.py` — how prompts are loaded by id (D-11/D-12 versioning).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Field[T]` / `Evidence` / `ConflictingValue` / `FlagStatus` (`schemas/envelope.py`) — the
  grounding gate consumes and re-emits these directly; the envelope's `model_validator` already
  enforces that `unsupported` carries no value/evidence, so the gate's downgrade is just setting
  `status=unsupported` and letting the contract hold.
- Prompt registry (`prompts/registry.py`) + the 3 existing prompt stubs — author in place, version
  via filename suffix (D-12).
- LLM tier factory `get_llm('reasoning'|'cheap')` (Phase 1) — generation prompts call `reasoning`.

### Established Patterns
- pydantic schemas are the contract source; any change to `RFQ`/`VendorResponse` must regenerate
  `packages/shared-types` and pass the codegen drift-check test (Phase-1 D-14, PLAT-02).
- `# ponytail:` comments mark deliberate kept-complexity; the stubs note "real fields land in P2".
- Generic pydantic models need the `# noqa: UP046` pattern (see envelope.py) for pydantic2ts.

### Integration Points
- The grounding gate is built standalone now but is the seam Phase 3 extraction calls (D-05–D-07) —
  its signature is the cross-phase contract, so get it right before any agent exists.
- Sample data lands under `data/`; live regen is exposed for in-app use (DATA-04), consumed by the
  P5 Vendor Input / RFQ Overview screens.
- Fleshing out `RFQ`/`VendorResponse` propagates through `shared-types` to the P5 UI.
</code_context>

<specifics>
## Specific Ideas

- The phase theme mirrors Phase 1's "prove it": the gate must be demonstrably falsifiable — a
  fabricated span is downgraded to `unsupported` by code (success criterion 1), and a genuine span
  survives without over-rejection (criterion 2). Both are unit tests, no LLM.
- "Code that disproves the model" — the gate's job is to *refute*, not to trust; the downgrade
  report is the evidence that it did.
- The 3 personas are chosen to collectively exercise every flag type (missing, unclear, conflicting,
  unsupported) so downstream extraction/comparison demos have real material.
</specifics>

<deferred>
## Deferred Ideas

- File upload (PDF/Word/Excel/PPT best-effort text extraction) — Phase 5 (INPUT-02); Phase 2 vendor
  responses are generated as text, not parsed from binary docs.
- RFQ Overview / Vendor Input screen rendering — Phase 5 (UI-01/UI-02); Phase 2 produces the
  structured data + rendered Markdown they will consume.
- Extraction agent that *produces* the `Field[T]` facts the gate validates — Phase 3; Phase 2 builds
  only the gate and its contract.
- 4th vendor persona (multi-currency/tax-ambiguous or partial-scope specialist) — possible richer
  comparison grid later; 3 is the committed scope.

None of the above is lost; each is anchored to its owning phase.
</deferred>

---

*Phase: 2-Grounding Gate & Messy Data*
*Context gathered: 2026-06-27*
