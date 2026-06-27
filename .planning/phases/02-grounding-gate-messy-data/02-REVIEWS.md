---
phase: 2
reviewers: [codex, ollama]
reviewed_at: 2026-06-27T14:30:01Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md, 02-04-PLAN.md]
unavailable_reviewers:
  - claude (skipped — orchestrator runs inside Claude Code; skipped for review independence)
  - opencode (insufficient account balance)
  - cursor (authentication required — not logged in)
  - gemini, qwen, coderabbit (CLI not installed)
  - lm_studio, llama_cpp (no local server running)
---

# Cross-AI Plan Review — Phase 2: Grounding Gate & Messy Data

> 2 independent external reviewers (Codex / OpenAI, Ollama / minimax-m2.5). Claude skipped for
> independence (orchestrator IS Claude Code). Feed back into planning via `/gsd:plan-phase 2 --reviews`.

---

## Codex Review

## Plan 02-01

**Summary:** Good intent: it front-loads falsifiability tests and fixture tests before implementation. The main issue is a serious contradiction in the RED test design.

**Strengths**
- Establishes the grounding gate API and downgrade report before implementation.
- Includes the two key phase-goal tests: fabricated evidence downgraded, genuine evidence preserved.
- Fixture tests are correctly deterministic against committed files, not live LLM calls.
- Keeps `rapidfuzz` out of stubs, avoiding dependency failure before 02-02.

**Concerns**
- **HIGH:** The instruction to “wrap each test body in `pytest.raises(NotImplementedError)`” conflicts with the stated RED goal. Those tests would pass against stubs and then fail after implementation unless rewritten. RED tests should call the functions normally and fail with `NotImplementedError`.
- **MEDIUM:** `test_sample_fixtures.py` references future `RFQ.line_items` and `VendorResponse.raw_text` while schemas are still stubs. Collection may fail with `AttributeError` depending on test shape, not just missing files.
- **MEDIUM:** The conflicting-field test expectation is underspecified. If one conflicting value fails, the whole field should become `unsupported`, but the plan also says “fabricated CV is downgraded and genuine CV survives,” which suggests partial preservation.

**Suggestions**
- Remove all `pytest.raises(NotImplementedError)` wrappers. Let the tests fail naturally.
- For fixture tests, assert file existence before model field access so pre-02-03 failure is `AssertionError`/missing file, not schema mismatch.
- Define the conflicting-field expected behavior explicitly: any failed evidence downgrades the whole `Field` to `unsupported`.

**Risk Assessment: MEDIUM**
The harness is useful, but the `pytest.raises` instruction can invert the RED→GREEN workflow and break 02-02.

---

## Plan 02-02

**Summary:** This is the strongest plan technically and directly targets the headline reliability rule: code verifies spans, ignores model offsets, and downgrades unsupported facts. A few offset-mapping and downgrade-report details need tightening.

**Strengths**
- Correctly keeps grounding pure, deterministic, and LLM-free.
- Explicitly ignores model-supplied offsets and recomputes them.
- Handles exact match, fuzzy fallback, short-snippet guard, conflicting fields, and recursive pydantic traversal.
- Uses `rapidfuzz.partial_ratio_alignment`, which is appropriate for fuzzy substring matching with offsets.

**Concerns**
- **HIGH:** The normalization map algorithm using `.strip()` plus `surviving_positions[:len(normalized)]` is wrong when normalized text has leading whitespace. It can shift offset mappings.
- **HIGH:** `_ground_evidence_item` sets `original_status="present"` or even `original_status=ev.source_id` in examples. `original_status` should come from the enclosing field’s actual status.
- **MEDIUM:** Short-snippet guard downgrades even exact matches like `Q3`. That is defensible, but it means “genuine evidence present passes” is not universally true. Tests and docs should frame this as an intentional reliability tradeoff.
- **MEDIUM:** Conflicting fields: “any downgrade → unsupported” is simple and safe, but it discards genuine conflicting values too. That matches conservative grounding, but should be explicitly documented.
- **LOW:** `ground_model(obj: BaseModel, ...)` may miss `dict[str, Field]` or nested dict values. Probably acceptable for P2, but worth noting before P3 schemas settle.

