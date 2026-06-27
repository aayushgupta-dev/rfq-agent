# Phase 3: Extraction Agent - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 3-Extraction Agent
**Areas discussed:** Schema & RFQ-awareness, Call strategy & streaming, Prompt trace, Flag posture & evidence & clarification boundary

User opted to discuss all four offered gray areas and explicitly asked that "anything and
everything relevant and niche be covered" — so several niche schema/boundary corrections were
surfaced alongside the headline decisions.

---

## Schema & RFQ-awareness

| Option | Description | Selected |
|--------|-------------|----------|
| RFQ-aware hybrid | 8 RFQ line items as scaffold; per-item pricing+scope as Field[T] → natural `missing`; cross-cutting at doc level | ✓ |
| Vendor-shaped free-form | Extract vendor's own shape; Phase 4 does all alignment; can't detect missing-line-item at extraction | |
| Full per-item structuring | Force all 8 categories per line item; over-built, invites fabrication | |

| Option | Description | Selected |
|--------|-------------|----------|
| Doc-level pricing field + per-item `unclear` | Bundle captured verbatim at doc level; affected items marked `unclear` | ✓ |
| Force a per-item split | Allocate bundle across items; rejected (§24 normalization + fabrication) | |
| Leave entirely to comparison | Only doc-level bundle; per-item stays `missing` | |

| Option | Description | Selected |
|--------|-------------|----------|
| Per-claim list where natural | Multi-claim categories → list[Field]; narrative → single Field | ✓ |
| Single Field per category | One Field+snippet per category; coarse, one bad snippet kills the category | |
| List for every category | Even narrative becomes lists; fragments prose, inflates output | |

**User's choice:** RFQ-aware hybrid + doc-level pricing/per-item-unclear + per-claim-list-where-natural.
**Notes:** Drove the D-04 no-`dict[str,Field]` constraint (closes carried-forward IN-04) and the D-05
`vendor_name` correction (see below).

---

## Call strategy & streaming

| Option | Description | Selected |
|--------|-------------|----------|
| Single call, sectioned-split as researched fallback | One structured-output call/vendor; split only if truncation observed | ✓ |
| Always sectioned (2+ calls) | Always split; over-built before any truncation seen | |
| Per-line-item calls | 24+ calls; slow, expensive, wrong shape for cross-cutting | |

| Option | Description | Selected |
|--------|-------------|----------|
| Status for progress, grounded data only | Ground server-side; only grounded result+report cross SSE; never stream ungrounded facts | ✓ |
| Stream token-level partial fields | Richer demo but shows ungrounded facts; rejected | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hard error; truncation recoverable, refusal not | Never parse; truncation auto-retries sectioned once; refusal hard-stops | ✓ |
| Hard error, no auto-retry | Both stop, no recovery; simpler but a truncation kills the vendor needlessly | |

**User's choice:** Single-call + grounded-data-only streaming + truncation-recoverable/refusal-not.
**Notes:** Confirmed detecting `finish_reason`/`refusal` through LangChain is the flagged research item.

---

## Prompt trace (PROMPT-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Committed JSON + rendered MD under docs/traces/ | Reproducible deliverable now; Phase 5 viewer reuses the JSON | ✓ |
| In-app only | Defer to Phase 5; risks the requirement slipping | |
| JSON artifact only | Skip rendered MD until Phase 5 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Full pipeline incl. pre/post-grounding diff | input → prompt → raw output → grounding+report → final grounded | ✓ |
| Assignment-minimal | Four named stages, raw=final; loses the raw-vs-grounded contrast | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — select a real run that downgrades | Ensure ≥1 trace shows a genuine downgrade; doubles as threshold calibration | ✓ |
| Capture whatever the first run produces | May miss demonstrating the gate refuting the model | |

**User's choice:** Committed JSON+MD + full-pipeline + ensure-a-real-downgrade.
**Notes (refinement mid-discussion):** User added — capture **3–5 traces, not one**, so the eventual
solution presents a *body* of traces (one per sample vendor covering all flag types + 1–2 showcasing
a real downgrade). Folded into CONTEXT.md D-12.

---

## Flag posture, evidence & clarification boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Humility-biased, model uses only 4 states | Prefer unclear/missing over confident present; model never assigns `unsupported` (gate-only) | ✓ |
| Neutral / best-effort | Higher coverage, invites over-assertion; rejected | |

| Option | Description | Selected |
|--------|-------------|----------|
| Snippet + source_id only; gate computes offsets | Lean output (lower truncation risk); prompt hammers verbatim quoting | ✓ |
| Placeholder offsets on canonical schema | No fork but pays tokens for ignored integers | |

| Option | Description | Selected |
|--------|-------------|----------|
| Extraction only flags; clarifications Phase 4 | Clean boundary; clarification.v1.md untouched | ✓ |
| Extraction also drafts per-vendor clarifications | Duplicates Phase 4 ownership; two sources of clarification logic | |

| Option | Description | Selected |
|--------|-------------|----------|
| vendor_name plain str from provenance | Known metadata, not an extracted fact; avoids needless downgrade | ✓ |
| Keep as grounded Field[str] | Risks spurious `unsupported` on a name we already know | |

**User's choice:** Humility-biased/4-states + snippet-only-evidence + flag-only + vendor_name-plain-str.
**Notes:** All four recommendations accepted.

---

## Claude's Discretion

- Exact `ExtractionResult` / `LineItemExtraction` field names and the model-facing→canonical mapping.
- Extraction `StateGraph` node structure, function signatures, SSE endpoint surface.
- Whether a stated grand `total_price` is a distinct doc-level Field (assumed yes).
- Prompt few-shot selection/ordering and exactly how RFQ line items are injected.
- Code-level test structure (asserting grounding, absence surfacing, strict-mode hard errors).

## Deferred Ideas

- Sectioned multi-call extraction — researched contingency (build only if truncation observed).
- Clarification question generation — Phase 4 (COMPARE-05).
- `not-comparable` representation — Phase 4 (carried Phase-2 WR-01); not a field-level status.
- Extraction Review screen / in-app trace viewer / file upload — Phase 5.
- Streaming token-level partial fields — rejected on reliability grounds.
