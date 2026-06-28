---
phase: 4
reviewers: [codex, ollama, opus-agent]
reviewed_at: 2026-06-28
plans_reviewed: [04-01-PLAN.md, 04-02-PLAN.md, 04-03-PLAN.md, 04-04-PLAN.md]
verdict: HIGH concerns — replan required
---

# Cross-AI Plan Review — Phase 4 (Comparison Agent)

Three independent reviewers (Codex, Ollama/minimax-m2.5:cloud, and an Opus-backed reviewer
agent following the GSD plan-review criteria) reviewed all four Phase 4 plans against the
phase goal, the locked decisions (D-01..D-11), and the project's non-negotiable reliability
bar (CLAUDE.md §1/§2/§8: evidence over assertion, absence first-class, **grounding enforced
in code, never on the model's word**).

**Headline:** The reliability *architecture* (the verdict clamp) is sound and well-aligned
with the phase goal — all three reviewers agree. But the plans **delegate too many
code-owned, reliability-critical surfaces to the model's word**, and the single most
important behavior — the clamp applied to the *real* model result — is **not tested
end-to-end**. These are fixable before Wave 3 executes.

---

## Codex Review

**Summary:** Right product thesis (qualitative, clamp-first, evidence-aware, traceable), but
the implementation still delegates too many code-owned surfaces to the model. Biggest risks:
`ComparisonResult` is both the model-output schema *and* the final trusted schema;
`line_item_offers` / readiness / attention points can be model-invented; the trace depends on
live model misbehavior to prove the clamp. **Would not execute unchanged.**

**Concerns:**
- **HIGH — `ComparisonResult` should not be the raw model output schema.** It contains
  code-owned fields (`clamp_report`, `model_proposed`, final clamped verdicts, readiness,
  offer table, attention points, clarifications). Asking the model to emit it invites
  hallucinated clamp reports and model-authored "final" data. Use a separate
  `ComparisonDraft` for model output; construct `ComparisonResult` in code.
- **HIGH — light alignment is not enforced in code.** The model produces `line_item_offers`;
  a prompt saying "do not normalize" is not enough. Build the offer table in code directly
  from `ExtractionResult.line_items[*].pricing/scope_coverage`, preserving verbatim values +
  evidence paths. Otherwise computed prices / currency conversions / paraphrases can slip in.
- **HIGH — attention points are only partly code-seeded.** Code detects triggers, but the
  model still emits `attention_points`; the "do not add entries not in trigger list"
  instruction is not enforced. Code should build one `AttentionPoint` shell per trigger
  (model fills only `summary`) or filter model output against trigger IDs.
- **HIGH — clarification questions are not constrained after model output.** Tests only check
  `_collect_flagged_fields`, not that model output matches the seeded set. Add code
  validation: same count, same `(vendor_name, field_path, flag_status)` set, no extras/omissions.
- **HIGH — missing dimensions/vendors can bypass the clamp.** `_apply_verdict_clamp` walks
  `result.dimensions`; if the model omits a dimension/vendor or emits an unexpected vendor
  name, there is nothing to clamp. Code must validate and complete the full 6×N matrix.
- **HIGH — trace generation depends on live model error.** `clamp_step.entries >= 1` requires
  the model to misbehave, but the prompt strongly instructs correct downgrades. Use a
  deterministic injected over-optimistic raw draft / fixture mode so the clamp proof is stable.
- **MEDIUM — grounding boundary underspecified:** `/compare/vendors` is schema-validated, not
  necessarily grounding-gate-validated. Name the trust assumption or add a provenance marker.
- **MEDIUM — empty-list semantics:** `_ceiling_for_flags([])` likely returns `comparable`
  unless special-cased; a dimension with no flags could be called comparable.
- **MEDIUM — COMPARE-02 is per dimension *and* line-item**, but the schema is mostly per
  dimension; `LineItemOffer` lacks a line-item-level verdict/reason.
- **MEDIUM — two `result` SSE events** (compare emits one, clarify emits an updated one).
- **MEDIUM — test plan contradiction:** RED stubs raise `NotImplementedError` yet "full suite
  green" is claimed; mark `xfail` or run targeted tests.
- **LOW — 04-01 says 12 stubs but lists 13.**

**Risk Assessment: HIGH** — concept strong, but plans rely too much on prompt obedience for
reliability-critical outputs. Moving offer/readiness/trigger/clarification construction into
code and splitting raw-draft from final-result drops risk to MEDIUM/LOW.

---

## Ollama Review (minimax-m2.5:cloud)

**Summary:** Well-structured; achieves comparability-before-ranking with code-enforced guards.
The verdict clamp (`min(model_verdict, code_ceiling)`) is the headline reliability move and
mirrors the Phase 3 grounding gate. Correct wave ordering. Several HIGH concerns around clamp
enforcement, prompt completeness, and the dimension-contribution map.

**Strengths:** clamp architecture sound (`_VERDICT_ORDER` deterministic); grounding boundary
transitive (`isinstance` check); schema avoids `dict[str,Model]`; `ComparabilityVerdict` in
`domain.py` (WR-01 resolved); clarification seeding code-driven; comprehensive 13-stub coverage.

**Concerns:**
- **HIGH — `model_proposed` is not required by the prompt.** The clamp needs the model's raw
  verdict to compute the trace diff, but `comparison.v1.md` never instructs the model to emit
  `model_proposed` alongside the clamped verdict. Add it to the output-format section.
- **HIGH — field→dimension contribution map may be incomplete.** Hand-coded for a fixed
  6-dimension set; misses future `ExtractionResult` fields (`assumptions`, `exclusions`) and
  can't adapt to new dimensions. Add a coverage test that fails fast if the schema adds fields.
- **HIGH — `cross_vendor_conflict` detection is underspecified.** How does code detect "same
  field conflicting across vendors"? Implement `_detect_conflicts` over common field paths;
  test two vendors with conflicting timelines → trigger emitted.
- **MEDIUM — clarification failure proceeds silently** (empty list reads as "no issues"); add
  an `AttentionPoint(trigger_type="clarification_generation_failed")`.
- **MEDIUM — no validation that vendor line items align with the RFQ's 8 line items**; a
  vendor with different line items would be aligned incorrectly. Flag `not_comparable` for scope.
- **LOW — `_MAX_VENDORS = 5` hardcoded** (document the prototype limitation).
- **LOW — trace may show 0 downgrades if vendors are too clean** (warning, still commits).

**Risk Assessment: MEDIUM** — core mechanism sound and well-tested; address the three HIGH
concerns (prompt `model_proposed`, contribution-map coverage, conflict detection) before Wave 3.

---

## Opus Reviewer Agent Review

**Summary:** Plans achieve the goal **honestly and with unusual rigor**. The reliability spine
is *not* wrong — guard order is correct (ceiling computed before the model call, clamp applied
before the `result` emit), WR-01 closed by construction, grounding boundary enforced in code,
no-leaderboard defended at multiple layers. The concerns are about **the gap between the
clamp's intent and what the tests actually prove**, plus schema/type seams and verdict-ordering
edge cases. None rise to "this phase will fabricate"; most are "the test doesn't prove what the
plan claims."

**Concerns:**
- **HIGH — the clamp tests prove the *primitives*, not the clamp-over-the-real-result.**
  `test_clamp_only_downgrades` only calls `clamp_verdict(...)` / `_ceiling_for_flags(...)` on
  hand-built scalars. **No test injects a mocked model `ComparisonResult` with `comparable`
  over a missing field and asserts the *emitted result event's* verdict was downgraded to
  `not_comparable`.** `_apply_verdict_clamp` — the most reliability-critical function — is
  untested end-to-end. RESEARCH Pitfall 1 describes exactly this test in prose but it never
  became a stub.
- **HIGH — the dimension-name binding is an unverified string-key join.** `dimension` is a free
  `str` on `DimensionComparison` (the `# 'technical'|'commercial'|...` is a *comment*, not an
  enum). If the model returns `"Commercial"` or omits a dimension, `ceilings[dv.dimension][...]`
  `KeyError`s or silently misses → **clamp does not apply → a model `comparable` over a missing
  field survives.** The fallback is unspecified (raise? `.get()` default `comparable` = bypass?).
  Fix: make `dimension` a `ComparisonDimension(StrEnum)`; default any unmatched/missing
  dimension to `not_comparable` (**fail closed**); test a mis-cased/unknown dimension.
- **HIGH — `partially`/empty-ceiling underspecified → possible silent upgrade.**
  `_ceiling_for_flags([])` (a dimension where a vendor contributed zero fields — empty
  `compliance_points`, empty `risks[]`) returns `comparable` via fall-through. But the
  field→dimension map says "empty compliance = partially" — a direct contradiction → an
  all-empty-compliance vendor gets `comparable`, the opposite of D-04. Define the
  zero-contributing-fields branch explicitly, per dimension, with tests.
- **MEDIUM — `ClarificationSet` is referenced as a structured-output schema but defined inside
  `comparison.py`, outside the contract/drift-check.** Define it in `domain.py` next to
  `ClarificationQuestion`, or drop it and return `list[ClarificationQuestion]`.
- **MEDIUM — clarify-node failure introduces a second `result` emission path** (compare emits
  `result`, clarify emits an updated `result`) → two `result` events, contradicting the clean
  `status…→result→done` sequence; `test_comparison_sse_taxonomy` won't catch it. Pick one
  `result`-emit path.
- **MEDIUM — `test_attention_points_are_triggered` tests the detector, not the "no fabricated
  point" guarantee.** D-08's claim ("the panel cannot surface a point the data doesn't
  support") is asserted only by prompt instruction = **on the model's word (§2 violation)**.
  Intersect model `attention_points` against the code trigger set; test that a fabricated point
  is dropped.
- **MEDIUM — `cross_vendor_conflict` detector is semantically wrong.** `conflicting` is a
  *per-field* FlagStatus (a vendor's own field), not a cross-vendor relation. Two vendors with
  different `present` timelines is the real cross-vendor conflict and is invisible to a
  `status == conflicting` check → the trigger is near-dead. Clarify what it detects.
- **LOW — vendor-count guard:** plan says 400, FastAPI `ValueError` → 422 (internal
  inconsistency). **LOW — `min_lines` floors invite padding** (demote to advisory). **LOW —
  trace test asserts a property of a captured file, not of the code** (known-flaky).

**Risk Assessment: MEDIUM** — design correct; risk is the gap between claims and verification.
An executor could ship all 13 tests GREEN with a clamp that silently no-ops on a mis-cased or
empty dimension — exactly the failure this reliability-defining phase exists to prevent. With
the end-to-end clamp test + StrEnum-fail-closed dimension + explicit empty-ceiling semantics,
the phase drops to LOW.

---

## Consensus Summary

### Agreed Strengths (2+ reviewers)
- The verdict-clamp architecture (`min(model_verdict, code_ceiling)`, downgrade-only) is sound
  and correctly mirrors the Phase 3 grounding gate. (all three)
- `ComparabilityVerdict` as a new `domain.py` StrEnum (never on `FlagStatus`) is the right
  boundary — WR-01 resolved by construction. (all three)
- Grounding boundary is enforced in code (`isinstance(e, ExtractionResult)`) and transitive —
  `ExtractionResult` carries no raw text. (Ollama, Opus)
- No-leaderboard / no-sort-key is defended at the schema + test layers. (Ollama, Opus)
- Wave ordering (tests → schema → agent → prompts/trace) is correct. (all three)
- Prompt requirements are concrete (verdict definitions, no-normalization, humility, few-shots).
  (Codex, Ollama)

### Agreed Concerns (priority order — these drive the replan)
1. **[BLOCKER] The clamp is not verified end-to-end, and a real bypass path exists.** No test
   asserts the clamp downgrades a *mocked model result*; and the `dimension` free-string key
   join is fail-open — a mis-cased/omitted dimension silently bypasses the clamp, letting a
   model `comparable` over a missing field survive. (Opus HIGH×2; Codex HIGH "missing
   dimensions bypass clamp"; Ollama HIGH "contribution map") →
   **Fix:** add `test_clamp_applied_to_result` (mock model → assert emitted verdict downgraded
   + `model_proposed` recorded); make `dimension` a `ComparisonDimension(StrEnum)`; in
   `_apply_verdict_clamp` default any unmatched `(dimension, vendor)` to `not_comparable`
   (**fail closed**); validate the full 6×N matrix is present before emit.
2. **[BLOCKER] Reliability-critical surfaces are model-authored, not code-owned (§2 violation).**
   The model emits the final `ComparisonResult` including `attention_points`, `line_item_offers`,
   readiness, clamp report, clarifications — guarded only by prompt instruction. (Codex HIGH×3;
   Opus MEDIUM attention/clarification; Ollama on clarification) →
   **Fix:** model emits a **draft** (proposed per-dimension verdicts + phrasing only); **code**
   constructs/validates the final result — build the offer table from verbatim
   `ExtractionResult` values + evidence; build one `AttentionPoint` shell per code-detected
   trigger (model fills only `summary`, code drops any model-invented point); validate the
   clarification set exactly matches `_collect_flagged_fields` (count + identity, reject extras).
3. **[BLOCKER] The model's raw verdict (`model_proposed`) is never required by the prompt**, yet
   the clamp diff / trace depends on it. (Ollama HIGH; Codex implies via draft split; Opus via
   the e2e test) → **Fix:** require `model_proposed` in `comparison.v1.md` output format (or
   capture it from the draft schema before clamping).
4. **[HIGH] Empty / zero-contributing-fields ceiling is unspecified and contradicts the
   compliance map** → silent upgrade to `comparable`. (Opus HIGH; Codex MEDIUM; Ollama HIGH) →
   **Fix:** explicit per-dimension empty-field branch + tests (empty compliance → at least
   `partially`; empty risks → per RESEARCH A2).
5. **[HIGH] The D-11 trace depends on live, non-deterministic model misbehavior.** (Codex HIGH;
   Opus LOW; Ollama LOW) → **Fix:** capture the trace from a deterministic injected
   over-optimistic raw draft (fixture mode) so the clamp downgrade is always demonstrable.
6. **[MEDIUM] Double `result` SSE emission** from the clarify node. (Codex, Opus) → emit exactly
   one final `result` after clamp + clarification; use `status`/`partial` for progress.
7. **[MEDIUM] `cross_vendor_conflict` detector is wrong/underspecified** — `conflicting` is
   per-field, not cross-vendor. (Ollama HIGH, Opus MEDIUM) → define detection over differing
   values across vendors; add a test.
8. **[MEDIUM] No validation that vendor line items map to the RFQ's 8 line items.** (Ollama) →
   validate; flag scope `not_comparable` on mismatch.
9. **[MEDIUM] `ClarificationSet` lives outside the contract/drift-check.** (Opus) → move to
   `domain.py` or return `list[ClarificationQuestion]`.
10. **[LOW] cleanups:** 400→422 acceptance note (Opus); 12-vs-13 stub count (Codex); RED-stub vs
    "full suite green" contradiction (Codex); `_MAX_VENDORS=5` documented as a prototype limit
    (Ollama); demote `min_lines` to advisory (Opus).

### Divergent Views
- **Light-alignment / offer-table enforcement:** Ollama rated the schema-level `LineItemOffer`
  (no normalized fields, `non_equivalence_flag`) a **strength**; Codex rated it a **HIGH**
  concern because the *model* still populates the offer table and a type with no normalized
  fields doesn't stop the model from writing a computed value into a verbatim field. **Resolution
  for replan:** side with Codex/Opus — build the offer table in code from `ExtractionResult`
  verbatim values; the schema shape alone is necessary but not sufficient.
- **Overall risk:** Codex = HIGH, Ollama = MEDIUM, Opus = MEDIUM. The HIGH-vs-MEDIUM split is
  about *likelihood of shipping a bypass*, not about the design — all three agree the fixes are
  pre-Wave-3 and don't require re-architecting.

### Verdict
**Replan required.** Multiple consensus BLOCKER/HIGH concerns center on the project's defining
rule — *grounding enforced in code, never on the model's word* (CLAUDE.md §2/§8). Re-plan
Phase 4 with `--reviews` to: (1) split model-draft from code-constructed final result, (2) make
the clamp fail-closed on dimension/vendor key with an end-to-end test, (3) resolve empty-ceiling
semantics, (4) require `model_proposed`, (5) make the trace deterministic, and (6) fold in the
MEDIUM/LOW cleanups.