**Suggestions**
- Fix normalization stripping by tracking start/end indices before composing `orig_indices`, or avoid `.strip()` and instead trim both normalized text and mapping together.
- Pass `field.status` into `_ground_evidence_item` so `DowngradeEntry.original_status` is accurate.
- Add explicit tests for source-id missing and pure-function non-mutation.
- Add empty-snippet / empty-source guards to avoid index errors in `_match_exact` and `_match_fuzzy`.

**Risk Assessment: MEDIUM**
The plan achieves the grounding goal if implemented carefully, but the offset-map bug could produce incorrect highlights, which is central to the phase.

---

## Plan 02-03

**Summary:** The schema and prompt work is mostly well-scoped and aligned with the phase. It avoids pre-extracting vendor facts, which is important. The main risk is schema looseness around `mess_spec` and structured-output compatibility.

**Strengths**
- Correctly keeps RFQ as plain structured data, not grounded `Field[T]`.
- Correctly keeps `VendorResponse` as raw messy text plus provenance, not pre-extracted claims.
- Includes shared TS type regeneration and drift test.
- Prompts explicitly address realism, messiness, anti-hallucination, and format diversity.

**Concerns**
- **MEDIUM:** `mess_spec: list[dict]` is loose. It weakens the contract and generated TS types. A small `MessSpecItem` pydantic model would be safer and still lightweight.
- **MEDIUM:** “line_items with ≥8 field minimum” in must-haves conflicts with the actual schema having no validator. Tests later require exactly 8. The schema/prompt/test contract should be consistent.
- **MEDIUM:** Updating `messy-data-gen` frontmatter `model_tier` to `cheap` may conflict with “preserve frontmatter exactly.” It is probably fine if tests only require keys, but the plan contradicts itself.
- **LOW:** RFQ date strings are unconstrained. Fine for prototype, but generation tests may accept nonsensical dates unless fixture tests inspect them.
- **LOW:** Prompt says “Do not invent technology vendors, awards, or client names not established” but also asks for a specific client name. The RFQ prompt should establish allowed invented-but-realistic fictional context clearly.

**Suggestions**
- Add a `MessSpecItem` model with `line_item: str`, `issue_type: str`, `instruction: str`; use `list[MessSpecItem]`.
- Decide whether exactly 8 line items is schema-validated or test-only. For this prototype, test-only is fine, but remove “minimum” language.
- Add prompt registry tests that assert bodies are non-TODO and non-empty beyond frontmatter.
- Keep prompt docs and prompt frontmatter aligned on whether `messy-data-gen` is a reference document or callable prompt.

**Risk Assessment: LOW-MEDIUM**
The plan supports the phase well. The risks are mostly contract clarity and future maintainability, not core reliability.

---

## Plan 02-04

**Summary:** This plan closes the loop with generation agents, fixtures, live endpoints, and Prompt Pack docs. It is directionally correct, but it has filename mismatches and some live-generation ergonomics that could cause avoidable failures.

**Strengths**
- Commits deterministic fixtures while keeping live regeneration available.
- Keeps fixture tests against committed samples, avoiding LLM flakiness in CI.
- Adds Prompt Pack documentation with failure example and versioning notes.
- Validates persona input before generating vendor responses.

