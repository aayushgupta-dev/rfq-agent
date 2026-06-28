# AI Pipeline Architecture

This diagram shows the agent pipeline from input to final buyer-facing output.

```mermaid
flowchart TD
    RFQGen["RFQ Gen\n(LangGraph + gpt-5.4)"]
    VendorGen["Vendor Gen\n(LangGraph + gpt-5.4)"]
    MessyTax["messy-data-gen\ntaxonomy\n(embedded in vendor-gen)"]

    RFQJson["data/rfq.json\n(committed sample)"]
    VendorJson["data/vendor_*.json\n(≥3 messy responses)"]

    VendorResponse["VendorResponse\n{vendor_name, raw_text, source_id}"]
    RFQ["RFQ\n{line_items, scope,\ntimelines, compliance}"]

    ExtractionAgent["Extraction Agent\n(LangGraph + gpt-5.4)\nextraction.v1 prompt"]
    ExtractionDraft["ExtractionResult draft\n(model output, unverified)"]
    GroundingGate["Grounding Gate\n[code-enforced]\nlocate evidence spans\ndowngrade fabricated snippets\nrecompute char offsets"]
    ExtractionResult["ExtractionResult\n(grounded)\nField[T] with verified evidence"]

    ExtractionResultArr["ExtractionResult[]\n(one per vendor)"]
    ComparisonAgent["Comparison Agent\n(LangGraph + gpt-5.4)\ncomparison.v1 prompt"]
    ComparisonDraft["ComparisonDraft\n(model verdicts, unverified)"]
    ClampStep["Comparability Clamp\n[code-enforced]\ncap verdict to evidence ceiling\nrecord ClampEntry per override"]
    ClarificationAgent["Clarification Agent\n(LangGraph + gpt-5.4-mini)\nclarification.v1 prompt"]
    ComparisonResult["ComparisonResult\n(clamped + clarified)"]

    SSE["SSE Stream\n{type, payload}\nstatus / partial / result / done / error"]
    Browser["Browser\nBuyer UI\n(Next.js)"]

    UIUXGen["UI/UX Gen\n(one-shot, gpt-5.4)\nui-ux-gen.v1 prompt"]
    UISpec["UI/UX Spec artifact\n(captured in docs/traces/)"]

    MessyTax --> VendorGen
    RFQGen -- "live or committed" --> RFQJson
    VendorGen -- "live or committed" --> VendorJson

    RFQJson --> RFQ
    VendorJson --> VendorResponse
    VendorResponse --> ExtractionAgent
    RFQ --> ExtractionAgent

    ExtractionAgent -- "gpt-5.4 structured output" --> ExtractionDraft
    ExtractionDraft --> GroundingGate
    GroundingGate -- "pass" --> ExtractionResult
    GroundingGate -- "downgrade unsupported" --> ExtractionResult

    ExtractionResult --> ExtractionResultArr
    ExtractionResultArr --> ComparisonAgent
    RFQ --> ComparisonAgent

    ComparisonAgent -- "gpt-5.4 structured output" --> ComparisonDraft
    ComparisonDraft --> ClampStep
    ClampStep -- "clamped verdicts + ClampEntry[]" --> ClarificationAgent
    ClarificationAgent -- "gpt-5.4-mini" --> ComparisonResult

    ExtractionAgent -- "status events" --> SSE
    ComparisonAgent -- "status events" --> SSE
    ExtractionResult -- "result event" --> SSE
    ComparisonResult -- "result event" --> SSE
    SSE --> Browser

    UIUXGen --> UISpec
```

## Reliability Guarantees (code-enforced, not model-asserted)

| Step | What code enforces |
|------|-------------------|
| **Grounding Gate** | Evidence snippets are located in the source text (fuzzy threshold 90%). Snippets that cannot be found are downgraded to `unsupported`. Model-supplied `char_start`/`char_end` are discarded and recomputed. |
| **Comparability Clamp** | Vendor × dimension verdicts are capped by a ceiling derived from the `FlagStatus` values in the `ExtractionResult`. A vendor with `missing` fields on a dimension cannot be `comparable` on that dimension, regardless of what the model proposed. Every override is recorded as a `ClampEntry` visible in the Prompt Trace screen. |
| **Structured output** | Both agents use the OpenAI structured-output / JSON-schema path with pydantic models. The schema enforces the `Field[T]` envelope on every extracted value — a model that omits a required field causes a validation error, not a silent null. |
| **SSE streaming** | Agent work streams to the browser as it completes. Status events ("Aligning to RFQ… Extracting fields… Grounding evidence…") give the buyer live progress. An `error` event surfaces failures explicitly — never a blank screen or a fabricated result. |

## Prompt Pack Summary

| Prompt | Model tier | Job |
|--------|-----------|-----|
| `rfq-gen.v1` | gpt-5.4 | Generate one realistic marketing-services RFQ |
| `vendor-gen.v1` | gpt-5.4 | Generate a deliberately messy vendor response |
| `messy-data-gen.v1` | — (embedded taxonomy) | Defines 8 mess types injected by vendor-gen |
| `ui-ux-gen.v1` | gpt-5.4 | Generate buyer UI spec (one-shot artifact capture) |
| `extraction.v1` | gpt-5.4 | Extract structured facts with evidence and flag states |
| `comparison.v1` | gpt-5.4 | Compare vendors across 6 dimensions; comparability first |
| `clarification.v1` | gpt-5.4-mini | Draft buyer clarification questions for flagged fields |
