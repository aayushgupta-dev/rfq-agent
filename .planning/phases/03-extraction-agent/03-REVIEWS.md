---
phase: 3
reviewers: [codex, ollama_minimax_m2_5, claude_opus_independent]
reviewed_at: 2026-06-27T17:12:49Z
plans_reviewed: [03-01-PLAN.md, 03-02-PLAN.md, 03-03-PLAN.md, 03-04-PLAN.md]
note: "gemini/qwen not installed; opencode (no balance) and cursor (not authenticated) unavailable. claude CLI skipped for independence (running inside Claude Code). Substituted an independent fresh-context Opus reviewer agent + minimax-m2.5 via local ollama."
---

# Cross-AI Plan Review — Phase 3 (Extraction Agent)

## Codex Review

## Overall Summary

The phase is well-scoped around the right reliability story: RFQ-aware extraction, strict structured output, server-side grounding before SSE, and trace artifacts that prove raw-vs-grounded behavior. The plans are strong on product intent and rubric alignment, but several test and implementation details would make execution brittle or impossible as written. The biggest risks are test design mismatches, refusal/truncation handling assumptions, strict `xfail` stubs not being removed, and the hard requirement for a “genuine downgrade” from live traces, which may be nondeterministic.

## Plan 03-01 Review

### Strengths
- Good TDD intent: locks Phase 3 verification before implementation.
- Covers the important behaviors: schema shape, grounding, truncation, refusal, missing line items, SSE taxonomy, trace artifacts.
- Trace test includes a machine-checkable downgrade requirement, which supports the “code disproves the model” narrative.

### Concerns
- **HIGH:** `@pytest.mark.xfail(strict=True)` will block later “GREEN” tests unless later plans explicitly remove those marks. If a test passes while still marked strict xfail, pytest reports XPASS as failure.
- **HIGH:** `test_walker_covers_all_fields` design is likely wrong. `DowngradeReport.entries` appears to represent downgrades, not every field visited. Missing fields may not produce entries, so entry count cannot prove walker coverage.
- **MEDIUM:** Tests that import future `agents.extraction` are reasonable, but mocking `_chain` before the module exists can become fragile if the implementation uses `_chain.with_config`, `_llm_with_raw`, or async invocation differently.
- **MEDIUM:** “RED stubs” using xfail do not actually fail the suite. That may satisfy collection, but it weakens the red/green signal.
- **LOW:** The plan says 6 functions in roadmap text but defines 8 tests. Not harmful, but clean up the mismatch.

### Suggestions
- Add a follow-up task in each later plan to remove relevant `xfail` marks when implementing the behavior.
- Redesign walker coverage to monkeypatch or spy on `grounding.gate.ground_field`, collect visited field paths, and compare against an independent schema walk.
- Prefer real assertion bodies from the start, marked xfail only for missing implementation.
- Keep mock expectations at the public function/graph boundary where possible, not tied too tightly to `_chain` internals.

### Risk Assessment
**MEDIUM-HIGH.** The verification intent is good, but as written some tests will either give false confidence or fail later for test-mechanics reasons.

## Plan 03-02 Review

### Strengths
- Correctly fixes `vendor_name` as provenance metadata, not a grounded fact.
- The schema reflects the RFQ-aware hybrid decision well: line-item extraction plus document-level pricing structure.
- Avoids `dict[str, Field]`, directly addressing the known grounding walker limitation.
- Includes shared TypeScript regeneration and drift checking.

### Concerns
- **HIGH:** If `Field[T]` fields have no defaults, constructing “minimal valid ExtractionResult with all fields missing” in tests becomes verbose and easy to break. That is fine, but the plan should provide fixtures/builders.
- **MEDIUM:** `LineItemExtraction.pricing: Field[Decimal]` may be too strict for model output if vendor pricing is often ranges, retainers, “T&M”, “included”, currency-qualified, or bundled. Decimal works for clean numeric prices but not all real proposal pricing.
- **MEDIUM:** `total_price: Field[Decimal]` has the same issue. A stated total might include currency, taxes, conditions, or ranges. A `Field[str]` plus optional numeric normalization would be safer for a 5-day prototype.
- **MEDIUM:** `pricing_structure: Field[str]` is good, but no explicit currency/tax field means important ambiguity may be buried in prose.
- **LOW:** `compliance_points` as a list of only present claims may not surface missing compliance requirements unless the RFQ compliance checklist is also scaffolded. That may be okay for Phase 3, but it limits “absence first-class” outside line items.

### Suggestions
- Consider using `Field[str]` for `pricing` and `total_price` to preserve vendor wording. If numeric comparison is needed later, add derived normalization in Phase 4.
- Add test fixtures/helpers for `missing_field()`, `present_field()`, and minimal `ExtractionResult`.
- Add explicit comments/docstrings clarifying that list fields can be empty only when no claims are found, while missing required RFQ-linked items are represented in `line_items`.