**Concerns**
- **HIGH:** Filename mismatch: `generate_samples.py` writes `vendor_thorough_but_pricey.json`, `vendor_cheap_but_incomplete.json`, and `vendor_polished_fluff.json` if using `persona.replace("-", "_")`, but required files/tests expect `vendor_thorough.json`, `vendor_cheap.json`, `vendor_fluff.json`.
- **MEDIUM:** `POST /data/vendor-gen` regenerates a fresh RFQ internally every time. That proves live regen, but the caller cannot generate a vendor response against a chosen RFQ. This may limit the later in-app workflow.
- **MEDIUM:** Running `generate_samples.py` depends on live OpenAI calls. If no API key or model ID issue occurs, phase execution blocks. A fallback manual fixture-edit path should be allowed after failed live generation, while preserving regenerability.
- **MEDIUM:** The endpoint signature `async def post_vendor_gen(persona: str)` likely treats `persona` as a query parameter, not a JSON body. That is okay if intentional, but “POST” may surprise the frontend.
- **LOW:** `json.loads(model_dump_json())` is fine but unnecessary. FastAPI can return `model_dump(mode="json")`.
- **LOW:** Updating `VALIDATION.md` in an implementation plan is process-heavy and not essential to product behavior.

**Suggestions**
- Add an explicit `FIXTURE_FILENAMES` map:
  - `thorough-but-pricey -> vendor_thorough.json`
  - `cheap-but-incomplete -> vendor_cheap.json`
  - `polished-fluff -> vendor_fluff.json`
- Let `POST /data/vendor-gen` accept optional `rfq_text` or `rfq` input; if omitted, generate a fresh RFQ.
- Add a small route smoke test using FastAPI route inspection only, not live LLM calls.
- Document that sample generation is a developer script requiring `OPENAI_API_KEY`, while CI only validates committed fixtures.
- Prefer `vendor.model_dump(mode="json")` and `rfq.model_dump(mode="json")`.

**Risk Assessment: MEDIUM**
The plan achieves the data goal if the script runs, but the filename mismatch is likely to break fixture tests immediately.

---

## Overall Review

The plans are well aligned with the phase goal: they prioritize a code-enforced grounding gate, deterministic downgrade behavior, realistic messy fixtures, and prompt documentation. The biggest blockers are procedural/test-design issues rather than architectural ones:

- Fix 02-01’s `pytest.raises(NotImplementedError)` contradiction.
- Fix 02-02’s normalization mapping around stripped whitespace and accurate downgrade status reporting.
- Fix 02-04’s vendor fixture filename mismatch.

With those corrected, the plan set should achieve the core reliability rule: facts are displayable only when code can locate their evidence in source text; fabricated spans are downgraded regardless of any model assertion.

---

## Ollama Review (minimax-m2.5)

# Phase 2 Plan Review: Grounding Gate & Messy Data

## Summary

This phase implements the reliability keystone — a code-level grounding gate that verifies every evidence span against source text (never trusting model-supplied offsets) and generates deliberately messy vendor data to test extraction/comparison agents. The four plans follow a disciplined RED-before-GREEN workflow: stubs + tests (02-01), gate implementation (02-02), schema/prompt fleshing (02-03), then generation agents + live-regen API (02-04). The phase closes with all 16 automated tests GREEN and data fixtures committed.

**Overall Risk Assessment: MEDIUM**

The technical foundation is sound (rapidfuzz, two-stage normalization, NFKC offset mapping all verified via research). However, the phase carries execution risk from: (1) the fuzzy threshold calibration which is assumed at 90 but untested against actual messy data, (2) the dependency chain where 02-02 must complete before 02-04 can run generation, and (3) the need to capture a real prompt failure for PROMPT-04 which may not occur organically. The core "code that disproves the model" principle is correctly embedded throughout — D-01 explicitly ignores model offsets and recomputes from scratch.

---

## Plan-by-Plan Review

### 02-01-PLAN.md — Test Stubs + Module Stubs

**Summary**: Creates the grounding package stubs (gate.py + report.py + __init__.py) and writes all 9 EXTRACT-04 unit tests + 5 DATA fixture tests in RED state (imports resolve but tests fail with NotImplementedError/FileNotFoundError).

**Strengths**:
- Correct RED-before-GREEN discipline — tests exist before implementation, enabling falsifiability verification
- test_grounding_gate.py covers all 9 EXTRACT-04 cases including the two critical falsifiability tests (Test A: fabricated span downgraded, Test B: genuine span passes)
- test_sample_fixtures.py assertions for messiness are string-search based (not structural) per D-13, which is correct since vendor text is raw prose
- Module stubs raise NotImplementedError rather than returning dummy values — this forces implementation rather than allowing silent pass-through
- Imports structured to resolve cleanly: `from schemas.envelope import Field as EnvelopeField` avoids pydantic collision

