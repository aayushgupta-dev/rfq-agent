# Clarification Prompt Documentation

**Prompt:** `services/ai/prompts/clarification.v1.md`
**Version:** 1
**Model tier:** cheap (gpt-5.4-mini)

---

## What It Does

The clarification prompt takes a list of flagged fields — fields where an extraction or
comparison result has a status of `missing`, `unclear`, `conflicting`, or `unsupported` — and
drafts one specific, actionable clarification question per flagged field. Each question is
phrased neutrally and professionally, names the specific field and line item, and states the
nature of the ambiguity. The output is a `ClarificationSet` — a structured list of
`ClarificationQuestion` objects in the same order as the input flagged fields.

---

## Why It Is Structured This Way

**Clarification is a comparison-phase concern.** The clarification prompt is called after
the comparison agent runs, not after extraction. This is a deliberate architectural
separation: extraction identifies flagged fields per-vendor in isolation; comparison
identifies which gaps matter for cross-vendor evaluation. Clarification questions generated
from comparison output are therefore grounded in the buyer's actual decision context — "we
need this information to compare vendors on the commercial dimension" — rather than being
generic per-vendor checklists.

**One question per flagged field, same order.** The strict one-to-one mapping between input
flags and output questions enforces grounding: every question traces to a specific flagged
field with a known flag status and field path. The order preservation ensures the UI can
align questions with their source fields without an additional lookup. A model that groups
or reorders questions would produce questions that are harder to trace back to their source
evidence.

**Cheap model tier.** Clarification question drafting is a structured reformulation task:
take a flagged field description and produce a professional question. It does not require
the multi-step extraction reasoning or comparability analysis that the reasoning tier
handles. Using `gpt-5.4-mini` here keeps latency and cost proportionate to the task
complexity — clarification questions are generated after the expensive extraction and
comparison calls, and a cheap tier is sufficient to produce quality professional copy.

**Quality rules prohibit generic questions.** The prompt's "Question quality rules" section
explicitly requires questions to name the specific field, line item, and ambiguity type —
and prohibits generic questions like "Please clarify your pricing." This is enforced at the
prompt level because generic questions reduce the buyer's information gain: a question that
names the specific missing field and explains why it's needed for comparison is far more
actionable than a blanket clarification request.

**`why_needed` field makes questions self-explaining.** Each `ClarificationQuestion` includes
a `why_needed` field — one sentence explaining why the information is needed for comparison.
This field is surfaced in the UI alongside the question, giving the buyer context before they
send it to the vendor. It also serves as a grounding check: if `why_needed` cannot be stated
in one sentence without fabricating context, the question is too vague.

---

## How It Handles Unreliable / Missing / Conflicting Information

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Flagged field has insufficient context to generate a meaningful question | Output notes the field as "clarification not possible without more context" rather than generating a vague generic question | Buyer sees an honest limitation rather than a useless question |
| Question would assume missing information (e.g., "what is your price for X" when pricing was flagged as `unsupported`) | Valid — the question is grounded in the absence; it is asking for information the vendor did not provide | Question correctly targets the gap |
| Question would fabricate context (e.g., assuming a specific timeline was mentioned when it was `missing`) | Prohibited: "Questions are grounded in the extraction data — no new claims or assumptions are introduced" | Question references only the flag status and field path, not fabricated context |
| Question must be neutral and not accusatory | Copy guidelines: "phrased neutrally and professionally — not accusatory" with examples | Questions read as buyer-to-vendor information requests, not challenges |
| Input has a `conflicting` flag with two contradictory values | Question must reference both values and ask the vendor to confirm which applies | Question surfaces the conflict, not just one side of it |

A v2 prompt would be triggered by: questions that are consistently too vague despite the
quality rules, or if a `why_needed` field is found to be fabricating comparison context (e.g.,
claiming a dimension was assessed when the comparison input did not include it). The fix would
add few-shot examples pairing a flagged field description with a correct vs. incorrect question
format.
