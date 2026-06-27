---
id: messy-data-gen
version: 1
intent: >
  Issue-type taxonomy used as a reference embedded in vendor-gen; defines the 8 mess types
  that stress extraction and comparison agents. Not a standalone generation call — vendor-gen
  embeds this taxonomy inline so the model understands what each issue type means and how
  to inject it faithfully.
model_tier: cheap
failure_handling: >
  This prompt is a reference document, not a model generation call. If a downstream agent
  using this taxonomy produces output that does not reflect the mess spec (e.g., a
  missing_line_item flaw is "corrected" by the model), the vendor-gen prompt must be
  strengthened with an explicit "do not fix" instruction for that specific flaw. The fix
  is always in the generating prompt, not in post-processing the output.
---

# Messy Data Issue-Type Taxonomy

This document defines the 8 deliberate flaw types that can be injected into vendor
responses via a mess spec. It is the authoritative reference for:

- The `vendor-gen` prompt (embeds this taxonomy so the model knows what each type means)
- Hand-authored mess specs in `agents/vendor_gen.py` (D-09)
- The `test_sample_fixtures.py` tests (D-13 — tests assert each type is detectable)
- The Prompt Pack documentation (PROMPT-04 — explains how each type stresses the extraction agent)

---

## Issue Type Definitions

### 1. `bundled_scope`

**Description:** Two or more RFQ line items are rolled into a single quoted price with no
individual cost breakdown. The vendor names the services but refuses (or "forgets") to
split the fee.

**Example in vendor text:**
> "Our Integrated Campaign Package covering Strategy & Creative and TVC Development is
> priced at USD 280,000. We do not provide separate line-item costs as our teams work
> in an integrated model."

**Why it causes buyer problems:** The buyer cannot compare strategy costs or TVC development
costs independently across vendors. Apples-to-oranges — one vendor prices them separately,
another bundles. Makes cost normalisation impossible without querying the vendor.

**How this stresses the extraction agent:** The agent must flag the two line items as
`unclear` (a price exists but is not assignable to either item alone) rather than
`missing` or `present`. The evidence snippet is a bundled price that cannot be
attributed to one field without vendor clarification.

---

### 2. `missing_line_item`

**Description:** One or more RFQ line items are simply not addressed in the proposal. No
mention, no price, no scope — as if the vendor didn't read that section of the RFQ.

**Example in vendor text:**
The proposal covers Strategy & Creative, TVC Development, TVC Production, Social Organic,
and Paid Media Planning. The sections on Paid Media Buying, Kids Compliance, and Launch
Management are absent.

**Why it causes buyer problems:** The buyer cannot evaluate whether the vendor is capable
of — or willing to — deliver the omitted service. A silent omission is harder to spot
than a stated exclusion.

**How this stresses the extraction agent:** The extraction result for the omitted line item
must be `missing` with no evidence. The agent must not fabricate a price or assume the
item is included in another line item's quote. Detection requires knowing what is NOT in
the text, not just what is.

---

### 3. `vague_timeline`

**Description:** Timeline is given as a season, quarter, or fuzzy range — never a concrete
start/end date or week count that could anchor the project plan.

**Example in vendor text:**
> "We anticipate kicking off strategy in Q4, with creative ready for review by early Q1.
> Production would wrap approximately 10-12 weeks from go-ahead, subject to your approval
> process."

**Why it causes buyer problems:** The buyer cannot build a project plan or compare vendor
timelines without a common date anchor. "Q4" could mean October or December. "10-12 weeks
from go-ahead" is meaningless without a go-ahead date.

**How this stresses the extraction agent:** The timeline field cannot be `present` — a
concrete value cannot be extracted. The agent must flag it as `unclear` with the vague
phrase as evidence. Representing a vague timeline as a specific date would be fabrication.

---

### 4. `unclear_tax_and_currency`

**Description:** Prices are quoted without clarifying whether tax (VAT, GST) is included
or excluded, or prices appear in a mix of USD and unspecified "local currency equivalents".

**Example in vendor text:**
> "Strategy & Creative: USD 95,000 (exc. applicable local taxes). TVC Production:
> AUD 310,000 or USD equivalent, subject to exchange rate at invoicing."

**Why it causes buyer problems:** The buyer cannot compare total cost of ownership across
vendors. The effective USD cost is unknowable until tax rate and exchange rate are applied.
A "cheaper" quote may actually be more expensive after tax.

**How this stresses the extraction agent:** The price field must be flagged `unclear` —
a number exists but the net cost to the buyer is ambiguous. The evidence snippet includes
the ambiguous qualifier. The agent must not strip the ambiguity or pick one interpretation.