### Risk Assessment
**MEDIUM.** The schema direction is solid, but pricing as `Decimal` may force premature normalization and cause structured-output failures.

## Plan 03-03 Review

### Strengths
- Correct reliability boundary: model output is grounded before any `result` event crosses SSE.
- Explicitly treats truncation and refusal as hard errors.
- Reuses existing LangGraph and FastAPI SSE patterns.
- Exposes `generate_extraction_with_trace`, which is a good trace-capture seam.

### Concerns
- **HIGH:** The implementation mutates a Pydantic model via `raw.vendor_name = vendor.vendor_name`. If models are frozen later or validation constraints matter, prefer `model_copy(update={...})`.
- **HIGH:** Refusal handling assumes `include_raw=True` returns `{"raw", "parsed"}` reliably and that `raw_output["parsed"]` is non-null. The plan does not handle `parsing_error`, `parsed is None`, or validation errors that are not refusals.
- **HIGH:** The prompt asks the model to output `vendor_name`, then overwrites it. Better: still include the schema field, but the prompt should say set it to the provided vendor name exactly, or use a separate model-facing schema without provenance fields.
- **MEDIUM:** `generate_extraction()` uses `asyncio.run`, which fails if called inside an existing event loop. For scripts it is fine; for app internals it is risky. Provide async and sync variants.
- **MEDIUM:** `POST /extract/vendor` accepts a nested `VendorResponse`; the `model_validator` max length is good, but the plan does not mention protecting the direct graph/API path from enormous RFQ content.
- **MEDIUM:** The route appends `done` even after an `error` event. That is probably fine, but tests should assert expected error stream shape.
- **LOW:** Module-level `_chain = _prompt | _llm_with_raw` loads prompt and LLM at import time. This can make tests/imports require env setup unless the factory already handles it cleanly.

### Suggestions
- Handle all structured-output wrapper cases: truncation exception, refusal, `parsing_error`, `parsed is None`, and unexpected exception → safe `error` event.
- Use `raw = raw.model_copy(update={"vendor_name": vendor.vendor_name})`.
- Export `async_generate_extraction()` and let `generate_extraction()` be script-only.
- Add a dedicated error code for schema parse failure, recoverable depending on cause.
- Consider a lean internal model-facing schema if provenance overwrite becomes awkward.

### Risk Assessment
**MEDIUM-HIGH.** The architecture is right, but error handling is under-specified for real LangChain/OpenAI wrapper behavior.

## Plan 03-04 Review

### Strengths
- Strong rubric alignment: full prompt, prompt documentation, reproducible traces.
- Good prompt constraints: humility bias, verbatim evidence, no invented values, bundled pricing not split.
- Trace format is well thought out and useful for demo/submission.
- Human checkpoint is appropriate because prompt quality and trace genuineness are judgment-heavy.

### Concerns
- **HIGH:** Requiring at least one genuine downgrade from live traces is risky and nondeterministic. A good prompt may quote perfectly, producing zero downgrades. That should not force lowering `FUZZY_THRESHOLD`.
- **HIGH:** The instruction “if no downgrade, lower `FUZZY_THRESHOLD`” is dangerous. Lowering the threshold usually makes grounding stricter or looser depending implementation, but changing calibration just to force a trace can damage reliability.
- **HIGH:** Prompt body cannot contain the word `unsupported`, but docs may need to explain gate behavior. The automated check only loads prompt body, which is fine, but writers must avoid frontmatter/body ambiguity.
- **MEDIUM:** “Few-shot examples at least 3, one per flag state” conflicts with four states. It should require at least 4 examples or say one example may cover multiple states.
- **MEDIUM:** `fields_checked = len(report.entries) + count of fields NOT downgraded` is not available from `DowngradeReport` unless extra instrumentation exists. This repeats the Plan 03-01 report-count issue.
- **MEDIUM:** The capture script is listed in the task but not in `files_modified` frontmatter.
- **LOW:** Live OpenAI dependency means this wave is not fully autonomous/reproducible in CI. That is acceptable for traces, but should be explicitly marked as manual/live.

### Suggestions
- Replace “must show genuine downgrade” with one deterministic reliability test plus best-effort live trace downgrade. For example, run one trace against a committed adversarial vendor sample or fixture that naturally causes a fabricated/paraphrased span through the production chain.
- Do not tune `FUZZY_THRESHOLD` just to create a downgrade. Tune only based on a documented calibration set.
- Add `services/ai/scripts/capture_traces.py` to `files_modified`.
- Add a trace metadata field: `model`, `prompt_version`, `created_at`, and maybe `source_fixture`.
- Fix few-shot requirement to cover all four states.
- Either remove `fields_checked` or add a real grounding summary counter from `ground_model`.

