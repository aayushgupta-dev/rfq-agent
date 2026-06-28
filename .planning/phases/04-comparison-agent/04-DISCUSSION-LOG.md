# Phase 4: Comparison Agent - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-28
**Phase:** 4-Comparison Agent
**Mode:** `--all` (all gray areas auto-selected; discussed interactively)
**Areas discussed:** Comparability signal representation, Verdict authority, Alignment boundary, Output surfaces (line items), Clarification generation, Clarification scope, Comparison trace, Per-vendor readiness rollup + framing + ordering, Attention points

---

## Comparability signal representation

| Option | Description | Selected |
|--------|-------------|----------|
| Per-dimension badge matrix | vendor×dimension grid, cell = comparable/partial/not + reason | |
| Narrative-first per dimension | prose paragraph per dimension | |
| Hybrid: matrix + narrative | badge matrix headline + narrative drill-down + attention panel | ✓ |

**User's choice:** Hybrid — matrix + narrative + attention-points panel.
**Notes:** Maps to D-01.

---

## Verdict authority (comparability keystone)

| Option | Description | Selected |
|--------|-------------|----------|
| Code-derived, model explains | code computes verdict from flags; model only writes reason | |
| Model judges, code guards | model proposes verdict; code can only downgrade to a flag-derived ceiling | ✓ |
| Model judges freely | no code enforcement | |

**User's choice:** Model judges, code guards (clamp-to-ceiling, downgrade-only).
**Notes:** Maps to D-03/D-04. The phase's "code disproves the model" keystone, mirroring the EXTRACT-04 grounding gate.

---

## Alignment vs normalization boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Surface as-is, zero reconciliation | group by line_item_id (done at extraction), show verbatim + flag non-equivalence; never convert/split/normalize | ✓ |
| Surface + safe reconciliation | also normalize currency labels/units to a common basis | |

**User's choice:** Surface as-is, zero reconciliation.
**Notes:** Maps to D-05. Honors §24; the §21 light-vs-heavy differentiator.

---

## Output surfaces — line-item table

| Option | Description | Selected |
|--------|-------------|----------|
| Line-item table + dimension matrix | 6-dim matrix + 8-line-item × vendor offer table with badges | ✓ |
| Dimension matrix only | line-item detail stays in per-vendor extraction view | |

**User's choice:** Both surfaces.
**Notes:** Maps to D-06. Where COMPARE-04 "surface differences" pays off.

---

## Clarification generation mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Separate cheap-tier call, code-seeded | code collects flagged fields; gpt-5.4-mini drafts questions | ✓ |
| Inline in the comparison call | one reasoning call emits comparison + clarifications | |

**User's choice:** Separate cheap-tier, code-seeded.
**Notes:** Maps to D-09. Reuses the reserved clarification.v1.md stub; input set is code-controlled.

---

## Clarification scope / granularity

| Option | Description | Selected |
|--------|-------------|----------|
| One per flagged field, buyer-prioritized | one grounded question per flagged field; no cap; ordered by impact, grouped by vendor | ✓ |
| Top-N prioritized only | cap at N highest-impact | |

**User's choice:** One per flagged field, buyer-prioritized.
**Notes:** Maps to D-10. No cap — dropping gaps violates "absence is first-class".

---

## Comparison trace deliverable

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — verdict-clamp trace | ≥1 trace showing raw-model-verdict → code-clamped-verdict diff + clarification set | ✓ |
| No separate trace | rely on P3 traces + unit tests | |

**User's choice:** Yes — verdict-clamp trace.
**Notes:** Maps to D-11. The phase's reliability-proof artifact; feeds the P5 trace viewer.

---

## Per-vendor overall readiness rollup

| Option | Description | Selected |
|--------|-------------|----------|
| No overall rollup — per-dimension only | per-dimension verdicts + attention panel; no per-vendor signal | |
| Qualitative per-vendor readiness | non-numeric per-vendor summary | ✓ |

**User's choice:** Qualitative per-vendor readiness (chosen over the "no rollup" recommendation).
**Notes:** Triggered a follow-up on framing + ordering to keep it §24-safe. Maps to D-07.

---

## Readiness framing

| Option | Description | Selected |
|--------|-------------|----------|
| Dimension-list, no count | which dimensions comparable vs blocked, no X/N | |
| Allow the X/N count | keep "4/6 comparable" count | ✓ |

**User's choice:** Allow the X/N count (chosen over the "no count" guardrail recommendation).
**Notes:** Residual implicit-rank risk accepted; mitigated by the never-sort + data-readiness framing. Maps to D-07.

---

## Vendor ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Never sort by readiness | stable input/alphabetical order always | ✓ |
| Sort by readiness | order most→least comparable | |

**User's choice:** Never sort by readiness.
**Notes:** Maps to D-07. Sorting = ranking; contradicts COMPARE-05. This is the guardrail that keeps the X/N count defensible.

---

## Attention points

| Option | Description | Selected |
|--------|-------------|----------|
| Code-triggered, model phrases | code detects triggers deterministically; model only phrases | ✓ |
| Model-authored from the data | model picks + writes attention points freely | |

**User's choice:** Code-triggered, model phrases.
**Notes:** Maps to D-08. Same posture as the verdict guard.

---

## Claude's Discretion

- Call strategy: single structured-output call over all vendors at once; sectioned/per-dimension split is a researched contingency built only if truncation appears (mirrors P3 D-06).
- Dimension derivation: mapping the 6 dimensions onto ExtractionResult fields.
- Streaming: reuse P3 SSE spine (status events align→comparability→compare→clarify→done + final grounded result); never stream a pre-clamp verdict.
- Exact ComparisonResult / sub-model field names, the field→dimension contribution map, and attention-trigger thresholds.
- Number of comparison traces (≥1 required).
- Code-level test structure (clamp downgrade-only, no aggregation over missing, code-seeded clarifications, attention points trace to a trigger, no reorder by readiness).

## Deferred Ideas

- Sectioned/per-dimension comparison call — researched contingency, not speculative.
- Vendor Comparison screen / line-item table UI / in-app comparison-trace viewer — Phase 5.
- Weighted/numeric scoring, should-cost engine, currency reconciliation — permanently out of scope (§24), not deferred.
- Stateful clarification → re-extraction feedback loop — v2 (FLOW-01/FLOW-02).