---

### 5. `partial_scope`

**Description:** The vendor addresses a line item but only covers some of the required
deliverables, silently ignoring the rest. Unlike `missing_line_item`, the line item is
responded to — just incompletely.

**Example in vendor text:**
> "Social Organic: we will develop a 12-week editorial calendar for Instagram and TikTok
> and produce 24 pieces of content. Our team is highly experienced in organic social."
(The RFQ also required YouTube Shorts content, a community management playbook, and an
influencer identification brief — none of which are mentioned.)

**Why it causes buyer problems:** Partial scope coverage looks like a complete answer on
quick reading. The gap only becomes visible when the buyer checks the RFQ deliverable list
against the proposal line by line.

**How this stresses the extraction agent:** Some deliverable fields will be `present` with
evidence; others will be `missing`. The agent must enumerate all required deliverables from
the RFQ and flag each one individually — a single "scope covered" flag is insufficient.

---

### 6. `internal_conflict`

**Description:** The same fact (price, timeline, team size, scope inclusion) appears twice
in the proposal with contradictory values. The contradiction is not acknowledged or resolved.

**Example in vendor text:**
> [Executive Summary] "Our dedicated team of 12 professionals will manage the programme."
> [Team Structure section, three pages later] "This account will be serviced by a core
> team of 6, supported by our wider agency network on an as-needed basis."

**Why it causes buyer problems:** The buyer cannot know which figure is authoritative. In
a procurement context, a contract dispute about team size or price would rely on the document
itself — and the document contradicts itself.

**How this stresses the extraction agent:** The conflicting field must be `conflicting` with
a `values[]` list carrying both contradictory claims, each with its own evidence snippet.
The agent must not pick one value and discard the other — both must surface.

---

### 7. `weak_compliance_claim`

**Description:** Compliance capability is asserted in general terms without naming the
specific regulation, standard, or accreditation; without describing the process; and
without offering evidence or a reference.

**Example in vendor text:**
> "Compliance is central to everything we do. We are fully conversant with all relevant
> advertising regulations and have a long track record in compliance-sensitive categories.
> Our creative team works closely with our internal compliance function to ensure all
> work meets the highest standards."

**Why it causes buyer problems:** For a children's product campaign, COPPA compliance and
claims substantiation are legal requirements, not nice-to-haves. A vague assurance provides
no evidence the vendor has the capability. If something goes wrong, "we said we were
compliant" is not a defence.

**How this stresses the extraction agent:** The compliance field cannot be `present` — the
assertion exists but cannot be grounded in a specific, verifiable claim. It should be
`unclear` with the vague prose as evidence, and a clarification question should be generated
asking for the named regulation, the certifying body, and the process.

---

### 8. `marketing_fluff`

**Description:** Language that makes impressive-sounding assertions without any specifics,
metrics, client names (where verifiable), or concrete examples. Positive claims that cannot
be evaluated or verified.

**Example in vendor text:**
> "We are a world-class integrated agency with a proven track record of delivering
> exceptional results for ambitious brands. Our award-winning creative consistently
> outperforms category norms, and our proprietary strategic methodology has been
> recognised as an industry-leading approach to brand transformation."

**Why it causes buyer problems:** Fluff displaces substance. A proposal heavy in marketing
language is harder to evaluate against a structured RFQ. Claims like "award-winning" or
"proven" are meaningless without specifics.

**How this stresses the extraction agent:** Marketing fluff may appear in fields where a
buyer expects a fact (e.g. the "previous experience" or "team credentials" field). The
agent must flag such fields as `unclear` rather than `present`, and the evidence snippet
must quote the fluff so the buyer can see exactly what was asserted.

---

## Summary Table

| issue_type | Status result in extraction | Clarification question needed? |
|---|---|---|
| `bundled_scope` | `unclear` (price exists but not attributable) | Yes — request itemised breakdown |
| `missing_line_item` | `missing` (no evidence at all) | Yes — ask if service is in scope |
| `vague_timeline` | `unclear` (date ambiguous or absent) | Yes — request specific dates |
| `unclear_tax_and_currency` | `unclear` (net cost unknowable) | Yes — request all-in USD figure |
| `partial_scope` | Mixed: `present` for covered deliverables, `missing` for omitted ones | Yes — flag missing deliverables |
| `internal_conflict` | `conflicting` with two `values[]` entries | Yes — request authoritative figure |
| `weak_compliance_claim` | `unclear` (assertion unverifiable) | Yes — request named regulation + process |
| `marketing_fluff` | `unclear` (no factual basis) | Yes — request specific examples/metrics |
