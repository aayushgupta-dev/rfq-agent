# RFQ Generation Prompt Documentation

**Prompt:** `services/ai/prompts/rfq-gen.v1.md`
**Version:** 1
**Model tier:** reasoning (gpt-5.4)

---

## What It Does

The rfq-gen prompt generates one realistic marketing-services RFQ covering all 8 named line
items (strategy & creative, TVC development, TVC production, social organic, paid media
planning, paid media buying, kids advertising & claims compliance, launch program management).
It produces a structured JSON object that validates against the `RFQ` pydantic schema, complete
with scope, timelines, commercial expectations, a vendor questionnaire, and compliance
requirements. The output must feel like a real procurement event — not a clean sample.

---

## Why It Is Structured This Way

**Concrete persona and procurement event.** The prompt frames the model as a senior procurement
manager at "Luminos Consumer Brands" preparing a go-to-market pitch for "GlowBite", a
children's vitamin gummy. A named company and product ground the RFQ in a coherent commercial
context; without this, the model defaults to generic, under-specified scope language. The
persona also sets the right register — procurement-professional, not marketing — so the RFQ's
tone matches what a real buyer would circulate.

**Explicit 8 line items with schema-matching IDs.** Each line item is listed by its exact
`id` and `name` (matching what the extraction agent expects in `LineItemExtraction.line_item_id`).
Sample deliverables are provided inline so the generated scope is specific rather than a
template placeholder. Without this scaffold, the model invents arbitrary categories and IDs
that break downstream schema validation. The 8 items are also the rubric line items — the RFQ
must cover them so vendor responses and extractions are traceable back to a shared scaffold.

**Compliance clauses named explicitly.** COPPA, CAP/BCAP, CARU, and product-claims
substantiation are enumerated in both the vendor questionnaire and the compliance section.
The extraction agent looks for these in vendor responses; omitting them from the RFQ removes
the buyer's obligation to require compliance coverage — reducing extraction signal on the
compliance dimension.

**Anti-hallucination instruction.** A dedicated section near the end prohibits the model from
referencing real living persons, named award shows, proprietary technology vendors, or
third-party brands. Without it, the model produces plausible but unverifiable references
(e.g., a real media owner's rebate policy, a named regulatory ruling) that undermine the
sample data's credibility for a reviewer.

**JSON-only output instruction.** The final section requires the model to respond with the
JSON object only, matching schema field names exactly. Without this instruction, the model
typically wraps JSON in markdown fences or adds explanatory prose that breaks
`RFQ.model_validate_json()`.

---

## How It Handles Unreliable / Missing / Conflicting Information

The RFQ is our own generated artifact, not vendor-supplied input, so missing/conflicting
information is not the primary risk. Instead, the risks are over-tidiness and hallucination:

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Generic or under-specified output (vague deliverables, round-number budgets) | Realism standard section instructs the model to inject specificity: named deliverables, concrete calendar dates, realistic budget tiers | RFQ reads like a real procurement event, not a template |
| Model adds invented references (real brands, award shows, real companies) | Anti-hallucination instruction prohibits named references by category | No unverifiable commercial claims in the sample data |
| Model omits budget ambiguity, making the RFQ unrealistically clean | Commercial expectations section explicitly instructs asymmetric budget tiers and partial disclosure for some line items | RFQ has realistic information gaps that vendors must navigate |

If the model produces a generic or implausible RFQ despite these instructions, the failure
would trigger a v2 prompt adding stronger realism forcing instructions or structural templates
for each section.
