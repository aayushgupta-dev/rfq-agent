# Demo Script — Bid Desk (≤5 min)

## Arc (D-19): "Code disproves the model"

The demo narrative follows a procurement buyer working through a messy competitive bid.
Each screen demonstrates a specific rubric item. The climax is the Trace screen — where the
buyer sees, literally, that the AI model proposed one verdict and the code overruled it
because the evidence required it.

Extraction and comparison run the live OpenAI pipeline (D-02), so exact field values and
verdicts may vary run-to-run. The narration below describes **behavioral properties** to
observe — not specific values to assert.

---

## Pre-Demo Checklist

- [ ] Warm the Render instance: `curl https://[your-render-url]/data/rfq`
      (prevents cold-start delay at the opening screen)
- [ ] Open the app at your Vercel URL (or `http://localhost:3000`)
- [ ] Navigate to **Prompt Trace** and select the "Comparison 1" tab — confirm amber rows are
      visible in the "Code vs. Model" section (this tab uses fixture data, so it is deterministic)
- [ ] Navigate back to **RFQ Overview** before starting the recording
- [ ] Have Chrome DevTools Network tab open and filtered to "EventStream" to show SSE chunks
      if needed for the streaming demonstration

---

## Screen-by-Screen Script

### 00:00–00:30 — RFQ Overview

**What to show:** The RFQ renders instantly from committed data. Scroll to show the 8 line items,
the compliance requirements, and the vendor questionnaire.

**Narration:**
> "Here's the procurement event — a marketing services RFQ for an 18-month product launch. Eight
> line items: strategy, creative, TVC development and production, social media, paid media, kids
> advertising compliance, and launch management. The AI generated this RFQ from a prompt — you can
> click 'Regenerate' to run it live. Note the compliance requirements and the vendor questionnaire —
> these are deliberately demanding, which is why the vendor responses look the way they do."

**Optional:** Click "Regenerate RFQ" and wait a few seconds to show live generation.

---

### 00:30–01:30 — Vendor Input → Extraction Review (Fluff vendor)

**What to show:** Load the "Fluff" vendor (most messy — weak scope, marketing language, missing
commercial terms). Navigate to Extraction Review. Observe what the AI extracted.

**Narration:**
> "I'll load the 'Polished Fluff' vendor — this one reads like a marketing brochure. Watch the
> extraction run live."

[Wait for SSE to complete]

> "Look at the Gaps panel at the top. Count how many fields are flagged — [observe the count on
> screen]. Every flag is a real gap in what this vendor submitted. The AI didn't fill them in and
> call them 'TBD' — it flagged them explicitly with the reason.
>
> Expand any field with an evidence snippet. The quoted text is verbatim from the vendor's
> response. That evidence is validated in code after the model returns — if the model's snippet
> can't be located in the source, it gets downgraded to 'unsupported' automatically."

---

### 01:30–02:30 — Load all 3 vendors → Comparison

**What to show:** Go back to Vendor Input and load the "Thorough" and "Cheap" vendors. Navigate to
Comparison. Focus on the comparability matrix and the attention panel.

**Narration:**
> "Now I'll load all three vendors so we can compare. The comparison doesn't start until we have
> extraction results for each."

[Load Thorough and Cheap vendors, wait for extractions]

[Navigate to Comparison, wait for SSE]

> "Before the system ranks anyone, it determines who is actually comparable on each dimension.
> Find a cell in the matrix with a 'not comparable' badge — [point to one on screen]. That vendor
> didn't provide sufficient evidence for the system to say their proposal is comparable on that
> dimension. The reason is shown right in the cell.
>
> The attention panel on the left lists clarification questions the system generated — one per
> flagged field. These are the exact questions the buyer would send to vendors to get the missing
> information."

---

### 02:30–03:30 — Prompt Trace → "Code disproves model"

**What to show:** Navigate to Prompt Trace. Select "Comparison 1" (the fixture trace with known
amber rows). Find an amber-highlighted row in the "Code vs. Model" section.

**Narration:**
> "This is the 'code disproves the model' moment — the headline reliability claim made concrete.
>
> The 'Comparison 1' trace is a fixture — meaning it was generated with the model proposing
> 'comparable' for every vendor on every dimension, on purpose, so we can see the clamp in action.
>
> Look at the 'Code vs. Model' section. The amber rows are where the code overruled the model.
> The heading tells you exactly how many: [read the count on screen] verdicts were overruled.
>
> For each row: the model proposed 'comparable,' the code said 'not comparable,' and the reason
> is in the last column — a required field was missing in that vendor's extraction. The model
> couldn't see that; the code enforced it from the evidence."

[If running with live comparison data: switch to a non-fixture tab and look for amber rows.
If no amber rows appear on the current tab, switch to another tab until one is visible.]

> "This is the reliability architecture in one view: the pipeline timeline shows input →
> prompt → raw model output → final result. The clamp diff shows every place where
> 'strong prompt design' meant the code overruled a model guess."

---

### 03:30–04:30 — Prompt Pack

**What to show:** Scroll down to the Prompt Pack list. Point out the 7 prompts with their IDs,
versions, and intent descriptions.

**Narration:**
> "Below the trace: the Prompt Pack. Seven versioned prompts — each documented with its ID,
> version, and the one-line intent. Each is a first-class source artifact, not a string buried
> in code.
>
> The extraction prompt's design — the four flag states, the evidence contract, the humility
> instruction — is what makes everything above possible. The docs folder has the full rationale
> for each prompt."

---

### 04:30–05:00 — Return to Comparison, closing narration

**What to show:** Navigate back to Comparison. Point to the "not a ranking" label and the
"Comparability determined in code from evidence" note.

**Narration:**
> "Back to the comparison screen — no fabrication. The comparability verdict here is derived from
> extraction evidence, not from a model assertion. There's no numeric leaderboard, no scoring
> — just: who addressed the brief, where the gaps are, and what the buyer needs to ask.
>
> Missing is missing. Not filled in. That's the design principle."

---

## Key Points to Hit (rubric coverage)

| Rubric item | Demo moment | Weight |
|-------------|-------------|--------|
| **Prompt quality & architecture** | Prompt Pack list (03:30–04:30); extraction prompt system message visible in trace raw output | 30% |
| **Realistic data generation** | Fluff vendor extraction showing multiple gaps; mention the 3 deliberately messy vendors were generated from a prompt | 20% |
| **Extraction accuracy & reliability** | Evidence snippets inline; grounding gate explanation in trace (amber rows = code enforcement) | 20% |
| **Product thinking in comparison** | Not-comparable badges with reasons; attention panel with clarification questions; no ranking | 15% |
| **UI/UX prompt quality** | Mention ui-ux-gen.v1 produced the design spec; the buyer-first layout (gaps first, evidence inline) | 10% |
| **Demo clarity & docs** | This script; README; write-up in docs/write-up.md | 5% |

Note: extraction and comparison run the live GPT-5.4 pipeline (D-02). Exact field counts and
verdicts vary run-to-run. Narrate what you observe on screen — the behavioral properties
(gaps surfaced, clamps visible, evidence shown) are stable even if the specific values differ.
