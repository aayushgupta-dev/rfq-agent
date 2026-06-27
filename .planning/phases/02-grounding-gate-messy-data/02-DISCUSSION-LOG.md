# Phase 2: Grounding Gate & Messy Data - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-27
**Phase:** 2-grounding-gate-messy-data
**Areas discussed:** Grounding match strategy, Grounding gate contract, Vendor-gen pipeline, Doc shape & mess testing

---

## Grounding match strategy

### Q: How does the gate locate evidence in the source text?
| Option | Description | Selected |
|--------|-------------|----------|
| Search & recompute | Ignore model offsets; search source for snippet, recompute & overwrite real offsets | ✓ |
| Verify model offsets | Check `source[start:end]` matches snippet; downgrade if not | |

### Q: How aggressively do we normalize before matching?
| Option | Description | Selected |
|--------|-------------|----------|
| Moderate | Whitespace collapse + case-fold + NFKC + smart quotes/dashes; keep digits/currency | ✓ |
| Aggressive | + strip all punctuation/symbols (risks `$1,200`≈`1200`) | |
| Minimal | Whitespace + case only (over-rejects on PDF artifacts) | |

### Q: What fuzzy fallback fires when normalized-exact misses, and at what bar?
| Option | Description | Selected |
|--------|-------------|----------|
| rapidfuzz partial, ~90 | `partial_ratio` sliding window, accept ≥~90, tuned in tests | ✓ |
| Exact-only, no fuzzy | No fuzzy stage (roadmap calls for fuzzy fallback) | |
| token_set_ratio, ~85 | Order-independent token overlap (lets recombined snippets slip) | |

**Notes:** All recommended. Offset recompute requires normalized→original index remapping — flagged
as a planner/research wrinkle, not a user decision.

---

## Grounding gate contract

### Q: What does the gate operate on?
| Option | Description | Selected |
|--------|-------------|----------|
| Field core + generic walker | Pure `ground_field` + schema-agnostic recursive `Field[T]` walker; testable now | ✓ |
| ExtractionResult only | Single function over the whole result; couples to a P3 schema that doesn't exist | |

### Q: What does the gate do on a failed (ungrounded) span?
| Option | Description | Selected |
|--------|-------------|----------|
| Return new + downgrade report | Pure: new object with `unsupported`/cleared fields + structured report | ✓ |
| Mutate in place, no report | In-place downgrade, no record of what was rejected | |

### Q: How is the source text supplied to the gate?
| Option | Description | Selected |
|--------|-------------|----------|
| source_id → text map | `dict[str,str]` keyed by `Evidence.source_id`; multi-source ready | ✓ |
| Single source string | One string, ignores `source_id` | |

**Notes:** All recommended.

---

## Vendor-gen pipeline

### Q: One-pass or two-pass generation?
| Option | Description | Selected |
|--------|-------------|----------|
| One-pass (persona + mess spec) | `vendor-gen` emits messy directly; `messy-data-gen` = embedded taxonomy | ✓ |
| Two-pass (draft → mess transform) | Clean draft then inject mess; explicit seam but "vandalized" artifacts | |

### Q: How are the per-vendor mess specs defined?
| Option | Description | Selected |
|--------|-------------|----------|
| Hand-authored in code | Explicit specs per persona; DATA-03 tests can assert each issue type | ✓ |
| LLM-chosen per vendor | Model picks issues; can't assert specifics, reproducibility suffers | |

### Q: How many vendors, and how distinct?
| Option | Description | Selected |
|--------|-------------|----------|
| 3 complementary personas | pricey/over-scoped · cheap/incomplete · fluff/conflicting | ✓ |
| 4 personas | + multi-currency/tax or partial-scope specialist; more time cost | |

**Notes:** All recommended.

---

## Doc shape & mess testing

### Q: How is the generated RFQ represented?
| Option | Description | Selected |
|--------|-------------|----------|
| Structured + rendered doc | Structured `RFQ` pydantic via structured output + rendered Markdown | ✓ |
| Free-text doc only | Prose only; P5 would re-parse, lose typed RFQ | |

### Q: How is a vendor response represented?
| Option | Description | Selected |
|--------|-------------|----------|
| Raw messy text + provenance | Raw doc text + metadata; IS the extraction/grounding input | ✓ |
| Pre-structured fields | Filled structured object; defeats the phase | |

### Q: How do we assert messiness in tests (DATA-03)?
| Option | Description | Selected |
|--------|-------------|----------|
| Assert on committed samples | Deterministic fixtures; assert declared issue types detectable | ✓ |
| Assert on live generation | Regenerate in test; flaky, slow, burns API | |

**Notes:** All recommended. Surfaced the RFQ-structured vs vendor-raw-text asymmetry during this area.

---

## Claude's Discretion

- Module layout/function names for the gate beyond the D-05–D-07 contract shape; report data structure.
- Normalization pipeline ordering + exact fuzzy threshold (tuned in tests).
- Persona prose styles / format-divergence details beyond the 3 failure profiles.
- Sample fixture storage layout under `data/` and the live-regen API surface.
- PROMPT-04 failure-example capture approach (assumed: harvest a real failure during prompt authoring).

## Deferred Ideas

- File upload / best-effort binary text extraction — Phase 5 (INPUT-02).
- RFQ Overview / Vendor Input screen rendering — Phase 5 (UI-01/UI-02).
- Extraction agent producing the facts the gate validates — Phase 3.
- 4th vendor persona (multi-currency/tax or partial-scope) — possible later enrichment.