**Concerns**:
- **MEDIUM**: The test assertions for messiness (test_vendor_fixture_messiness, test_cheap_incomplete_has_missing_price, test_polished_fluff_has_conflict) use keyword search patterns (e.g., `"TBD" in raw.lower()`). These are fragile — if the LLM generates different phrasing (e.g., "price to be confirmed" vs "TBD"), the tests fail even though messiness is present. The plan acknowledges iteration may be needed, but there's no fallback strategy if the model consistently uses unexpected phrasing.
- **LOW**: The stub functions return NotImplementedError, which is correct, but if an implementation mistake causes a stub to be called, the error message won't indicate which test failed. Consider adding the function name to the error message for faster debugging.

**Suggestions**:
1. Add a comment in test_sample_fixtures.py noting that messiness patterns are intentionally flexible per D-13, and that if the model uses unexpected phrasing, the fix is in the prompt (vendor-gen.v1.md), not the test assertion
2. In gate.py stubs, change `raise NotImplementedError` to `raise NotImplementedError("ground_field not implemented")` to include function context

**Risk Assessment: LOW** — Plan is well-structured for RED-before-GREEN. The main risk is test fragility on messiness assertions, but that's manageable through iteration.

---

### 02-02-PLAN.md — Grounding Gate Implementation

**Summary**: Installs rapidfuzz, implements the full grounding gate with two-stage normalization, exact + fuzzy matching, conflicting-field handling, and recursive walker. All 9 EXTRACT-04 tests must turn GREEN.

**Strengths**:
- D-01 is correctly enforced: model-supplied `char_start`/`char_end` are completely ignored; all offsets are recomputed via `_normalize_with_map` + search
- Two-stage normalization (Pattern 2) correctly handles NFKC expansion (ligatures → multi-char) AND whitespace collapse (multi-char → single char) by building separate mapping arrays
- The `partial_ratio_alignment` API is used correctly with `dest_start`/`dest_end` for offset recovery (Pattern 3 verified from rapidfuzz type stub)
- Conflicting field branch (Pitfall 5) correctly iterates `field.values` and grounds each `ConflictingValue.evidence` independently — the envelope invariant means `conflicting` fields have no top-level evidence
- Pure function design (D-06) via `model_copy(update=...)` — no in-place mutation
- MIN_SNIPPET_LEN guard (15 chars) addresses Pitfall 3: short fabricated snippets score near-100 via partial_ratio

**Concerns**:
- **HIGH**: The fuzzy threshold is hardcoded to 90.0 (FUZZY_THRESHOLD = 90.0) with only a comment that it's "tuned in tests." The research notes (A1) flag this as LOW confidence: "If too low: fabricated snippets pass grounding. If too high: legitimate fuzzy matches (minor typos, whitespace diffs) get downgraded." The plan doesn't include explicit threshold calibration steps — it assumes 90 works out of the box. If 90 is wrong, all fuzzy matching tests fail.
- **MEDIUM**: The offset remapping from normalized space back to original space requires correct composition of both mapping arrays. The code sketch in RESEARCH.md shows the logic, but there's no inline test in the implementation verifying the remapping is correct for a known NFKC case (e.g., `ﬁ` → "fi"). The plan relies on the existing test suite to catch errors, but a unit test specifically for the `_normalize_with_map` function would be safer.
- **MEDIUM**: There's no handling for the "reverse NFKC" case where source text has NFD decomposed text (e.g., "e" + combining acute) that NFKC composes to "é". RESEARCH.md acknowledges this: "The result is conservative — the offset points to the base char — which is acceptable for grounding." This is acceptable but worth a comment in the code to prevent confusion later.