### Risk Assessment
**HIGH.** This plan carries the most grading value but also the most nondeterminism. The trace requirement needs a deterministic path that does not incentivize weakening the grounding gate.

## Overall Risk Assessment

**MEDIUM-HIGH.** The phase goals are correct and the architecture is mostly sound, but execution risk is concentrated in test mechanics, structured-output edge cases, pricing schema strictness, and nondeterministic trace downgrade evidence. Fixing those before implementation would make the phase much safer without expanding scope.

---

## MiniMax-M2.5 Review (via local Ollama)

# Phase 3: Extraction Agent Plan Review

## Summary

The Phase 3 plans implement the core extraction agent that transforms messy vendor proposals into grounded, evidence-backed structured output. The plans are well-structured with clear TDD discipline (test-first stubs), proper schema design decisions from context, and a solid integration pattern following the proven `_demo.py` spine. However, there are some concerns around the refusal detection path, trace verification edge cases, and prompt design assumptions that should be addressed before execution.

---

## Plan-by-Plan Analysis

### 03-01-PLAN.md — Wave 1: RED Test Stubs

**Strengths:**
- Defines all 8 test functions mapping directly to validation requirements
- Uses `@pytest.mark.xfail(strict=True)` — correctly fails RED now, goes GREEN on implementation
- Covers critical edge cases: truncation, refusal, missing line items, walker coverage
- Includes the D-15 requirement: test_traces_committed asserts non-empty downgrade_report.entries
- Uses proper isolation pattern (imports inside test functions to avoid collection errors)

**Concerns:**
- **MEDIUM**: The test_refusal_raises_error_event stub assumes a specific mock strategy (`include_raw=True` path) but the implementation pattern in 03-03-PLAN.md may differ. The stub should be flexible enough to accept either the `include_raw=True` detection OR a wrapped result inspection approach.
- **LOW**: test_missing_line_items_surface_as_missing mocks the chain to return a pre-built result — this tests SSE propagation but not the actual extraction logic that determines "missing" status.

**Risk Level:** LOW

---

### 03-02-PLAN.md — Wave 2: Schema Flesh-Out

**Strengths:**
- Correctly fixes D-05: `vendor_name: str` instead of `vendor_name: Field[str]`
- D-01 (RFQ-aware hybrid) properly implemented with `list[LineItemExtraction]`
- D-02 (bundled pricing) split into `pricing_structure` (doc-level) + `total_price` + per-item `unclear`
- D-03 (per-claim grounding) uses `list[Field[str]]` for assumptions, risks, exclusions, compliance_points
- D-04 hard constraint enforced: no `dict[str, Field]` shapes — walker coverage guaranteed
- Codegen drift-check integration is correct

**Concerns:**
- **HIGH**: The plan says "Do NOT add default values to Field[T] fields" but `list[Field[str]]` fields need a default factory. The action says "default to an empty list via pydantic_Field(default_factory=list)" which is correct, but this should be explicit in the task to avoid confusion.
- **MEDIUM**: LineItemExtraction uses `line_item_id` and `line_item_name` as provenance (not grounded), but the prompt design in 03-04-PLAN.md assumes the model should extract these from the RFQ context. This is fine, but the schema should document that these are copied from RFQ.line_items[].id, not extracted from vendor text.

**Risk Level:** LOW

---

### 03-03-PLAN.md — Wave 3: Agent + SSE Route

**Strengths:**
- Follows `_demo.py` pattern exactly for StateGraph + stream_writer
- Two-path detection for truncation (LengthFinishReasonError) vs refusal (additional_kwargs.get("refusal")) — matches RESEARCH.md Pattern 2
- D-07 enforced: ground_model runs BEFORE result SSE event — no ungrounded facts flash to client
- D-10 handled: placeholder offsets (char_start=0, char_end=1) — gate overwrites
- generate_extraction_with_trace correctly exposes raw vs grounded pair from production chain
- Max length guard (200k chars) on vendor.raw_text via model_validator

**Concerns:**
- **HIGH**: The refusal detection path uses `include_raw=True` but the action description says "include_raw=True for the refusal check path only" — this is correct per RESEARCH.md, but the implementation should verify that truncation is caught BEFORE the refusal check runs. Currently the plan has truncation path first (correct), then refusal path after. This ordering is correct.
- **HIGH**: The stub for test_refusal_raises_error_event needs to be updated — the plan uses `include_raw=True` but the mock strategy in the stub may not match. Need to ensure the mock returns `{"raw": mock_msg, "parsed": ...}` structure.
- **MEDIUM**: The extraction route accepts full `VendorResponse` and `RFQ` objects in the request body. This could be a large payload. The max_length check on raw_text is good, but the request size could still be large. Consider adding a request body size limit at the FastAPI level.
- **LOW**: The `generate_extraction_with_trace` function uses `asyncio.run()` for the sync wrapper — this works but blocks the event loop. Since it's only for script/test use (not production), this is acceptable.

