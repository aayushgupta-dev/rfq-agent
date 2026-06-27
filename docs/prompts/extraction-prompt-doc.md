# Extraction Prompt Documentation

**Prompt:** `services/ai/prompts/extraction.v1.md`  
**Version:** 1  
**Model tier:** reasoning (gpt-5.4)

---

## What It Does

The extraction prompt reads one vendor's raw proposal text and produces a structured
`ExtractionResult` covering: scope summary, per-RFQ-line-item pricing and scope coverage
(8 items), pricing structure, total price, commercial terms, timeline, compliance points,
assumptions, exclusions, and risks.

Every extracted fact carries a verbatim evidence snippet linking it to the source text.
Fields that are absent, ambiguous, contradictory, or unverifiable are explicitly flagged —
never silently filled, never fabricated.

---

## Why It Is Structured This Way

**Humility bias.** The prompt is written to prefer `unclear` over a confident `present`
on weak evidence, and `missing` over invention. This is the #1 reliability rule: a
confident `present` on shaky evidence is worse than an honest `unclear` because the
buyer then acts on a fabricated signal. The rubric penalises unsupported AI claims
(§24 anti-patterns) — the bias is the direct answer to that risk.

**Four-state model.** The model outputs exactly `present | missing | unclear | conflicting`.
A fifth state (`unsupported`) exists at the code level in the grounding gate but is
intentionally absent from the prompt. The gate downgrades fields whose evidence cannot
be located in the source text; the model should never self-declare a claim unsupported
(CLAUDE.md §2: never trust an LLM-supplied verified/grounded flag). Keeping the
boundaries clean prevents the model from gaming the gate.

**Verbatim evidence requirement.** Every non-missing field must carry at least one
verbatim snippet from the vendor response (≥20 characters, ≥3 words). The grounding
gate locates the snippet in the raw source text — if it cannot find it (exact match or
fuzzy ≥90 score), the field is downgraded to `unsupported`. This means paraphrasing
or inventing snippets will be caught in code, not by trusting the model.

**RFQ-aware line-item extraction.** The RFQ line items are injected as structured JSON
so the model knows exactly which services to check. This is the "RFQ-aware hybrid"
approach (D-01): per-item scope and pricing are extracted with explicit `missing` flags
when the vendor did not bid an item. Without the RFQ scaffold, the model could only
extract what the vendor mentioned and would miss silent omissions.

**No clarification questions.** The extraction prompt deliberately does not generate
clarification questions. That is a comparison-phase concern (Phase 4 / COMPARE-05)
which requires cross-vendor context to produce useful questions. Mixing it here would
couple the phases and reduce reusability.

---

## How It Handles Unreliable, Missing, and Conflicting Information

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Vendor did not address a line item | Set both pricing and scope_coverage to `missing` | Buyer sees explicit gap |
| Vendor gave a bundled total, no per-item breakdown | Per-item pricing → `unclear`; document-level `pricing_structure` → quotes the bundle | Never fabricates per-item splits |
| Vague/conditional statement ("TBD pending budget") | Use `unclear` with verbatim quote | Buyer sees the vagueness |
| Two contradictory statements | Use `conflicting` with `values[]`, each side with its own evidence | Both sides visible, nothing discarded |
| Vendor made a claim with no traceable text | Code gate downgrades to `unsupported` after model returns | Model cannot self-clear grounding |

---

## Evidence Floor vs Gate Minimum — MIN_SNIPPET_LEN Relationship (W-R3)

`gate.py` enforces a hard minimum snippet length of `MIN_SNIPPET_LEN = 15` characters.
Any snippet shorter than 15 characters is rejected by the gate and the field is downgraded.

The prompt instructs the model to supply snippets of **≥20 characters and ≥3 words**.
This floor is set *above* the gate floor intentionally:

- A 15–19 character snippet would pass the gate but violate the prompt instruction.
- Setting the prompt floor at 20 closes the gap and preserves the calibration intent.
- Prompt editors must keep the prompt floor ≥ `MIN_SNIPPET_LEN`. If `MIN_SNIPPET_LEN`
  is raised in `gate.py`, the prompt floor must be raised to match or exceed it.

The prompt also adds the ≥3 words requirement to prevent single-word snippets that hit
15+ characters via a long technical term (e.g. "Paid-Media-Buying-TBD-pending").

---

## What the Captured Traces Demonstrate

The committed traces under `docs/traces/` demonstrate **verbatim-evidence integrity**:
every fact shown in a trace's final result traces to a real, locatable span in the
vendor source text. On these fixtures gpt-5.4 quoted evidence character-for-character —
including the deliberately vague adversarial fixture — so the grounding gate confirmed
every snippet and **no downgrade fired**. Zero downgrades is the honest reflection of
model behaviour here, not a gap: the gate's downgrade behaviour (fabricated spans,
sub-threshold fuzzy matches, missing source IDs, too-short snippets) is proven
separately and rigorously by the unit tests in `services/ai/tests/test_grounding_gate.py`.
The `FUZZY_THRESHOLD` was deliberately left untouched (B-R3) — it is not a dial to turn
for trace production.