**Suggestions**:
1. Add a threshold calibration step in the implementation task: run the gate against the three vendor fixtures (generated in 02-04) and log the actual fuzzy scores. If any genuine evidence spans score < 90, lower the threshold. If any fabricated spans score ≥ 90, raise the threshold. Make this explicit in the task verification.
2. Add a dedicated unit test for `_normalize_with_map` that asserts: `source[orig_start:orig_end] == snippet` for a known NFKC case (ligature `ﬁ`) to verify the offset remapping is correct before relying on it in the full tests
3. Add a code comment in the normalization function explaining the NFD→NFC "conservative offset" behavior to document why offsets may point to the base character rather than the combining mark

**Risk Assessment: MEDIUM** — The implementation logic is sound, but the hardcoded 90 threshold is a critical unknown. If it's wrong, tests fail and recalibration is needed. The offset remapping is algorithmically correct but benefits from explicit unit testing.

---

### 02-03-PLAN.md — Schema Flesh-Out + Prompt Authoring

**Summary**: Fleshes out RFQ and VendorResponse pydantic schemas, regenerates the TS contract, and authors the three data-generation prompts (rfq-gen, vendor-gen, messy-data-gen).

**Strengths**:
- Schema correctly avoids Field[T] wrappers (D-11: RFQ is our own artifact, not grounded extraction; D-12: VendorResponse carries raw text + provenance only)
- RFQ uses `list[int]` for budget ranges instead of `tuple[int, int]` per Pitfall 6 (OpenAI structured output JSON schema subset constraint)
- ExtractionResult and ComparisonResult are correctly left unchanged (P3/P4 stubs)
- Codegen drift test is correctly included as verification — domain.py changes must propagate to shared-types
- Prompt frontmatter preserved (registry test validates required keys)
- messy-data-gen correctly marked as model_tier="cheap" since it's a taxonomy reference, not a generation call

**Concerns**:
- **HIGH**: The plan requires "authoring" the three prompt bodies but doesn't specify the evaluation criteria. The rubric weights prompts at 30%. The prompts must demonstrate: (1) explicit anti-hallucination instructions, (2) specific line item names (not "item 1, item 2"), (3) realistic complexity injection (not clean samples). The plan references "anti-hallucination instruction" but there's no checklist or test to verify the prompt actually achieves this. A failed prompt quality check would blow the phase deadline.
- **MEDIUM**: The RFQ schema allows `timeline_weeks: int | None = None` and `budget_range_usd: list[int] | None = None`. If the LLM generates `None` for these fields, the fixture tests expecting 8 line items with populated fields may fail. There's no model-level constraint enforcing "exactly 8 line items with populated fields" — that would require a custom validator.
- **MEDIUM**: D-14 requires documenting "≥1 documented prompt failure example + fix." The plan says "harvested from real authoring" but if no failure occurs during the brief authoring window, it says to "manufacture a realistic one from the RESEARCH.md pitfall list." This feels like gaming the requirement — a manufactured failure isn't the same as a real one learned from iteration.

**Suggestions**:
1. Add a prompt quality checklist to the verification step: rfq-gen must specify 8 named line items, include compliance clauses (COPPA, claim substantiation), include anti-hallucination instruction; vendor-gen must embed messy-data-gen taxonomy, specify format diversity per persona
2. Consider adding a model_validator to RFQ to enforce `len(line_items) >= 8` as a hard constraint, not just a generation target
3. For D-14, prioritize capturing a real failure during the vendor-gen prompt authoring (the mess spec injection is complex and prone to misinterpretation). If no real failure occurs, document the *potential* failure modes from the research (Pitfall 3, 6) with the mitigations already in the prompt, rather than inventing a failure that didn't happen.

**Risk Assessment: MEDIUM-HIGH** — The prompt quality is 30% of the grade, and the plan doesn't include quality gates. The schema looks correct but lacks enforcement for the 8-line-item constraint.

---

### 02-04-PLAN.md — Generation Agents + Live Regen + Documentation

