# Comparison Trace 2 — Live Mode (real GPT-5.4)

> **Live Mode:** real GPT-5.4 call via `POST /compare/vendors` (the production route).
> Reasoning model: `gpt-5.4` · Clarification model: `gpt-5.4-mini`.
> Companion to the deterministic fixture trace (`comparison_trace_1`).

## 1. Input
- **RFQ:** Request for Quotation (RFQ) - GlowBite 18-Month Go-to-Market Marketing Services Program
- **Vendors:** cheap-but-incomplete, polished-fluff, thorough-but-pricey

## 2. Resolved Prompt
- comparison.v1 (reasoning) + clarification.v1 (cheap)

## 3. Verdict-Clamp Diff (real model proposed → code clamped)

_No clamp entries recorded._

## 4. Clarification Questions (live)
- **cheap-but-incomplete** / `line_items[2].pricing` (missing): Regarding your pricing for line item 2, your response does not include a price for this item. Could you provide the specific fee for line_items[2]?

- **cheap-but-incomplete** / `line_items[2].scope_coverage` (missing): Regarding the scope coverage for line item 2, your response does not specify what is included for this deliverable. Could you describe the exact scope covered by line_items[2]?

- **cheap-but-incomplete** / `line_items[6].pricing` (missing): Regarding your pricing for line item 6, your response does not include a price for this item. Could you provide the specific fee for line_items[6]?

- **cheap-but-incomplete** / `total_price` (missing): Your response does not include a total project price. Could you provide the full total price for the proposed scope?

- **thorough-but-pricey** / `total_price` (missing): Your response does not include a total project price. Could you provide the full total price for the proposed scope?

- **cheap-but-incomplete** / `line_items[5].pricing` (unclear): Regarding your pricing for line item 5, the price shown is unclear. Could you clarify the exact fee for line_items[5] and confirm the currency and billing basis?

- **cheap-but-incomplete** / `line_items[6].scope_coverage` (unclear): Regarding the scope coverage for line item 6, your description is unclear. Could you clarify exactly what deliverables and services are included in line_items[6]?

- **cheap-but-incomplete** / `timeline` (unclear): Regarding your project timeline, the schedule is unclear. Could you clarify the expected delivery timeline, including key milestones and any conditions that could affect timing?

- **thorough-but-pricey** / `line_items[0].pricing` (unclear): Regarding your pricing for line item 0, the amount is unclear. Could you clarify the exact fee for line_items[0] and confirm the currency and billing basis?

- **thorough-but-pricey** / `line_items[1].pricing` (unclear): Regarding your pricing for line item 1, the amount is unclear. Could you clarify the exact fee for line_items[1] and confirm the currency and billing basis?

- **thorough-but-pricey** / `line_items[4].pricing` (unclear): Regarding your pricing for line item 4, the amount is unclear. Could you clarify the exact fee for line_items[4] and confirm the currency and billing basis?

- **thorough-but-pricey** / `line_items[5].pricing` (unclear): Regarding your pricing for line item 5, the amount is unclear. Could you clarify the exact fee for line_items[5] and confirm the currency and billing basis?

- **polished-fluff** / `pricing_structure` (conflicting): Your response contains conflicting statements about the pricing structure. Could you confirm the correct pricing structure and indicate which version should be used for evaluation?

- **polished-fluff** / `total_price` (conflicting): Your response appears to list conflicting total price figures. Could you confirm the correct total price for the proposal?

- **polished-fluff** / `timeline` (conflicting): Your response includes conflicting timeline information. Could you confirm the correct project timeline and which schedule should be considered final?

- **thorough-but-pricey** / `line_items[2].pricing` (conflicting): Regarding your pricing for line item 2, your response contains conflicting figures. Could you confirm the correct fee for line_items[2]?


## 5. Vendor Readiness
| Vendor | Readiness |
|--------|-----------|
| cheap-but-incomplete | 1 of 6 dimensions comparable; blocked on technical, commercial, scope, timeline, compliance |
| polished-fluff | 3 of 6 dimensions comparable; blocked on commercial, timeline, compliance |
| thorough-but-pricey | 5 of 6 dimensions comparable; blocked on commercial |
