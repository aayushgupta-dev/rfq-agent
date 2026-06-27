# Data Generation Prompts — Prompt Pack Documentation

**Phase:** 02 — Grounding Gate & Messy Data
**Covers:** rfq-gen.v1.md, vendor-gen.v1.md, messy-data-gen.v1.md (PROMPT-04)

---

## rfq-gen (version 1)

**Source file:** `services/ai/prompts/rfq-gen.v1.md`

### What it does

Generates one realistic marketing-services RFQ for a competitive agency pitch covering
8 named service line items (strategy & creative through launch program management),
returning a structured JSON object that validates against the `RFQ` pydantic schema.

### Why it is structured this way

**Persona framing:** The prompt opens with a senior procurement manager persona at
"Luminos Consumer Brands" for a fictional product launch ("GlowBite"). Giving the model
a concrete role and client establishes a coherent commercial context without which the
model defaults to generic, under-specified output. The fictional brand is established
upfront so the anti-hallucination instruction can point to it by name.

**8 named line items specified by id and name:** The model cannot infer the exact 8
categories that match our schema (or the precise `id` values the extraction agent
expects) without explicit listing. Each line item includes sample deliverables so the
generated scope feels like a real procurement event rather than a template with
placeholder text. Omitting this causes the model to invent generic line items and
arbitrary IDs that break schema validation.

**Compliance clauses explicitly listed:** COPPA, CAP/BCAP, CARU, and product-claims
substantiation are named directly in both the questionnaire and compliance requirements
sections. The extraction agent will look for these in vendor responses; if they're
absent from the RFQ, vendors have no obligation to address them and the extraction
coverage is reduced.

**Anti-hallucination instruction:** An explicit "Anti-Hallucination Instruction" section
near the end tells the model not to reference real living persons, named award shows,
proprietary technology vendors, or third-party brands. Without this, the model
frequently invents plausible-sounding but unverifiable claims (e.g., referencing a real
media owner's rebate policy, citing a named regulatory ruling). For an RFQ that will be
shown to reviewers as sample data, invented references undermine credibility.

**JSON-only output instruction:** The final section instructs the model to respond with
the JSON object only, matching the schema field names exactly. Without this the model
often wraps the JSON in markdown fences or adds prose commentary, breaking
`RFQ.model_validate_json()`.

### How it handles unreliable / missing information

The RFQ is our own artifact — the model generates it from a complete, structured
prompt. Missing information is not a risk in the same way it is for vendor responses.
However, the anti-hallucination instruction prevents the model from _adding_ information
that wasn't in the prompt (invented clients, made-up awards, fabricated regulatory
rulings). If the model produces a generic or under-specified RFQ (vague deliverables,
round-number budgets with no rationale), the prompt's realism standard section
instructs it to inject specificity — named deliverables, concrete calendar dates,
realistic budget tiers.

### Model tier

**reasoning** (gpt-5.4) — the RFQ requires generating 8 coherent line items with
schema-matching JSON field names, realistic budget ranges at different tiers, and
multiple compliance clauses that cohere into a single procurement event. A "cheap" tier
model produces generic output that fails the 8-item uniqueness and specificity bar.

---

## vendor-gen (version 1)

**Source file:** `services/ai/prompts/vendor-gen.v1.md`

### What it does

Generates a single vendor proposal response to a given RFQ — deliberately realistic
and messy. Takes `{rfq_text}`, `{persona}`, and `{mess_spec}` as input parameters.
Returns raw agency prose (not JSON) exactly as the vendor would write it, with all
deliberate flaws intact.

### Why it is structured this way

**One-pass generation (D-08):** The prompt instructs the model to produce the messy
proposal in a single call — not a clean response that is then "vandalized" by a second
pass. This design choice was deliberate: one-pass generation produces coherent prose
where the flaws feel organic (a real agency that genuinely forgot to price a line item
writes differently than a clean proposal with pricing deleted). Two-pass vandalization
creates artifacts — abrupt holes, format inconsistencies, disconnected paragraphs — that
the extraction agent might detect as artificial rather than real vendor messiness.

**Mess spec as structured input (D-09):** The mess spec is passed as a structured list
of `MessSpecItem` dicts (with `line_item`, `issue_type`, `instruction` fields) rather
than as free-form instructions. Structured input makes each flaw deterministic and
testable: `test_sample_fixtures.py` asserts that the committed fixtures contain
specific markers for each issue type. Free-form instructions would produce flaws that
are real but unpredictable in their surface form, making automated assertions brittle.