**Summary**: Implements rfq_gen.py + vendor_gen.py agents, runs them to produce committed data fixtures, wires live-regen API endpoints, and documents the Prompt Pack with PROMPT-04 failure example.

**Strengths**:
- Correct separation: rfq_gen uses `.with_structured_output(RFQ)` (Pattern 5), vendor_gen uses plain `.invoke()` (Pattern 6) — one structured, one messy, matching D-08/D-12
- MESS_SPECS are hand-authored in code per D-09 — this makes DATA-03 assertions deterministic and testable
- generate_samples.py correctly uses the rendered Markdown as input to vendor generation (D-12: vendor responses are grounded against the RFQ)
- Live-regen API endpoints are synchronous (correct per RESEARCH.md Open Q3: "generation is fast enough to buffer")
- API endpoints validate persona against MESS_SPECS keys before use (mitigates T-02-11)

**Concerns**:
- **HIGH**: The plan runs live LLM calls to generate fixtures: "cd services/ai && uv run python scripts/generate_samples.py" — this requires OPENAI_API_KEY in .env. If the API key is missing or the model fails, the plan dead-ends. There's no fallback to generate fixtures from cached output or to skip generation and use stub data. The verification step depends entirely on a successful LLM call.
- **HIGH**: The messiness iteration loop: "If any messiness assertion fails... iterate: adjust the mess spec instruction in MESS_SPECS or add a stronger instruction in the vendor-gen prompt, then regenerate and re-test. Do NOT relax the test assertion to make it pass." This is correct discipline, but if the LLM consistently fails to produce the expected messiness patterns (e.g., always includes "$" even when told to omit), the plan could iterate indefinitely. There's no maximum iteration limit or escalation path.
- **MEDIUM**: POST /data/vendor-gen generates a fresh RFQ inline before generating each vendor response. This is inefficient (N+1 LLM calls for N vendors) and creates inconsistency (each vendor sees a slightly different RFQ if generation is non-deterministic). The note says "for the prototype this is acceptable" but it undermines comparability — the whole point is comparing vendors against the *same* RFQ.
- **LOW**: The docs/prompts/data-generation.md failure example section may contain a manufactured failure if no real failure occurred during authoring. The plan acknowledges this but the resulting documentation may not be credible.

**Suggestions**:
1. Add a pre-check before running generate_samples.py: verify OPENAI_API_KEY is set and the model is accessible with a simple `get_llm("reasoning").invoke("hi")` test call. If it fails, abort with a clear error message rather than proceeding to dead-end.
2. Cap the messiness iteration at 3 attempts. After 3 failures, escalate to the planner (or document the failure as a "known limitation" in the write-up rather than forcing the test to pass).
3. For the POST /data/vendor-gen inefficiency: consider adding an optional `rfq_id` parameter that accepts a previously-generated RFQ, or cache the generated RFQ in module-level state for the lifetime of the API process. This ensures all vendors in a comparison see the same RFQ.
4. In docs/prompts/data-generation.md, clearly label the failure example as "real failure from authoring" vs "anticipated failure with mitigation in place" to maintain credibility.

**Risk Assessment: MEDIUM-HIGH** — The heavy dependency on live LLM calls for fixture generation is the main risk. If the model fails to produce expected messiness patterns, the plan enters an undefined iteration loop. The API endpoint inefficiency is acceptable for a prototype but worth documenting.

---

## Cross-Plan Concerns

### Dependency Chain Risk

The phase has a strict dependency chain:
- 02-01 (stubs + tests) → 02-02 (gate impl) → 02-04 (generation)
- 02-03 (schema + prompts) can run in parallel with 02-02 but feeds 02-04
- 02-04 depends on both 02-02 and 02-03 completing

**Concern**: 02-04 cannot run until 02-02 (gate) and 02-03 (schema/prompts) are complete. If 02-02's threshold calibration fails, 02-04 stalls. If 02-03's prompts don't produce the expected messiness, 02-04 iterates. There's no slack in the 5-day timeline for this.

### Core Principle Violation Risk

