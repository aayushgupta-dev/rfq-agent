# Comparison Trace 2 — Live Mode (real GPT-5.4)

> **Live Mode:** real GPT-5.4 call via `POST /compare/vendors` (the production route).
> Reasoning model: `gpt-5.4` · Clarification model: `gpt-5.4-mini`.
> Companion to the deterministic fixture trace (`comparison_trace_1`).

## 1. Input
- **RFQ:** Request for Quotation (RFQ) - GlowBite 18-Month Go-to-Market Marketing Services Program
- **Vendors:** Northbridge Studio, Apex Strategy Group, Meridian & Partners

## 2. Resolved Prompt
- comparison.v1 (reasoning) + clarification.v1 (cheap)

## 3. Verdict-Clamp Diff (real model proposed → code clamped)

_No clamp entries recorded._

## 4. Clarification Questions (live)
- **Northbridge Studio** / `line_items[2].pricing` (missing): Regarding your pricing for line item 2, your response does not include the price for this item. Could you provide the specific fee for line_items[2]?
- **Northbridge Studio** / `line_items[2].scope_coverage` (missing): Regarding line item 2, your response does not include the scope coverage for this deliverable. Could you confirm exactly what is included in line_items[2]?
- **Northbridge Studio** / `line_items[6].pricing` (missing): Regarding your pricing for line item 6, your response does not include the price for this item. Could you provide the specific fee for line_items[6]?
- **Northbridge Studio** / `total_price` (missing): Your response does not include a total project price. Could you provide the overall total fee for the full scope?
- **Meridian & Partners** / `total_price` (missing): Your response does not include a total project price. Could you provide the overall total fee for the full scope?
- **Northbridge Studio** / `line_items[5].pricing` (unclear): Regarding your pricing for line item 5, the amount shown is unclear. Could you confirm the exact fee for line_items[5] and whether it is a fixed price or an estimate?
- **Northbridge Studio** / `line_items[6].scope_coverage` (unclear): Regarding line item 6, the scope coverage is unclear. Could you clarify exactly which tasks or deliverables are included in line_items[6]?
- **Northbridge Studio** / `timeline` (unclear): Your timeline is described unclearly. Could you confirm the expected delivery schedule, including the start date, key milestones, and final completion date?
- **Meridian & Partners** / `line_items[0].pricing` (unclear): Regarding your pricing for line item 0, the amount shown is unclear. Could you confirm the exact fee for line_items[0] and whether it is a fixed price or an estimate?
- **Meridian & Partners** / `line_items[1].pricing` (unclear): Regarding your pricing for line item 1, the amount shown is unclear. Could you confirm the exact fee for line_items[1] and whether it is a fixed price or an estimate?
- **Meridian & Partners** / `line_items[4].pricing` (unclear): Regarding your pricing for line item 4, the amount shown is unclear. Could you confirm the exact fee for line_items[4] and whether it is a fixed price or an estimate?
- **Meridian & Partners** / `line_items[5].pricing` (unclear): Regarding your pricing for line item 5, the amount shown is unclear. Could you confirm the exact fee for line_items[5] and whether it is a fixed price or an estimate?
- **Apex Strategy Group** / `pricing_structure` (conflicting): Your response contains conflicting statements about the pricing structure. Could you confirm the correct pricing structure and indicate which terms apply?
- **Apex Strategy Group** / `total_price` (conflicting): Your response contains conflicting statements about the total price. Could you confirm the correct overall total fee?
- **Apex Strategy Group** / `timeline` (conflicting): Your response contains conflicting statements about the timeline. Could you confirm the correct delivery schedule and final completion date?
- **Meridian & Partners** / `line_items[2].pricing` (conflicting): Regarding your pricing for line item 2, there appear to be conflicting statements about the fee. Could you confirm the correct price for line_items[2]?

## 5. Vendor Readiness
| Vendor | Readiness |
|--------|-----------|
| Northbridge Studio | 1 of 6 dimensions comparable; blocked on technical, commercial, scope, timeline, compliance |
| Apex Strategy Group | 3 of 6 dimensions comparable; blocked on commercial, timeline, compliance |
| Meridian & Partners | 5 of 6 dimensions comparable; blocked on commercial |