**Risk Level:** MEDIUM (refusal detection mock mismatch)

---

### 03-04-PLAN.md — Wave 4: Prompt + Traces

**Strengths:**
- D-09 enforced: "unsupported" word NOT in prompt body — critical for rubric
- D-10 verbatim instruction: ≥20 chars, ≥3 words — prevents MIN_SNIPPET_LEN (15) Pitfall 6
- Few-shot examples for all 4 flag states
- D-11: extraction only flags, no clarification questions — clean boundary
- Trace format matches D-14 spec exactly
- D-15: genuine downgrade requirement (not staged) — critical for rubric proof

**Concerns:**
- **HIGH**: The capture script warning says "Check FUZZY_THRESHOLD (currently 90) — threshold may be over-accepting" but offers no guidance on what threshold is appropriate. If all traces pass grounding (0 downgrades), this is a problem because D-15 explicitly requires ≥1 genuine downgrade. The plan should specify what action to take: lower threshold? inspect model behavior? escalate?
- **HIGH**: The test_traces_committed assertion is strict: at least one trace MUST have non-empty downgrade_report.entries. If no natural downgrade occurs (e.g., the model is perfectly quoting verbatim), the test fails. This is actually correct behavior per D-15, but the capture script needs to handle this gracefully — either strengthen the prompt or adjust the threshold, NOT stage a fake downgrade.
- **MEDIUM**: The prompt verification includes `assert 'verbatim' in body.lower()` but the actual requirement is ≥20 chars / ≥3 words. The prompt might say "verbatim" but still produce short snippets. The test could be more specific.
- **LOW**: The human checkpoint at the end is good, but "approved" is vague. Should specify what makes a trace "genuine" vs problematic.

**Risk Level:** MEDIUM (D-15 fallback not clear)

---

## Cross-Plan Concerns

### Dependency Ordering
- 03-01 → 03-02 → 03-03 → 03-04 is correct
- However, 03-04 depends on 03-03's `generate_extraction_with_trace` being exportable — if that's not exported correctly, the trace capture fails

### Integration Risks
1. **Schema drift**: If 03-02's schema doesn't match what 03-03's code expects, runtime errors occur. The codegen test catches this.
2. **Walker coverage**: D-04 prevents dict shapes, but the test verifies this. If someone adds a dict shape later, the test catches it.
3. **Refusal detection**: The mock in 03-01 may not match the implementation in 03-03. Need alignment.

### Security Considerations
- Vendor raw_text injection is data-only (not system prompt) — correct
- Max length check (200k) on raw_text — good DoS protection
- API key isolation in factory.py — already handled

---

## Suggestions

1. **Add refusal mock alignment check**: Before 03-03 execution, verify the stub's mock strategy (`{"raw": mock_msg, "parsed": ...}`) matches the actual implementation. If not, update the stub.

2. **Clarify D-15 fallback**: In 03-04-PLAN.md Task 2, add explicit guidance: "If no genuine downgrade found after running on all 3 vendors, the acceptable resolutions are: (a) strengthen verbatim instruction in extraction.v1.md to require longer snippets, (b) lower FUZZY_THRESHOLD in gate.py to 85, (c) escalate via /gsd:plan-phase if neither resolves. Do NOT stage a fake downgrade."

3. **Add prompt specificity check**: In 03-04-PLAN.md Task 1 verification, add: `assert any(len(e.get('evidence', [{}])[0].get('snippet', '')) >= 20 for e in [...])` or similar to verify snippet length requirements are in the prompt.

4. **Request body size limit**: Add `@app.post(..., response_model=...` with a FastAPI request size limit, not just pydantic validation.

5. **Document the LineItemExtraction provenance fields**: Add a ponytail comment explaining that `line_item_id` and `line_item_name` are copied from RFQ context, not extracted from vendor text.

---

## Risk Assessment

| Plan | Risk Level | Justification |
|------|------------|---------------|
| 03-01 | LOW | Test stub design is solid |
| 03-02 | LOW | Schema design matches context decisions |
| 03-03 | MEDIUM | Refusal detection mock alignment needed |
| 03-04 | MEDIUM | D-15 fallback path unclear |
| **Overall** | **MEDIUM** | Core functionality sound, but mock alignment and D-15 fallback need clarity |

The plans are well-constructed and follow the established patterns in the codebase. The main risks are around the refusal detection mock mismatch between the stub (03-01) and implementation (03-03), and the D-15 verification that requires at least one genuine downgrade. With the suggested clarifications addressed, execution risk is LOW.