The project's headline rule: "grounding is enforced in CODE, never on a model-supplied 'verified' flag." This is correctly enforced in:
- D-01: gate ignores model offsets entirely
- D-02: moderate normalization (symbols kept)
- D-06: pure function returns new object

**Potential violation**: The plan doesn't address what happens if the extraction agent (Phase 3) produces a `Field[T]` with `status=present` but `evidence=[]`. The gate's `ground_field` checks `if not field.evidence: return field, []` — it passes through fields with no evidence. This is arguably correct (the envelope validator should catch this at extraction time), but it's worth a comment noting that evidence-absent fields are not the gate's responsibility.

### Security Model

The threat register is adequate:
- T-02-03 (model offsets spoofing): mitigated by D-01
- T-02-04 (verified flag spoofing): mitigated by no such flag in schema
- T-02-05 (fabricated snippet passing fuzzy): mitigated by MIN_SNIPPET_LEN + 90 threshold
- T-02-11 (persona parameter tampering): mitigated by validation against MESS_SPECS keys

No HIGH-severity threats are unmitigated.

---

## Recommendations Summary

1. **Add threshold calibration step** in 02-02 after implementation: run the gate against the three vendor fixtures (or test data) and log fuzzy scores. Adjust 90 up or down based on actual results. Make this explicit in the verification step.

2. **Add unit test for `_normalize_with_map`** in 02-02 specifically testing NFKC ligature offset remapping, before relying on it in the full test suite.

3. **Add prompt quality checklist** to 02-03 verification: explicitly check that rfq-gen has 8 named line items, compliance clauses, anti-hallucination; vendor-gen has mess spec instructions.

4. **Add API key pre-check** before running generate_samples.py in 02-04 to fail fast if LLM is unavailable.

5. **Cap messiness iteration** at 3 attempts in 02-04 to prevent indefinite loops.

6. **Document the failure example honestly** in 02-04: label manufactured failures as anticipated vs real to maintain credibility.

---

## Final Verdict

**Phase 2 is well-designed and follows correct engineering discipline** (RED-before-GREEN, stub-verify-implement, pure functions, code-level grounding enforcement). The research is thorough (offset remapping, rapidfuzz API, NFKC edge cases all verified). The main risks are execution-bound: the fuzzy threshold calibration is untested, the live LLM generation may require iteration, and the prompt quality (30% of grade) lacks explicit verification. These are manageable with the suggestions above. The core principle — "code that disproves the model" — is correctly embedded throughout.

---

## Consensus Summary

Two independent reviewers converged strongly. Both judge the phase **well-designed and aligned
with the headline reliability rule** ("grounding enforced in code, never on a model flag" — D-01),
with overall risk **MEDIUM**. The blockers are procedural / test-design / concrete-bug issues, not
architectural ones.

### Agreed Strengths (raised by both)
- D-01 correctly enforced: the gate ignores model-supplied offsets and recomputes from scratch.
- RED-before-GREEN discipline; falsifiability tests (A: fabricated → downgraded, B: genuine → survives) front-loaded.
- Pure-function design (D-06, `model_copy`); fixture tests assert on committed samples, not live LLM (D-13).
- Correct split: `rfq_gen` uses structured output, `vendor_gen` uses plain `.invoke()` (D-08/D-12); messy-data-gen kept as taxonomy reference.
- Threat register adequate — no unmitigated HIGH-severity threats.

