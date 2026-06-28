# Vendor Response Generation Prompt Documentation

**Prompt:** `services/ai/prompts/vendor-gen.v1.md`
**Version:** 1
**Model tier:** reasoning (gpt-5.4)

---

## What It Does

The vendor-gen prompt generates a single vendor proposal response to a given RFQ — deliberately
realistic and messy. It takes `{rfq_text}`, `{persona}`, and `{mess_spec}` as structured inputs
and returns raw agency prose (not JSON) exactly as the vendor would write it, with all
deliberate flaws intact. Three runs of this prompt (one per vendor persona) produce the ≥3
messy vendor responses required by the rubric.

---

## Why It Is Structured This Way

**One-pass generation.** The prompt instructs the model to produce the messy proposal in a
single generation — not a clean response that is then "vandalized" by a second pass. One-pass
generation produces coherent prose where the flaws feel organic: a real agency that genuinely
forgot to price a line item writes differently than a clean proposal with pricing deleted
afterward. Two-pass vandalization creates artifacts — abrupt holes, format discontinuities,
disconnected paragraphs — that make the extraction agent's job easier (artificial holes are
structurally distinct from real omissions) and undermine the rubric's "realistic data"
requirement.

**Mess spec as a structured input.** The mess spec is passed as a structured list of
`MessSpecItem` dicts (each with `line_item`, `issue_type`, `instruction` fields) rather than
as free-form instructions. Structured input makes each flaw deterministic and testable:
`test_sample_fixtures.py` asserts that committed fixtures contain specific markers for each
issue type. Free-form instructions would produce flaws that are real but unpredictable in
their surface form, making automated assertions brittle and removing the traceability between
mess spec instruction and extraction output.

**Issue-type taxonomy embedded inline.** The full 8-type taxonomy table is embedded in the
prompt body (not referenced from a separate file). This ensures the model sees the exact
definition of each issue type when interpreting mess spec instructions — reducing ambiguity
about what "bundled_scope" or "internal_conflict" means. A separate reference would require
a second LLM call, adding latency with no benefit for a single-pass generation.

**Format diversity by persona.** Each persona is assigned a different document format:
formal tabular proposal / email letter / deck outline. Format diversity stresses the
extraction agent differently — tabular format is easy for a rule-based parser but requires
the agent to handle prose table descriptions; email style is unstructured but readable; deck
style uses callout boxes and strategic framework names that are high-signal noise. Using the
same format for all vendors would undertest the extraction agent's generalization.

**Double anti-cleanup instruction.** An explicit critical instruction tells the model not to
moderate, sanitize, or "fix" any injected flaw. This instruction appears twice: once in the
taxonomy intro and once as a standalone "Critical Instruction" section after the taxonomy.
The model sees the rule before and after the taxonomy table — reducing instruction-following
drift on longer generation tasks where the model may lose context of early constraints.

---

## How It Handles Unreliable / Missing / Conflicting Information

Vendor-gen deliberately instructs the model to produce unreliable information — which creates
a structural tension: the model must follow instructions to produce "bad" output (missing
fields, conflicting figures, weak compliance claims) while still producing coherent prose. The
approach:

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Model "helpfully" prices a line item the mess spec says to omit | Mess spec uses imperative, specific language: "Do NOT price or address TVC Production. Do not acknowledge the omission." The same rule is stated twice (taxonomy intro + Critical Instruction section) | Omission appears in generated prose; extraction flags it as `missing` |
| Model provides a rough estimate instead of a hard omission ("approximately $X–$Y, to be confirmed") | Quoted phrasing in mess spec: "Write explicitly: 'Paid Media Buying: TBD — we would need to understand your media budget before quoting.'" Quoted phrasing reduces model interpretation drift | Omission uses the expected test-assertable language |
| Model reconciles contradictory timeline figures instead of preserving the conflict | Anti-cleanup instruction: "Do not reconcile conflicting statements. Both figures must appear in the final response." | Extraction surfaces `conflicting` with both values |
| Model adds a compliance clause where the mess spec says to use vague language | Issue-type taxonomy defines "weak_compliance" with explicit examples of vague language to use instead of a clause | Extraction produces `unclear` on the compliance dimension |

If vendors consistently over-polish despite these instructions (a known model behavior for
deliberate-omission generation), a v2 prompt would add persona-specific format templates with
explicit placeholder markers (e.g., `[PRICE: TBD]`) in the mess-spec-affected positions —
making omissions structurally enforced rather than instruction-reliant.
