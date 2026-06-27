---
id: rfq-gen
version: 1
intent: >
  Generate one realistic marketing-services RFQ covering 8 line items (strategy & creative,
  TVC development, TVC production, social organic, paid media planning, paid media buying,
  kids advertising & claims compliance, launch program management), with scope, timelines,
  commercial expectations, a vendor questionnaire, and compliance requirements.
  Must feel like a real procurement event — not a clean sample.
model_tier: reasoning
failure_handling: >
  If the generation model produces a generic or unrealistically tidy RFQ, the prompt instructs
  it to inject specificity: named deliverables, concrete timelines, explicit commercial
  constraints, and real compliance clauses. Missing or vague generated fields are flagged
  for human review before committing as sample data.
---

You are a senior procurement manager at **Luminos Consumer Brands** — a mid-size FMCG company
preparing to launch **GlowBite**, a children's vitamin gummy range targeting ages 4–12.

Your task is to produce a realistic, detailed Request for Quotation (RFQ) for a competitive
marketing-services agency pitch. The RFQ covers an 18-month go-to-market program across
8 service categories. This is a genuine procurement event with real commercial constraints,
concrete timelines, and strict compliance requirements — NOT a sanitised template or a
generic example.

---

## Realism Standard

The RFQ must feel like a document a real procurement team would issue. Apply these rules:

- **Dates are concrete** — use realistic calendar dates relative to an issue date of
  2026-07-15 (response deadline: 2026-08-12). Line-item start dates fall in Q4 2026.
- **Deliverables are specific** — not "creative assets" but "3 × 30-second TVC spots + 1 × 60-second
  brand film", "12-week editorial calendar", "monthly paid-media performance report with CPL
  breakdown by channel".
- **Budget ranges reflect market rates** — strategy retainers, TVC production, and paid media
  buying budgets each sit in clearly different tiers. Budget ranges are in USD and should be
  realistic for a mid-size FMCG launch (total campaign budget approx USD 1.2 M – 1.8 M across
  all line items combined).
- **Commercial expectations are explicit** — payment milestones tied to deliverables (not
  "on completion"), performance guarantees (e.g., minimum GRP for TVC), and transparency on
  media markup or agency fee structures.

---

## The 8 Line Items

Generate each line item with: `id`, `name`, `description`, `deliverables` (list), `timeline_weeks`
(int), and `budget_range_usd` ([min, max] as a two-integer list).

Use these exact line item IDs and names:

1. **id: "strategy-creative"** — Strategy & Creative Development
   Scope: brand narrative, audience segmentation, creative platform, campaign concept, messaging
   architecture. Covers both trade and consumer audiences.
   Key deliverable: brand playbook, ≥3 creative routes for client review, campaign concept deck.

2. **id: "tvc-development"** — TVC Development
   Scope: TV commercial concept development, scriptwriting, storyboarding, director's treatment,
   casting brief. Excludes physical production (that is line item 3).
   Key deliverable: final approved script, 2-3 director treatments, casting brief for ≥2 roles.

3. **id: "tvc-production"** — TVC Production
   Scope: pre-production, talent/location casting, shoot, post-production, colour grade, audio
   mix. Output: 3 × :30 TVCs + 1 × :60 brand film. Cutdown edits for digital.
   Compliance: all claims (nutritional, efficacy) must be substantiated before shoot;
   no health/medical claims without regulatory clearance sign-off.

4. **id: "social-organic"** — Social Organic Content
   Scope: content calendar (Instagram, TikTok, YouTube Shorts), creative production for
   organic posts, community management playbook, influencer identification brief.
   Key deliverable: 12-week editorial calendar, 3-month content bank (≥36 pieces),
   influencer brief for 5-8 nano/micro creators.

5. **id: "paid-media-planning"** — Paid Media Planning
   Scope: channel strategy, audience targeting recommendations, media plan across TV, digital,
   and OOH for campaign launch window (12 weeks). Media plan must include reach/frequency
   projections and GRP targets for TVC.
   Key deliverable: integrated media plan, channel-mix rationale, projected reach/frequency
   by channel, monthly pacing schedule.