### Agreed Concerns (priority for the --reviews replan)
1. **[HIGH] 02-04 vendor-fixture filename mismatch (Codex).** `generate_samples.py` using `persona.replace("-","_")` would write `vendor_thorough_but_pricey.json` etc., but the committed-file list and fixture tests expect `vendor_thorough.json` / `vendor_cheap.json` / `vendor_fluff.json`. Breaks DATA tests immediately. → Add an explicit `FIXTURE_FILENAMES` persona→filename map.
2. **[HIGH] 02-01 RED-test contradiction (Codex).** Wrapping test bodies in `pytest.raises(NotImplementedError)` makes them PASS against stubs and FAIL after implementation — inverting RED→GREEN. → RED tests must call functions normally and fail naturally; drop the `pytest.raises` wrappers.
3. **[HIGH] 02-02 fuzzy threshold (90.0) is hardcoded and uncalibrated (Ollama; Codex-adjacent).** If wrong, fuzzy tests fail or fabricated spans slip through. → Add an explicit calibration step: run the gate against the 3 vendor fixtures, log scores, adjust the constant; make it a verification criterion.
4. **[HIGH] 02-02 offset-map correctness (Codex on `.strip()`/leading-whitespace; Ollama wants a dedicated `_normalize_with_map` unit test).** → Fix the strip/index handling and add a focused unit test asserting `source[start:end] == snippet` for the NFKC ligature case before relying on it.
5. **[HIGH] 02-02 `DowngradeEntry.original_status` accuracy (Codex).** Must come from the enclosing field's real status, not a hardcoded `"present"`/example value. → Pass `field.status` into the grounding helper.
6. **[MEDIUM/HIGH] Live-LLM fragility in 02-04 (both).** Fixture generation dead-ends if `OPENAI_API_KEY` is missing/model fails, and the messiness-iteration loop has no cap. → Add an API-key/model pre-check that fails fast; cap messiness iteration (~3) with an escalation/known-limitation path (never relax the assertion).
7. **[MEDIUM] `POST /data/vendor-gen` regenerates a fresh RFQ per call (both).** Inefficient (N+1) and breaks comparability — vendors should see the SAME RFQ. → Accept optional `rfq`/`rfq_text` input (or cache the generated RFQ); generate fresh only when omitted.
8. **[MEDIUM] 8-line-items contract inconsistency (both).** must_haves says "≥8 minimum", schema has no validator, tests require exactly 8. → Make the contract consistent (test-only is fine for a prototype; drop "minimum" language, or add a `model_validator`).
9. **[MEDIUM] `mess_spec: list[dict]` is loosely typed (Codex).** Weakens the contract + generated TS. → Introduce a lightweight `MessSpecItem` model (`line_item`, `issue_type`, `instruction`).
10. **[MEDIUM] Conflicting-field "any failure → whole field unsupported" discards genuine values (both).** Defensible/conservative, but → document it explicitly as an intentional reliability tradeoff in code + tests.
11. **[MEDIUM/HIGH] Prompt quality (30% of grade) has no verification gate (Ollama).** → Add a prompt-quality checklist to 02-03 verification (rfq-gen: 8 named line items + compliance clauses + anti-hallucination; vendor-gen: embedded taxonomy + per-persona format diversity).
12. **[MEDIUM] D-14 "manufactured failure" credibility (both).** → Prioritize capturing a REAL failure from authoring; if none occurs, label it honestly as an anticipated failure-mode + mitigation, not a fabricated incident.

### Minor / Low (worth a quick pass)
- Add empty-snippet / empty-source guards in `_match_exact`/`_match_fuzzy` (Codex).
- `ground_model` may miss `dict[str, Field]` / nested-dict values — note before P3 schemas settle (Codex).
- Include the function name in stub `NotImplementedError(...)` messages for faster debugging (Ollama).
- Prefer `model_dump(mode="json")` over `json.loads(model_dump_json())` (Codex).
- Document the NFD→NFC "conservative offset points at base char" behavior in a code comment (Ollama).
- RFQ prompt: reconcile "do not invent client names" vs. "produce a specific client name" — establish allowed fictional context (Codex).

### Divergent Views
No material disagreement. Codex skews toward concrete, immediately-breaking bugs (filename, strip,
original_status, RED wrappers); Ollama skews toward execution risk (threshold calibration, live-LLM
dependency, prompt-quality gating). The two sets are complementary, not conflicting.

### Cross-cutting note
Both flag the **5-day timeline has no slack** for the 02-02 (calibration) → 02-04 (generation)
dependency chain. The replan should de-risk the live-LLM and threshold steps so 02-04 can't stall.