**Issue-type taxonomy embedded inline:** The full 8-type taxonomy table is embedded
in the prompt body (not in a separate file reference). This ensures the model sees the
exact definition of each issue type when interpreting mess spec instructions — reducing
ambiguity about what "bundled_scope" or "internal_conflict" means. A separate reference
would require a second LLM call or prompt chaining, adding latency with no benefit.

**Format diversity by persona:** Each persona is assigned a different document format
(formal tabular proposal / email letter / deck outline). Format diversity stresses the
extraction agent differently: tabular format is easy for a rule-based parser but the
extraction agent must handle prose descriptions of tables; email style is unstructured
but readable; deck style uses callout boxes and strategic framework names that are
high-signal noise. Using the same format for all vendors would undertest the
extraction layer.

**"Do not clean up the mess spec" instruction:** An explicit critical instruction tells
the model not to moderate or sanitize any injected flaw. Without this, the model's
instruction-following tendency causes it to "helpfully" correct issues — pricing a line
item that the mess spec said to leave unpriced, reconciling conflicting figures, or
adding a compliance clause where the spec said to use vague language. This is the
primary failure mode for vendor generation (see Prompt Failure Example below).

**Anti-hallucination guardrail with fictional agency names:** The prompt suggests per-
persona fictional agency names (Meridian & Partners, Spark Creative Co., Apex Strategy
Group). This prevents the model from using real agency names, which would create
attribution issues in submitted sample data.

### How it handles unreliable / missing information

Vendor-gen deliberately INSTRUCTS the model to produce unreliable information. This
creates a structural tension: we need the model to follow instructions to produce
"bad" output (missing fields, conflicting figures, weak compliance claims) — which
requires the instructions to be more explicit and forceful than for a normal generation
task. The approach:

1. Mess spec instructions use imperative, specific language ("Do NOT price or address
   TVC Production. Do not acknowledge the omission.") rather than suggestive language
   ("you may leave TVC Production unpriced").

2. The "Critical Instruction" section at the end repeats the anti-cleanup rule after
   the full taxonomy — the model sees the rule twice (once in the taxonomy intro, once
   as a final instruction), reducing instruction-following drift.

3. Anti-hallucination and anti-cleanup are deliberately placed as separate sections so
   neither competes with the other in the model's attention.

### Model tier

**reasoning** (gpt-5.4) — each vendor response must coherently follow the persona's
voice and format, apply 4-5 mess spec instructions consistently across a long document,
and produce a response that reads like real agency prose despite the deliberate flaws.
A "cheap" tier model applies some mess spec instructions but inconsistently applies
others across a long generation, and the persona voice collapses into generic corporate
language.

---

## messy-data-gen (version 1)

**Source file:** `services/ai/prompts/messy-data-gen.v1.md`

### What it does

Serves as the definitive issue-type taxonomy reference — a structured catalog of the
8 deliberate flaw types that can be injected into vendor responses via the mess spec.
Each type includes: name, description, example text in vendor prose, why it causes
buyer problems, and how it stresses the extraction agent.

### Why it is structured this way

**Dedicated taxonomy reference (D-08):** The messy-data-gen prompt exists as a separate
Prompt Pack entry to document the taxonomy for reviewers and to give the taxonomy its
own versioned source file. The taxonomy content is embedded inline in vendor-gen.v1.md
(as a table) for efficiency — messy-data-gen is the canonical reference, vendor-gen
carries a condensed copy. This avoids an extra LLM call while keeping the taxonomy
version-controlled and reviewable as a first-class artifact.

**Summary table with FlagStatus mapping:** The prompt includes a summary table mapping
each issue type to its expected extraction `FlagStatus` (`missing`, `unclear`,
`conflicting`, `unsupported`) and whether a clarification question is needed. This
bridges the data-generation and extraction layers: a reviewer can trace from mess spec
instruction → expected extraction output, confirming that the extraction agent is
correctly identifying each flaw type.

**No input parameters:** messy-data-gen has no `{variable}` slots. It is a reference
document, not a generation prompt. It does not make LLM calls in the current pipeline.

### Model tier

**cheap** (gpt-5.4-mini) — messy-data-gen is a reference document, not a generation
call. If ever used as a generative prompt (e.g., to suggest new mess spec instructions
for a given RFQ), a cheaper model is appropriate since the taxonomy structure is fixed
and the output is structured text, not nuanced prose.

---

## Prompt Failure Example + Fix (PROMPT-04 — D-14)

**Label: Anticipated failure-mode (no real failure occurred during authoring).**

The rfq-gen, vendor-gen, and messy-data-gen prompts were authored offline and not
executed against a live model during plan 02-03. Plan 02-04 executed them for the first
time and generated the committed fixtures without a generation-level prompt failure
(all 5 fixture tests passed GREEN on the first run). Per D-14, the failure example
below is therefore labeled as an anticipated failure-mode derived from the taxonomy
and persona design, not a real observed failure.

### Anticipated Failure: vendor-gen over-polishes despite "omit fee" instruction

**Anticipated failure:** The vendor-gen prompt instructs the cheap-but-incomplete
persona to leave the Paid Media Buying fee as "TBD" explicitly. The model may instead
provide a rough estimate ("approximately $X–$Y, to be confirmed") — a "helpful"
elaboration that partially satisfies the omission instruction while also partially
violating it. The fixture test `test_cheap_incomplete_has_missing_price` checks for
TBD / "to be determined" / "price not provided" / "no price" / "not included" /
"upon request" — a model that writes "approximately $X–$Y, to be confirmed" might not
match any of these markers, causing the test to fail.

**Why this happens:** Instruction-following models have a tendency to optimize for
_helpfulness_ — producing an answer that satisfies the requester's apparent intent
(provide pricing) even when the explicit instruction says to omit it. This is a
well-documented LLM reliability challenge for deliberate-omission generation.

**Mitigation already in prompt:** The vendor-gen prompt contains two explicit anti-
cleanup instructions:
1. In the taxonomy intro: "Apply each instruction EXACTLY as specified — do not
   moderate, sanitise, or 'fix' any injected flaw."
2. As a separate "Critical Instruction" section: "If the mess spec says to omit a
   line item's pricing, omit it."
The mess spec instruction for cheap-but-incomplete uses imperative language: "Leave
the fee TBD. Write explicitly: 'Paid Media Buying: TBD — we would need to understand
your media budget before quoting.'" The explicit quoted phrasing reduces model
interpretation drift.

**Why this matters:** If vendors consistently over-polish their responses despite mess
spec instructions, the extraction agent sees fewer `missing`/`unclear` flags. This
directly reduces the rubric score for "absence is first-class" (CLAUDE.md §1,
Extraction accuracy 20%) — the evaluation criteria most directly tied to vendor
messiness.

**What would trigger a v2 prompt:** If the committed fixtures fail the messiness
assertions after regeneration (due to model behavior drift), or if the extraction
agent consistently reports fewer `missing`/`unclear` flags than expected. A v2 prompt
would add persona-specific format templates with explicit placeholder markers (e.g.,
`[PRICE: TBD]`) in the mess-spec-affected positions, making omissions structurally
enforced rather than instruction-reliant.

---

## Versioning / Eval Notes

### Current version: v1

**What would trigger a v2 prompt:**

- **rfq-gen v2:** If the committed RFQ fixture fails schema validation after model
  drift (e.g., a future model produces fewer than 8 line items, or generates
  non-matching field names). Or if the RFQ feels unrealistically simple for the
  GlowBite scenario — reviewers note the deliverables are generic rather than specific.

- **vendor-gen v2:** If any of the 5 fixture tests fail on regeneration (messiness
  assertions find that flaws are not present), or if the extraction agent consistently
  misses a flaw type that the mess spec was supposed to inject. A persistent
  over-polishing pattern (see failure example above) would trigger the structural
  placeholder approach described above.

- **messy-data-gen v2:** If new issue types are needed (e.g., a new flaw type
  identified during extraction agent development) or if the FlagStatus mapping changes
  when the ExtractionResult schema is fleshed out in Phase 3.

### Eval criteria — how to tell the prompts are working

1. **Structural check:** `uv run pytest tests/test_sample_fixtures.py -x -q` passes
   GREEN — the 5 assertions (existence + schema validity + messiness markers) confirm
   the fixtures are structurally correct and contain the expected flaw signatures.

2. **Semantic check (manual):** Read `data/rfq.md` — it should feel like a real
   procurement document, not a template. The 8 line items should have specific
   deliverables, concrete budget ranges in different tiers, and at least 5 compliance
   clauses.

3. **Extraction coverage check (Phase 3):** When the extraction agent runs on the
   three vendor fixtures, it should surface:
   - At least 2 `missing` flags across the three vendors (from cheap-but-incomplete
     omitted line items and polished-fluff vague pricing)
   - At least 1 `conflicting` flag (from polished-fluff internal timeline conflict)
   - At least 1 `unclear` flag (from cheap-but-incomplete vague timeline or
     thorough-but-pricey bundled pricing without per-item breakdown)

4. **Absence check:** No field in any vendor fixture should contain a fabricated
   number or claim that isn't grounded in the RFQ context. The grounding gate
   (plan 02-02) will validate evidence spans in Phase 3 output — data generation
   itself is not a trust boundary (T-02-13 accept).
