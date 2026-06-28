---
phase: 04-comparison-agent
slug: comparison-agent
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-28
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| POST /compare/vendors → ComparisonRequest | Untrusted HTTP payload; pydantic validates ExtractionResult[]+RFQ; vendor count guard rejects <2 or >5 vendors (422) | list[ExtractionResult] + RFQ |
| compare node → model (ComparisonDraft) | Model receives serialised ExtractionResult JSON; may only emit ComparisonDraft (proposed verdicts + phrasing) — structurally cannot emit ComparisonResult, clamp_report, line_item_offers, or vendor_readiness | ComparisonDraft |
| _apply_verdict_clamp → ComparisonDimension StrEnum | Unknown/mis-cased dimension strings coerced via StrEnum; ValueError → skip, default not_comparable applies | Dimension key |
| clarify node → model (ClarificationSet) | Model receives code-collected FlaggedField list; count+identity validated before accepting questions; extras dropped | ClarificationSet |
| SSE boundary | Exactly one result event emitted by clarify node after clamp+clarification; compare node stores, never emits | ComparisonResult JSON |
| fixture trace → clamp | Deterministic all-comparable draft injected; real _apply_verdict_clamp runs against real ExtractionResult; has_downgrades asserted before write | ComparisonDraft (fixture) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-01-SC | Tampering | No new npm/pip installs (Wave 1) | accept | No package installs; all deps from Phases 1–3 | closed |
| T-04-01-01 | Tampering | conftest builders could produce invalid ExtractionResult on schema change | mitigate | Pydantic construction validates on instantiation; missing_extraction/present_extraction/partial_extraction all call ExtractionResult(...) with live pydantic validation — conftest_comparison.py:54,71,95 | closed |
| T-04-01-02 | Tampering | E2E clamp test could mock too shallowly and pass when real clamp is broken | mitigate | test_clamp_applied_to_result asserts on state["result_sse_event"] (emitted SSE payload), not a return value — test_comparison_agent.py:716-717,957; clamp assertion traverses parsed ComparisonResult from the result event | closed |
| T-04-02-01 | Tampering | ComparabilityVerdict added to envelope.py FlagStatus | mitigate | ComparabilityVerdict(StrEnum) defined in schemas/domain.py:175; test_schema_shape asserts __module__ contains 'domain' | closed |
| T-04-02-02 | Tampering | dict[str, Model] shape in ComparisonResult breaks TS contract | mitigate | All ComparisonResult fields use list[BaseModel]; test_no_dict_shapes asserts no dict origin annotation; drift-check test passes | closed |
| T-04-02-03 | Spoofing | vendor_count/comparable stub fields left in schema, confusing agents | mitigate | Old stub fields deleted; grep for vendor_count/comparable in domain.py returns no class fields; test_schema_shape asserts 'vendor_count' not in model_fields | closed |
| T-04-02-04 | Tampering | Model-authored clamp_report or line_item_offers via ComparisonResult as structured output target | mitigate | _comparison_chain uses .with_structured_output(ComparisonDraft, ...) — comparison.py:100-102; ComparisonDraft has only {dimensions, narrative_summary} — domain.py:283-284; clamp_report/line_item_offers/vendor_readiness structurally absent from ComparisonDraft | closed |
| T-04-02-05 | Tampering | Free-string dimension key join: mis-cased "Commercial" bypasses clamp | mitigate | ComparisonDimension(StrEnum) in domain.py:191; _apply_verdict_clamp wraps dim string in ComparisonDimension() at comparison.py:274, ValueError caught, dimension skipped, default not_comparable matrix entry applies — comparison.py:275-278 | closed |
| T-04-02-06 | Tampering | ClarificationSet defined outside domain.py drift-check scope | mitigate | ClarificationSet in domain.py:387; test_schema_shape asserts __module__ contains 'domain'; pydantic2ts picks it up in codegen | closed |
| T-04-03-01 | Tampering | Model-proposed comparable verdict over missing field elevated without clamp | mitigate | _apply_verdict_clamp is fail-closed: 6×N matrix pre-filled not_comparable; clamp_verdict downgrade-only — comparison.py:246-333; test_clamp_applied_to_result asserts emitted result is not_comparable for vendor with missing pricing — test_comparison_agent.py:654-730 | closed |
| T-04-03-02 | Tampering | Model emits ComparisonResult (not ComparisonDraft) and bypasses code construction | mitigate | with_structured_output(ComparisonDraft) at comparison.py:100-102; isinstance(parsed, ComparisonDraft) type check at comparison.py:750; test_schema_shape asserts 'clamp_report' not in ComparisonDraft.model_fields | closed |
| T-04-03-03 | Tampering | Free-string dimension key join bypasses clamp for mis-cased dimension | mitigate | ComparisonDimension(StrEnum) coercion in _apply_verdict_clamp at comparison.py:274; ValueError → skip, default not_comparable — comparison.py:275-278; test_dimension_enum_fail_closed GREEN | closed |
| T-04-03-04 | Tampering | Model invents attention points not in code trigger list | mitigate | _build_attention_shells builds shells from code triggers; model fills summary only; model_by_type lookup at comparison.py:779-793 drops any trigger_type not in code-detected shells; test_attention_points_are_triggered asserts fabricated point dropped | closed |
| T-04-03-05 | Tampering | Model invents clarification questions for un-flagged fields | mitigate | Identity validation (vendor_name, field_path, flag_status) tuple set at comparison.py:866-876; non-matching questions dropped with logger.warning; test_clarification_seeded_by_code asserts extras dropped | closed |
| T-04-03-06 | Tampering | Double result SSE event; pre-clamp result leaks | mitigate | compare node stores result in state, does NOT emit — comparison.py:807-812; clarify node emits the single result event at comparison.py:894-900; test_comparison_sse_taxonomy asserts exactly one result event — test_comparison_agent.py:376,461 | closed |
| T-04-03-07 | Tampering | Offer table contains model-authored (potentially normalised) values | mitigate | _build_offer_table constructs from ExtractionResult.line_items verbatim values only — comparison.py:341-367; model cannot populate this table; test_offer_table_code_built asserts code-built, no normalized fields | closed |
| T-04-03-08 | Denial of Service | Oversized ExtractionResult[] payload (>5 vendors) | mitigate | ComparisonRequest._check_vendor_count model_validator rejects n>5 and n<2 with ValueError (→ FastAPI 422) — app.py:191-205 | closed |
| T-04-03-09 | Tampering | Raw vendor text passed to comparison (grounding boundary breach) | mitigate | _run_align_impl checks isinstance(e, ExtractionResult) for each input at comparison.py:611-623; emits error and returns early on type mismatch; ExtractionResult schema has no raw_text field | closed |
| T-04-03-SC | Tampering | npm/pip/cargo installs (Wave 3) | accept | No new packages installed; all deps from Phases 1–3 | closed |
| T-04-04-01 | Tampering | comparison.v1.md permits model to normalise values | mitigate | Explicit no-normalization instruction present at comparison.v1.md:178; prompts verified by automated assert ('normali' in comp_body) per 04-04 verify step | closed |
| T-04-04-02 | Tampering | comparison.v1.md omits model_proposed requirement; clamp trace cannot be produced | mitigate | "## REQUIRED: model_proposed per verdict" section at comparison.v1.md:145-151; automated assert confirms 'model_proposed' and 'required' in prompt body | closed |
| T-04-04-03 | Tampering | clarification.v1.md allows model to generate questions for unlisted fields | mitigate | "MUST produce exactly as many ClarificationQuestion objects as there are flagged fields" at clarification.v1.md:79-81; 'exactly' confirmed in prompt body | closed |
| T-04-04-04 | Information Disclosure | Trace captures full ExtractionResult JSON with vendor pricing data | accept | Prototype only; no real PII; trace committed to docs/ as graded submission deliverable per D-11 | closed |
| T-04-04-05 | Tampering | Trace committed with 0 clamp entries (no downgrade shown — rubric fails) | mitigate | _build_comparison_trace checks has_downgrades and calls sys.exit(1) if False — capture_comparison_trace.py:129-136; comparison_trace_1.json confirmed with 7 clamp entries; test_comparison_traces_committed asserts len >= 1 | closed |
| T-04-04-06 | Tampering | Trace misleads reviewer if fixture nature is hidden | mitigate | _fixture_mode:true in comparison_trace_1.json (confirmed key present); "## 6. Fixture Mode Note" section in comparison_trace_1.md; capture_comparison_trace.py:297-318 | closed |
| T-04-04-SC | Tampering | No new package installs (Wave 4) | accept | Zero new dependencies confirmed | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-01-SC | No package installs in Wave 1 — all deps from Phases 1–3; risk is hypothetical | Phase 04 executor | 2026-06-28 |
| AR-04-02 | T-04-03-SC | No package installs in Wave 3 — all deps from Phases 1–3 | Phase 04 executor | 2026-06-28 |
| AR-04-03 | T-04-04-04 | Comparison trace JSON committed to docs/ exposes vendor pricing verbatim values from extraction fixtures. Accepted for prototype: (a) data is synthetic/generated, not real vendor PII; (b) docs/traces/ is the graded submission artifact required by assignment §20/D-11; (c) no real money or identity data in the committed trace. Re-evaluate before any production deployment. | Human (2026-06-28 checkpoint) | 2026-06-28 |
| AR-04-04 | T-04-04-SC | No package installs in Wave 4 — zero new dependencies | Phase 04 executor | 2026-06-28 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags from SUMMARY.md Threat Flags

Wave 1 (04-01-SUMMARY.md): "No new network endpoints, auth paths, file access, or schema changes introduced — test-only files." — no unregistered flag.

Wave 2 (04-02-SUMMARY.md): "No new network endpoints, auth paths, or file access patterns. Schema-only change." — no unregistered flag.

Wave 3 (04-03-SUMMARY.md): New SSE endpoint POST /compare/vendors flagged. Maps to T-04-03-08 (DoS/vendor count guard) and T-04-03-09 (grounding boundary). Both mitigated. No unregistered flag.

Wave 4 (04-04-SUMMARY.md): "No new security-relevant surface introduced." — no unregistered flag.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-28 | 25 | 25 | 0 | gsd-security-auditor (claude-sonnet-4-6) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-28
