# Comparison Trace — Fixture Mode

> **Fixture Mode:** This trace uses a deterministic over-optimistic fixture draft.
> No live OpenAI call was made. See the Fixture Mode Note section for details.

## 1. Input

- **RFQ:** Request for Quotation (RFQ) - GlowBite 18-Month Go-to-Market Marketing Services Program
- **Vendors:** cheap-but-incomplete, polished-fluff, thorough-but-pricey

### Flag counts per vendor

| Vendor | missing | unclear | conflicting | unsupported |
|--------|---------|---------|-------------|-------------|
| cheap-but-incomplete | 4 | 3 | 0 | 0 |
| polished-fluff | 0 | 0 | 3 | 0 |
| thorough-but-pricey | 1 | 4 | 1 | 0 |

## 2. Resolved Prompt

- **id:** comparison
- **version:** 1

**System message excerpt:**
```
You are a procurement analyst comparing vendor responses to a marketing-services RFQ.
You receive structured extraction objects — one per vendor — and an RFQ for context.
Your job is to compare the vendors across six dimensions and surface where they are
comparable, where data is insufficient, and what requires further review.

## Your role

You ONLY phrase comparisons and narrative text. You do NOT:
- Invent pricing, timelines, or scope details not present in the extractions
- Compute a numeric...
```

## 3. THE VERDICT-CLAMP DIFF

> This is the rubric story: model proposed 'comparable' for all; code clamped where flags dictate.

| Vendor | Dimension | Model Proposed | Code Ceiling | Clamped To | Ceiling Reason |
|--------|-----------|----------------|--------------|------------|----------------|
| cheap-but-incomplete | technical | comparable | not_comparable | **not_comparable** | technical ceiling=not_comparable for cheap-but-incomplete |
| cheap-but-incomplete | commercial | comparable | not_comparable | **not_comparable** | commercial ceiling=not_comparable for cheap-but-incomplete |
| polished-fluff | commercial | comparable | partially | **partially** | commercial ceiling=partially for polished-fluff |
| thorough-but-pricey | commercial | comparable | not_comparable | **not_comparable** | commercial ceiling=not_comparable for thorough-but-pricey |
| cheap-but-incomplete | scope | comparable | not_comparable | **not_comparable** | scope ceiling=not_comparable for cheap-but-incomplete |
| cheap-but-incomplete | timeline | comparable | partially | **partially** | timeline ceiling=partially for cheap-but-incomplete |
| polished-fluff | timeline | comparable | partially | **partially** | timeline ceiling=partially for polished-fluff |

## 4. Clarification Questions

_fixture mode — no live clarification call made. In production, the clarify node generates one question per flagged field._

## 5. Final Result — Vendor Readiness

| Vendor | Comparable Dimensions | Descriptor |
|--------|-----------------------|------------|
| cheap-but-incomplete | 2/6 | 2 of 6 dimensions comparable; blocked on technical, commercial, scope, timeline |
| polished-fluff | 4/6 | 4 of 6 dimensions comparable; blocked on commercial, timeline |
| thorough-but-pricey | 5/6 | 5 of 6 dimensions comparable; blocked on commercial |

## 6. Fixture Mode Note

This trace uses a deterministic over-optimistic fixture draft. The model was NOT called. Instead, a synthetic ComparisonDraft was constructed with `model_proposed='comparable'` for every vendor on every dimension. The real `_apply_verdict_clamp` function then ran against real ExtractionResult data (loaded from committed extraction traces), producing the downgrade diff above.

**Why fixture mode?** The clamp diff must be reproducible and deterministic. A live model call may or may not produce over-optimistic verdicts — depending on the model's judgment. Fixture mode guarantees `has_downgrades == True` for any vendor with missing fields, making the code-authority guarantee demonstrable without relying on model misbehavior. (Review Fix 5)

**What this proves:** Code, not the model, decides the final comparability verdict. The clamp diff table shows exactly where model-proposed 'comparable' was downgraded to 'not_comparable' or 'partially' because the code ceiling rule detected missing or ambiguous fields in the extraction data.

