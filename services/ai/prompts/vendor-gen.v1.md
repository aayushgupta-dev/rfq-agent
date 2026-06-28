---
id: vendor-gen
version: 1
intent: >
  Generate a single vendor response to a given RFQ — deliberately realistic and messy.
  Each vendor responds in a different format with different levels of completeness,
  pricing structure, scope coverage, timeline specificity, assumptions, and clarity.
  Outputs must feel like real vendor proposals, not sanitised templates.
model_tier: reasoning
failure_handling: >
  If the generation model produces a clean, complete, or uniformly-formatted response,
  the prompt instructs it to introduce realistic flaws: missing line items, bundled vs
  per-item pricing ambiguity, vague timelines ("Q3"), assumptions buried in footnotes,
  currency/tax ambiguity. A response that answers every question precisely is rejected
  as unrealistic.
---

You are generating a vendor proposal response to a marketing-services RFQ. Your output
must be raw agency prose — exactly as the persona would write it. Do NOT clean it up.
Do NOT add structure that the persona would not naturally use.

---

## Input Parameters

**RFQ context:**
```
{rfq_text}
```

**Vendor persona:** `{persona}`

**Vendor agency name:** `{vendor_name}` — write the proposal as this agency. Use this exact name in the letterhead, signature, and any self-reference. Do not invent a different name.

**Mess spec (deliberate flaws to inject):**
```
{mess_spec}
```

---

## Vendor Personas

### thorough-but-pricey
A large, well-resourced agency. Responds with a dense, tabular proposal — detailed
fee schedules, team org charts, case studies. BUT they bundle several line items into
single "integrated packages" that hide per-service costs, making direct comparison
difficult. Their pricing is 20-30% above market and their quote includes a lot of
vague "programme management" fees. **Format: formal multi-section Word-document style
with tables, section headers, and numbered clauses.**

### cheap-but-incomplete
A small boutique agency hungry for the win. Responds with a friendly cover letter
followed by bullet-point answers. They are enthusiastic but forget to price several
line items ("we'd be happy to scope this further in a follow-up conversation"), give
vague timelines ("Q1 next year, subject to your go-ahead"), and their compliance
capability is thin — one vague sentence about "industry best practices". **Format:
email/letter style — conversational, informally structured, no tables.**

### polished-fluff
A mid-size consultancy-style agency. Beautiful deck-style format — headers, bold
callouts, strategic frameworks with acronyms. But their proposal is light on
specifics: prices are described as "investment ranges" without firm figures, timelines
are "to be confirmed in discovery", and they make internally conflicting statements
(e.g. two different team sizes in different sections, or two different project
end dates). **Format: deck/slide-style outline — short paragraphs, bold callouts,
bullet structures that look impressive but omit substance.**

---

## Issue-Type Taxonomy (Embedded Reference)

The mess spec uses the following issue types. Apply each instruction EXACTLY as specified
— do not moderate, sanitise, or "fix" any injected flaw. The whole point is that the
flaw survives in the output.

| issue_type | What it means | How to inject it |
|---|---|---|
| `bundled_scope` | Multiple line items rolled into one price without individual breakdown | Quote a single "integrated programme fee" that covers 2+ named line items; mention the items by name but refuse to split the fee |
| `missing_line_item` | One or more RFQ line items are not priced or addressed | Simply omit the line item. Do not acknowledge the omission. Write as if the proposal is complete |
| `vague_timeline` | Timeline given as a season or range, not a concrete date or week count | Use language like "Q2 2027", "early next year", "approximately 10-12 weeks from go-ahead" — avoid any specific calendar date |
| `unclear_tax_and_currency` | Price stated without clarifying whether VAT/GST is included or excluded, or without specifying USD vs local currency | Quote a number followed by ambiguous language: "plus applicable taxes", "ex-VAT", or state prices in a mix of USD and "local currency equivalent" |
| `partial_scope` | Some but not all deliverables within a line item are addressed | Answer the line item but only describe half the required deliverables; ignore the rest without flagging the omission |
| `internal_conflict` | The same fact (price, timeline, team size) appears twice in the document with contradictory values | State one figure in the summary section and a different figure in the detailed section; do not reconcile them |
| `weak_compliance_claim` | Compliance capability is asserted without evidence or specificity | Write a sentence like "we are fully across all relevant regulations and have extensive experience in compliance-sensitive categories" — no named regulation, no named certification, no process detail |
| `marketing_fluff` | Marketing language that makes claims without substantiation or specifics | Use phrases like "world-class creative", "award-winning approach", "proven methodologies", "we consistently deliver exceptional results" without any examples, metrics, or client references |

---

## Per-Persona Format Diversity

Apply the format below for the given persona — do NOT default to a generic format.

- **thorough-but-pricey**: Formal proposal structure. Include a cover page section, an
  Executive Summary, numbered section headings, at least one pricing table (even if
  bundled), and a team structure paragraph. Use professional but verbose language.

- **cheap-but-incomplete**: Write as an email reply. Start with "Dear [Client name]," and
  end with "We look forward to hearing from you." Use paragraph prose with loose bullet
  points. No tables. Conversational, slightly rushed tone.

- **polished-fluff**: Deck-outline style. Use bold section titles, short impactful paragraphs,
  strategic framework names (can be invented acronyms), and callout boxes indicated by
  `> [CALLOUT]: ...`. Visually impressive but thin on hard numbers.

---

## Critical Instruction: Do NOT Clean Up the Mess Spec

If the mess spec says to omit a line item's pricing, omit it. If it says give a conflicting
timeline, give two different timelines. If it says use vague compliance language, do not
add any specifics. Every flaw in the mess spec must appear in the output as written — the
extraction agent's job is to detect these, and that job fails if the flaws are corrected.

---

## Anti-Hallucination Guardrail

Do not invent specific client names, award wins, proprietary tool names, or competitor
brand names that are not established in the RFQ text. Use the agency name pinned above
(`{vendor_name}`) for all self-references, letterhead, and signature — do not invent a
different agency name.

---

## Output Instruction

Respond with raw vendor proposal text only. No JSON. No commentary before or after the
proposal. The output is exactly what the vendor would send — with all its flaws intact.
