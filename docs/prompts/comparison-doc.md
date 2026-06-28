# Comparison Prompt Documentation

**Prompt:** `services/ai/prompts/comparison.v1.md`
**Version:** 1
**Model tier:** reasoning (gpt-5.4)

---

## What It Does

The comparison prompt reads a set of `ExtractionResult` objects (one per vendor) and an RFQ,
then produces a `ComparisonDraft` covering six dimensions: technical capability, commercial
terms, scope coverage, timeline, compliance, and risk. For each dimension it proposes a
comparability verdict (`comparable` / `partially_comparable` / `not_comparable`), a narrative
explanation, per-vendor detail, buyer attention points, and a list of clarification questions
grounded in flagged fields. A code-level comparability gate runs after the model returns and
clamps any over-optimistic verdicts — the model's proposed verdicts are starting points, not
final answers.

---

## Why It Is Structured This Way

**Comparability-before-ranking is the structural principle.** The prompt's output schema
requires a `ComparabilityVerdict` per dimension before any narrative. This is the §21
differentiator: the buyer sees who is comparable on each dimension before any synthesis. The
schema enforces this ordering — the model cannot produce a summary without first determining
comparability, which means the code gate always has a comparability signal to clamp.

**Six-dimension structure matches the extraction schema.** The six comparison dimensions map
to the `ExtractionResult` categories (scope, pricing/commercial, timeline, compliance, risk)
plus a technical capability dimension synthesized from scope and line-item coverage. This
alignment ensures every comparison fact is traceable to an extracted field — the model cannot
introduce new commercial or technical claims that were not in the extraction input.

**Explicit prohibition on numeric scoring.** The prompt's "Your role" section explicitly lists
what the model must NOT do: invent pricing or timelines not in extractions, compute a numeric
score or weighted rank, force a "comparable" verdict on missing data, normalize currencies or
bundle structures, produce a ranking. These prohibitions are placed before the output schema
so they frame the model's task before it sees the format.

**Code-enforced comparability ceiling.** A note in the prompt tells the model that code will
enforce comparability ceilings independently of its proposed verdicts: "If your verdict is too
optimistic, code will downgrade it to the correct value." This prevents the model from
gaming the output by producing `not_comparable` everywhere to be "safe" — it can propose
verdicts honestly, knowing the gate handles corrections. The model's job is an informed
starting point, not defensive under-estimation.

**Attention triggers as structured input.** The prompt receives a `attention_triggers` list —
a code-detected set of trigger dicts with `trigger_type`, `dimension_or_field`, and
`vendors_affected`. These are computed by code from flagged fields before the model is called,
ensuring the buyer attention points are grounded in the same data the model sees. The model
elaborates on triggers rather than detecting them from scratch — reducing hallucination risk
on attention signals.

---

## How It Handles Unreliable / Missing / Conflicting Information

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Vendor data insufficient to compare a dimension | Output "not yet comparable — needs clarification" rather than forcing a verdict | Buyer sees explicit non-comparability with reason |
| Model wants to normalize bundled vs. itemized pricing to compare vendors | Explicit prohibition: "Do not normalize currencies, units, or bundle structures — surface them as-is" | Structural pricing differences are visible, not hidden |
| Model proposes `comparable` on a dimension where a vendor's field is `missing` | Code comparability gate clamps the verdict to `not_comparable` or `partially_comparable` | Over-optimistic comparisons are corrected without prompt re-runs |
| Model introduces new claims not present in the extraction input | "Your role" section prohibits introducing new claims beyond what extraction produced | Comparison facts are grounded in extraction evidence |
| Clarification questions are generic ("Please clarify your pricing") | Questions are generated from flagged fields with `field_path` and `flag_status` as context | Questions name the specific field and ambiguity type |
| Model produces a winner or recommendation | Prohibitions section: "Do not produce a ranking of vendors" | No vendor is declared preferred; comparability matrix is the output |

A v2 prompt would be triggered by: the model consistently misclassifying a specific flaw type
(e.g., treating `missing` pricing as `unclear`), or producing narrative that implies a winner
despite the no-ranking prohibition. The fix would add few-shot examples of correct dimension
verdicts for common flaw combinations.