---

## Claude Opus Review (independent fresh-context agent)

Both referenced artifacts exist. I have everything I need. Here is my review.

---

# Phase 3 (Extraction Agent) — Independent Adversarial Review

## 1. Summary

This is a strong, well-grounded plan. The phase is correctly framed as an *integration* phase — every reliability primitive (the `Field[T]` envelope with code-enforced validators, the `ground_model` walker, the SSE spine, the LLM factory) already exists and is tested, and the plans wire them together rather than reinventing them. The wave/dependency ordering is clean (RED stubs → schema → agent+route → prompt+traces), the D-04 no-dict constraint genuinely closes the walker gap by design, the model-facing→canonical mapping is sensibly collapsed via placeholder offsets, and the trace deliverable (D-14 raw-vs-grounded diff, D-15 genuine downgrade) is exactly the right rubric proof. The headline risks are not in the architecture but in two places: (a) **one Wave-1 test stub (`test_walker_covers_all_fields`) is specified in a way that cannot pass against the actual `ground_field` code**, and (b) **the truncation/refusal detection rests on MEDIUM-confidence behavior from two open LangChain bugs with no concrete fallback wired in if the assumption is wrong**. Both are fixable within the plan; neither undermines the design. With those addressed, the four plans do make all five success criteria TRUE.

## 2. Strengths

- **The grounding boundary is correctly placed and the design honors it.** D-07 (ground server-side *before* the SSE boundary; only the grounded `result` event crosses) is consistent across CONTEXT, RESEARCH, and Plan 03. The node emits `status` progress events, then `result` only after `ground_model` returns. No `partial`/ungrounded fact events. This is the single most important reliability property and it holds.
- **D-04 (no `dict[str, Field]`) genuinely closes the IN-04 walker gap.** I verified `_walk_and_ground` in `gate.py`: it traverses `Field`, nested `BaseModel`, `list[Field]`, and `list[BaseModel]`, and the ponytail comment confirms dict-valued containers are *not* traversed. The Plan-02 schema (`list[LineItemExtraction]`, `list[Field[str]]` for the per-claim categories, single `Field[T]` for narratives) uses only walker-covered shapes. The constraint is real, not cosmetic.
- **The model-facing → canonical mapping is correctly collapsed.** D-10's "model supplies snippet + source_id only; gate computes offsets" is implemented as placeholder offsets (`char_start=0, char_end=1`) that the gate overwrites — and I confirmed `Evidence`'s validator only requires `char_end > char_start ≥ 0`, so `(0,1)` passes. This eliminates a mapping step (good ponytail call) while keeping real offsets for UI highlighting. The plan correctly forbids any pre/post mapping layer.
- **Division of labor on the 4-state posture is airtight.** D-09 keeps `unsupported` strictly gate-only; the prompt-integrity assert (`'unsupported' not in body`, *no OR branch*) mechanically enforces it. The model emits 4 states; the gate owns the 5th. This is exactly the "never trust an LLM-asserted verified flag" rule (§2/§8) made executable.
- **Trace authenticity is enforced structurally, not by trust.** `generate_extraction_with_trace` is the *single authorized* capture surface (uses the production `_chain`, no local rebuilds), it returns the raw-ungrounded *and* grounded pair, and the D-15 check (`≥1 non-empty downgrade_report.entries`) is machine-verifiable with an explicit "do not stage a fake downgrade" instruction. The fallback diagnosis (lower `FUZZY_THRESHOLD` / strengthen verbatim instruction) doubles as the carried-forward Phase-2 calibration closure. This is the best part of the plan.
- **Provenance injection is handled correctly.** `raw.vendor_name = vendor.vendor_name` post-model (D-05) means the known name never gets grounded against `raw_text` (which could spuriously fail). The stub fix (`Field[str]` → plain `str`) is explicitly tracked.

## 3. Concerns

- **[HIGH] `test_walker_covers_all_fields` as specified cannot pass.** Plan 01 stub #2 sets every `Field[T]` to `status="missing"`, then asserts `len(DowngradeReport.entries) == (number of Field attributes)`. But I verified `ground_field` returns *early* on `missing`/`unsupported`: `if field.status in (FlagStatus.missing, FlagStatus.unsupported): return field, []`. A model full of `missing` fields produces **zero** downgrade entries — the assert will fail, and Plan 02's `<verify>` runs this exact test expecting GREEN. The walker *visits* every field, but visiting a `missing` field produces no entry, so entry-count is not a proxy for coverage. **This test will block Wave 1.** The coverage check needs a different mechanism (e.g. give each field locatable-but-fabricated evidence as `present` so each genuinely downgrades, or — cleaner — enumerate `model_fields` recursively and assert the walker's traversal set matches, independent of grounding outcome).