6. **id: "paid-media-buying"** — Paid Media Buying
   Scope: execution of the approved media plan — buying, trafficking, optimisation, reporting.
   Agency must disclose all volume rebates, kickbacks, or media owner incentives.
   Monthly performance report required: CPL, CTR, viewability, brand-safety incidents.
   Budget managed by agency on Luminos's behalf; all invoices from media owners passed through.

7. **id: "kids-compliance"** — Kids Advertising & Claims Compliance
   Scope: regulatory compliance review of all creative and media targeting children (ages 4–12).
   Must cover: COPPA (US) digital data requirements, CAP/BCAP Code (UK) if any UK media,
   CARU guidelines (US) for child-directed advertising, and substantiation of all product
   claims (nutritional content, taste, health benefits). A compliance sign-off is required
   before any asset goes to production or media trafficking.
   Key deliverable: compliance checklist per asset type, written sign-off memo for each TVC,
   quarterly compliance audit report.

8. **id: "launch-management"** — Launch Program Management
   Scope: end-to-end project management of the 18-month program — workback schedule, weekly
   status, cross-agency coordination, risk register, stakeholder reporting.
   Key deliverable: master project plan (Gantt), weekly status report, monthly executive summary,
   risk register updated fortnightly.

---

## Questionnaire

Include ≥8 vendor questions. Cover:

- Pricing model (day rate vs project fee vs retainer — and what is included/excluded)
- Team composition for this account (seniority mix, named leads, dedicated vs shared)
- Previous FMCG or children's product marketing experience (examples required)
- Exclusivity: do you currently work with a competitor brand? What conflicts policy applies?
- Timeline risk management: how do you handle scope changes that affect launch date?
- Kids compliance accreditation: which regulatory frameworks do you have in-house expertise on?
- Media transparency: describe your media ownership disclosure policy and rebate pass-through
- References: provide 2 client contacts for accounts of comparable scale and category

---

## Compliance Requirements

List at least the following (plus any others appropriate to the scope):

- All creative content targeting children under 13 must comply with COPPA (US) and applicable
  advertising codes before production. A qualified compliance officer's sign-off is mandatory
  before shoot.
- Product efficacy and nutritional claims must be substantiated with documented evidence prior
  to inclusion in any script, visual, or media asset. No implied health claims without
  regulatory clearance.
- Media agency must provide a signed disclosure of all media owner rebates, volume bonuses, or
  commercial arrangements that affect the net media rate. Failure to disclose is grounds for
  contract termination.
- Agency must maintain and make available on request a conflict-of-interest register covering
  all clients in the children's food/beverage and FMCG categories.
- Data privacy: any digital campaign element targeting users under 13 must be designed for
  COPPA compliance with written confirmation from the agency's legal or compliance function.

---

## Commercial Expectations

Articulate clearly:

- Preferred payment structure: 30% at contract signature, 30% at mid-campaign milestone,
  40% on final delivery sign-off. No payment in full at start.
- All quoted fees must be inclusive of agency profit margin; no undisclosed markups on
  third-party costs. All third-party costs itemised.
- Media buying agency must provide gross-to-net reconciliation within 30 days of each
  quarterly media flight.
- Vendors must hold professional indemnity insurance of ≥ USD 2 M per occurrence.
- Contract includes a 15% performance penalty for missed agreed milestones (applied to the
  relevant invoice, not in aggregate).

---

## Anti-Hallucination Instruction

Do not reference real living persons, named award shows, proprietary technology vendors, or
third-party brands unless they are explicitly established in this prompt. The client brand
is **Luminos Consumer Brands** / **GlowBite** — these are fictional. Use realistic fictional
agency names if vendor examples are needed. Do not fabricate competitor names, media partner
terms, or regulatory rulings.

---

## Output Instruction

Respond ONLY with the JSON object matching the RFQ schema. No prose, no markdown outside the
JSON. The JSON must be valid and parseable. Field names must match the schema exactly:
`title`, `client_name`, `issue_date`, `response_deadline`, `scope_summary`, `line_items`
(array of 8 objects), `commercial_expectations`, `questionnaire` (array of strings),
`compliance_requirements` (array of strings), `budget_total_usd` (integer, optional).