- **[MEDIUM] Truncation/refusal detection rests on MEDIUM-confidence open-bug behavior with no wired fallback.** RESEARCH.md itself rates this MEDIUM and cites two *open* issues (#29700, #25510). The plan commits to one specific shape: `_chain` built with `include_raw=True`, wrapped in `try/except LengthFinishReasonError`, then `raw_output["raw"].additional_kwargs.get("refusal")`. RESEARCH's own Pitfall 1 warns `LengthFinishReasonError` "propagates uncaught through the `include_raw=True` wrapper" — the plan *relies* on exactly that (the except catches it because the OpenAI client raises before the wrapper). If the installed `langchain-openai >=1.3.3` has *changed* this (backported a fix that routes truncation into `parsing_error` instead of raising), the `except` never fires and a truncated object could reach `["parsed"]`. The mocked tests pin the *intended* behavior but, being mocked, will pass regardless of what the real library does. There is no test against the live library and no documented fallback path (`include_raw` parsing_error inspection) if the assumption breaks. For a 20%-weighted reliability requirement (EXTRACT-05), this is thin.

- **[MEDIUM] No test that a genuinely truncated *real* response is never parsed — only mocked behavior is verified.** EXTRACT-05's success criterion is "truncation is never parsed as valid output." Both truncation tests mock the exception. Nothing in the plan forces a real truncation (e.g. a deliberately tiny `max_tokens` run against a large fixture) to confirm the end-to-end path actually catches it. Given the schema size question is explicitly *open* (RESEARCH Open Question #2: "whether gpt-5.4's output token limit will be hit in practice"), and the D-06 sectioned fallback is deferred until truncation is *observed*, the plan never creates the conditions to observe it. The trace-capture run (Plan 04 Task 2) is the only real run, and if all 3 fixtures fit comfortably, truncation handling ships entirely unexercised against the live stack.

- **[MEDIUM] `test_sse_event_taxonomy` (Plan 01 #7) drives a route that makes a live model call, with no mock specified.** The stub posts to `/extract/vendor` via `TestClient`. The extraction node's first action is `_chain.invoke(...)` — a real gpt-5.4 call. Unless the chain is patched, this test (a) costs an API call per CI run, (b) is non-deterministic, and (c) fails with no key in CI. Plan 01's stub text doesn't specify a mock for this one (it specifies mocks for truncation/refusal/missing but the taxonomy test just "posts to /extract/vendor"). Either it needs a patched `_chain` returning a canned `ExtractionResult`, or it should assert taxonomy via the same mocked-graph path as the other behavioral tests.

- **[MEDIUM] `total_price: Field[Decimal]` will almost always be `missing` and risks looking like a dead field — and OpenAI structured-output + `Decimal` is a known friction point.** D-02 keeps both `pricing_structure: Field[str]` (the verbatim bundle) and `total_price: Field[Decimal]` (separable grand total). With deliberately messy bundled vendors, `total_price` is `missing` for most/all of them by design — fine semantically, but the JSON-schema serialization of `Decimal` under `with_structured_output(method="json_schema")` can emit `format: decimal` or a string type that the model fills inconsistently, occasionally producing parse-time coercion surprises. Worth a targeted check during Plan 02/03 that a `Decimal`-typed `Field` round-trips through the structured-output call cleanly; if it fights the schema path, `Field[str]` for the raw number (gate still grounds it) is the lazier correct move.

- **[LOW] `MIN_SNIPPET_LEN = 15` vs. the prompt's "≥20 chars" instruction is a latent mismatch that could mask a calibration problem.** The gate rejects snippets <15 chars; the prompt asks for ≥20. If the model obeys, fine. But the gate's threshold and the prompt's instruction being different numbers means a model quoting 15–19 char snippets passes the gate while violating the prompt — and a *too-short, spuriously-high partial_ratio* match (the exact thing `MIN_SNIPPET_LEN` guards) could slip through grounding looking legitimate. Aligning the two (or making the prompt's floor ≥ the gate's) removes the gap.

- **[LOW] D-15's "if 0 downgrades, lower FUZZY_THRESHOLD" remedy could over-correct into false downgrades.** The fallback for "no natural downgrade occurred" is to lower the threshold until one appears. But a downgrade manufactured by lowering the threshold isn't the same as a genuine fabrication being caught — it could start rejecting *legitimate* fuzzy matches (the over-rejection failure mode Phase-2 SC#2 explicitly guards against). The more honest path if no downgrade occurs naturally is to inject one fabrication-prone case, not to detune the gate. The plan should prefer the verbatim-instruction-strengthening branch and treat threshold-lowering as a last resort with a regression check that genuine spans still survive.

- **[LOW] `generate_extraction` uses `asyncio.run` inside a sync wrapper — fine for scripts/tests, but a footgun if ever called from an async context.** The ponytail comment acknowledges it's for script/test use. Just confirm Plan 04's `capture_traces.py` doesn't end up inside an event loop (it won't as a plain script), and that no test calls `generate_extraction` from an already-running loop — `asyncio.run` raises `RuntimeError: cannot be called from a running event loop`.

## 4. Suggestions

1. **Rewrite `test_walker_covers_all_fields` to not depend on downgrade-entry count.** Either (a) populate every `Field` as `present` with a *fabricated* (non-locatable) snippet so each genuinely downgrades and entry-count == field-count holds, or (b) better: assert coverage directly by recursively enumerating `Field`-typed attributes in `ExtractionResult.model_fields` and confirming the set the walker would touch matches — decoupled from grounding outcome. This is the only HIGH and it blocks the wave; fix it in the Plan 01 stub spec before execution.
2. **Add one live-library guard test for truncation detection** (not just mocked): a `@pytest.mark.live`/opt-in test that calls the chain with a tiny `max_tokens` against the largest fixture and asserts a `LengthFinishReasonError` path (error event, no parse). Run it once during Plan 03/04 to validate the MEDIUM-confidence assumption against the *installed* `langchain-openai`, then it can be skipped in CI. Document the `include_raw` parsing-error fallback in the code as a `# ponytail:`-marked contingency so it's not a from-scratch investigation if the assumption breaks.
3. **Specify the mock for `test_sse_event_taxonomy`** in the Plan 01 stub — patch `agents.extraction._chain` to return a minimal valid `ExtractionResult` so the route exercises status→result→done deterministically without an API call.
4. **Add a Plan 02/03 sanity check that `Field[Decimal]` round-trips through `with_structured_output(method="json_schema")`** — a one-line `python -c` that invokes a trivial structured call, or just assert the generated JSON schema for `total_price` is sane. If it fights, downgrade to `Field[str]` (the gate doesn't care about the value type).
5. **Reconcile `MIN_SNIPPET_LEN` (15) with the prompt's ≥20-char instruction** — set the prompt floor at or above the gate floor and add a sentence to `extraction-prompt-doc.md` explaining the relationship (it's good Prompt-Pack material for the 30%).
6. **Reframe the D-15 zero-downgrade fallback** to prefer strengthening the verbatim instruction / adding a fabrication-prone case over lowering `FUZZY_THRESHOLD`, and gate any threshold change behind a regression assert that the genuine-span test (`test_evidence_required` analog) still passes — so calibration never silently introduces over-rejection.
7. **Confirm the `data/` fixture filenames before Plan 04** — Plan 04 references `data/rfq.json` / `data/vendor_*.json` as assumptions; a quick `ls data/` in the plan's read_first would prevent a Wave-4 stall if the committed names differ.

## 5. Risk Assessment

**Overall: MEDIUM (low-leaning).**

The architecture is sound, the reliability boundary is correctly placed and verified against real code, and the plans are honest about their YAGNI deferrals (single-call first, sectioned fallback only if observed). The four plans, *as designed*, do make all five success criteria TRUE. The MEDIUM rating is driven by two concrete, fixable issues: one Wave-1 test stub that cannot pass as specified (HIGH but localized — it will surface immediately and block, not ship silently), and the EXTRACT-05 truncation/refusal path resting on MEDIUM-confidence open-bug behavior that is only ever exercised via mocks, never against the live library in the planned runs. Neither is an architectural flaw; both are verification-coverage gaps. The downside if they slip through is bounded — a blocked wave (caught fast) and a reliability path that *might* be untested against the real stack (caught at demo time at worst, since the trace run is real). Address suggestions 1–3 and this drops cleanly to LOW.
---

## Consensus Summary

Three independent reviewers (Codex, MiniMax-M2.5, Claude Opus) agree the **architecture is sound** and the four plans, as designed, make all five success criteria TRUE. The reliability boundary (ground-before-SSE, D-07), the D-04 no-dict walker closure, the model-facing→canonical offset collapse (D-10), and the trace deliverable (D-14/D-15) all hold up — Opus verified the walker shapes and the `Evidence (0,1)` placeholder against live code. The risk is concentrated in **verification-coverage gaps and one un-passable test stub**, not in the design.

### Agreed Strengths (2+ reviewers)
- Correct grounding boundary: model output grounded server-side before any `result` event crosses SSE.
- D-04 (no `dict[str, Field]`) genuinely closes the IN-04 walker gap by design.
- `vendor_name` correctly fixed to plain `str` provenance (D-05), not grounded.
- `generate_extraction_with_trace` is a clean, single authorized trace-capture surface (no local rebuilds) — strong rubric proof.
- Strong TDD/wave discipline and rubric alignment (humility prompt, verbatim evidence, no clarifications).

### Agreed Concerns → BLOCKERS (must address in replan)
- **B-R1 [HIGH — code-verified, blocks Wave 1] (Codex + Opus + MiniMax):** `test_walker_covers_all_fields` cannot pass as specified. It builds an all-`missing` model and asserts `len(DowngradeReport.entries) == field_count`, but `ground_field` early-returns on `missing`/`unsupported` (`return field, []`), yielding **zero** entries. Entry-count is not a coverage proxy. Plan 02's `<verify>` runs this test expecting GREEN. **Fix:** redesign the test to prove coverage independent of grounding outcome — recursively enumerate `Field`-typed attributes in `ExtractionResult.model_fields` and assert the walker's traversal set matches (or populate every field as `present` with fabricated/non-locatable evidence so each genuinely downgrades).
- **B-R2 [HIGH] (Codex + MiniMax + Opus):** Truncation/refusal detection is only ever exercised via mocks and rests on MEDIUM-confidence open-bug behavior (#29700/#25510). It does not handle `parsed is None`, `parsing_error`, or non-refusal `ValidationError` → safe error event. **Fix:** harden the agent to map all structured-output failure shapes to a safe `error` event; add one opt-in/live guard test (tiny `max_tokens` vs a large fixture) that validates truncation against the *installed* `langchain-openai` during the Plan 03/04 real run; document the `include_raw` parsing_error fallback as a `# ponytail:` contingency.
- **B-R3 [HIGH] (Codex + MiniMax + Opus):** The D-15 zero-downgrade fallback instruction ("if no downgrade, lower `FUZZY_THRESHOLD`") is dangerous — a manufactured downgrade ≠ a genuine fabrication caught, and detuning the gate reintroduces the over-rejection failure mode Phase-2 SC#2 explicitly guards against (contradicts CLAUDE.md §2/§8). **Fix:** reframe the fallback to prefer strengthening the verbatim instruction or injecting a fabrication-prone case; gate any threshold change behind a regression assert that genuine spans still survive.
- **B-R4 [MEDIUM→blocker-worthy] (Opus):** `test_sse_event_taxonomy` posts to `/extract/vendor`, whose node calls `_chain.invoke()` — a live gpt-5.4 call with no mock specified (non-deterministic, costs an API call, fails in CI without a key). **Fix:** patch `agents.extraction._chain` to return a canned `ExtractionResult` so the route exercises status→result→done deterministically.

### Agreed Concerns → WARNINGS (fold into the same replan pass)
- **W-R1 (Codex + Opus):** `Field[Decimal]` for `pricing`/`total_price` risks structured-output friction and premature normalization on messy pricing (ranges, "T&M", "included"). Add a round-trip sanity check; fall back to `Field[str]` if it fights `method="json_schema"` (the gate doesn't care about value type).
- **W-R2 (Codex + MiniMax):** Add a request-body size limit at the FastAPI level (not just the pydantic `raw_text` max_length).
- **W-R3 (Opus):** Reconcile gate `MIN_SNIPPET_LEN=15` with the prompt's "≥20 chars" instruction (set prompt floor ≥ gate floor); document the relationship in the Prompt Pack doc.
- **W-R4 (Codex):** Use `raw.model_copy(update={"vendor_name": ...})` instead of attribute mutation; keep the model-facing vendor_name handling consistent (don't ask the model to output it then overwrite).
- **W-R5 (Codex + MiniMax):** Add test fixtures/builders (`missing_field()`, `present_field()`, minimal `ExtractionResult`) so all-missing construction isn't brittle.
- **W-R6 (Opus):** Confirm committed `data/` fixture filenames in Plan 04 `read_first` to avoid a Wave-4 stall.
- **W-R7 (Codex + Opus):** Keep `generate_extraction`'s `asyncio.run` script/test-only (footgun in an async context); note an async variant.

### Divergent Views
- **vendor_name handling:** Codex flags the post-model attribute mutation + "model outputs vendor_name then overwrite" as a HIGH robustness/consistency issue; Opus judges the post-model provenance set correct and safe. Resolution: keep the post-model provenance approach (Opus) but switch to `model_copy(update=...)` and keep the model-facing schema/prompt consistent (Codex) — captured as W-R4.
- **xfail mechanics:** Codex rates `xfail(strict=True)` → XPASS-failure risk HIGH; MiniMax rates the same pattern a strength ("fails RED now, GREEN on implementation"). Resolution: ensure each later plan removes the relevant `xfail` mark when it turns the test GREEN — captured under B-R1's test-stub redesign.

**Verdict:** 4 blockers (1 code-verified Wave-1 blocker) + 7 warnings → **replan via `/gsd:plan-phase 3 --reviews`.**
