---
phase: 02-grounding-gate-messy-data
plan: "04"
subsystem: data-generation-and-api
tags:
  - rfq-gen
  - vendor-gen
  - sample-fixtures
  - data-generation
  - live-regen-api
  - prompt-pack
  - DATA-01
  - DATA-02
  - DATA-03
  - DATA-04
  - PROMPT-04

dependency_graph:
  requires:
    - "02-01 (test_sample_fixtures.py RED tests; data/ fixture expectations)"
    - "02-02 (grounding gate — downstream consumer of vendor fixtures)"
    - "02-03 (RFQ/VendorResponse/MessSpecItem schemas; rfq-gen/vendor-gen prompts)"
  provides:
    - "services/ai/agents/rfq_gen.py: generate_rfq() + render_rfq_md()"
    - "services/ai/agents/vendor_gen.py: FIXTURE_FILENAMES + MESS_SPECS + generate_vendor_response()"
    - "services/ai/scripts/generate_samples.py: developer CLI for fixture regeneration"
    - "data/rfq.json + rfq.md: committed RFQ fixture (8 line items, GlowBite)"
    - "data/vendor_thorough.json, vendor_cheap.json, vendor_fluff.json: committed messy vendor fixtures"
    - "GET /data/rfq + POST /data/vendor-gen: live-regen API endpoints"
    - "docs/prompts/data-generation.md: PROMPT-04 documentation"
  affects:
    - "Phase 3 (extraction agent reads data/vendor_*.json raw_text)"
    - "Phase 5 (UI Vendor Upload screen uses committed fixtures as sample data)"

tech_stack:
  added: []
  patterns:
    - "Single-call structured output: ChatPromptTemplate + with_structured_output(RFQ) for rfq_gen"
    - "Plain LLM call for vendor_gen: ChatPromptTemplate + llm.invoke() → result.content as raw_text"
    - "FIXTURE_FILENAMES as authoritative filename map (not persona.replace derivation)"
    - "Hand-authored MESS_SPECS with MessSpecItem instances (typed, not list[dict])"
    - "API pre-check pattern: _check_api_access() fails fast without logging the key"
    - "model_dump(mode='json') throughout API endpoints — correct pydantic v2 JSON-serializable pattern"
    - "POST /data/vendor-gen accepts optional rfq_text for cross-vendor RFQ consistency"

key_files:
  created:
    - services/ai/agents/rfq_gen.py
    - services/ai/agents/vendor_gen.py
    - services/ai/scripts/generate_samples.py
    - data/rfq.json
    - data/rfq.md
    - data/vendor_thorough.json
    - data/vendor_cheap.json
    - data/vendor_fluff.json
    - docs/prompts/data-generation.md
  modified:
    - services/ai/api/app.py
    - .planning/phases/02-grounding-gate-messy-data/02-VALIDATION.md

decisions:
  - "langchain_core.prompts.ChatPromptTemplate used (not langchain.prompts) — langchain re-exports removed in current version"
  - "D-14: no real prompt failure observed — failure example labeled 'Anticipated failure-mode' per 02-03-SUMMARY.md note"
  - "Worktree env fix: symlinked main repo .env to worktree root (factory.py uses parents[3] from __file__)"
  - "MESS_SPECS uses MessSpecItem instances throughout — never list[dict] — matching typed TS contract"
  - "API pre-check calls get_llm('reasoning').invoke('ping') — reuses factory.py verify pattern without duplicating it"

metrics:
  duration_minutes: 35
  completed_date: "2026-06-27T15:30:00Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 11
---

# Phase 02 Plan 04: Data Generation Agents, Committed Fixtures, and Live-Regen API Summary

Generation agents (rfq_gen.py + vendor_gen.py) authoring messy fixtures via rfq-gen/vendor-gen prompts + structured output; committed 5 data/ fixture files; live-regen endpoints wired to FastAPI; PROMPT-04 documentation with anticipated failure example + versioning notes.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | rfq_gen.py + vendor_gen.py agents + generate_samples.py CLI + run to commit fixtures | bbbc922 | rfq_gen.py, vendor_gen.py, generate_samples.py, data/rfq.json, data/rfq.md, data/vendor_thorough.json, data/vendor_cheap.json, data/vendor_fluff.json |
| 2 | Live-regen API endpoints (DATA-04) + PROMPT-04 documentation | 8b825bb | api/app.py, docs/prompts/data-generation.md |
| 3 | Phase gate — full test suite GREEN + VALIDATION.md updated | df62e5e | 02-VALIDATION.md |

## What Was Built

### Task 1 — Generation Agents + Committed Fixtures

**rfq_gen.py:** Two functions:
- `generate_rfq() -> RFQ`: Loads `rfq-gen` prompt via registry, builds a `ChatPromptTemplate`
  with system prompt + "Generate the RFQ now." human message, chains with
  `get_llm("reasoning").with_structured_output(RFQ, method="json_schema")`. Returns a validated
  `RFQ` instance with 8 line items.
- `render_rfq_md(rfq: RFQ) -> str`: Pure string formatter. Produces a Markdown document with
  heading, client/date block, 8 line item sections (deliverables + budget range), commercial
  expectations, questionnaire (numbered), and compliance requirements. No LLM call. Used as
  `rfq_text` input to vendor_gen so all vendors respond to the same RFQ.

**vendor_gen.py:** Key exports:
- `FIXTURE_FILENAMES: dict[str, str]` — authoritative persona→filename map with short names
  (vendor_thorough.json not vendor_thorough_but_pricey.json). Matches the local constant in
  test_sample_fixtures.py exactly.
- `MESS_SPECS: dict[str, list[MessSpecItem]]` — hand-authored mess specs with typed
  `MessSpecItem` instances (never list[dict]). Three personas with 4-5 specs each targeting
  distinct issue types: bundled_scope, missing_line_item, vague_timeline, unclear_tax_and_currency,
  internal_conflict, weak_compliance_claim, marketing_fluff.
- `FORMAT_LABELS: dict[str, str]` — tabular_proposal / letter_email / deck_bullets.
- `generate_vendor_response(rfq_text, persona, mess_spec) -> VendorResponse`: One-pass LangChain
  call (D-08). Converts `mess_spec` to dicts via `model_dump()` for template interpolation.
  Returns a validated `VendorResponse` with `source_id` from `FIXTURE_FILENAMES`.

**generate_samples.py:** CLI tool with `_check_api_access()` pre-check (fails fast, never logs
the key — T-02-12). `main()` calls `generate_rfq()`, writes `rfq.json` + `rfq.md`, then iterates
`FIXTURE_FILENAMES` to generate and write the 3 vendor fixtures using `FIXTURE_FILENAMES` keys
(not `persona.replace("-", "_")`).

**Committed fixtures:**
- `data/rfq.json` — valid `RFQ` with 8 line items (GlowBite marketing-services pitch for
  Luminos Consumer Brands). All 5 DATA-01/02/03 fixture tests GREEN on first run.
- `data/rfq.md` — same RFQ as readable Markdown (vendor context).
- `data/vendor_thorough.json` — 24,789 chars, bundled pricing, over-scope, marketing fluff.
- `data/vendor_cheap.json` — 11,984 chars, 3 missing line items (TVC Production, Kids
  Compliance, Paid Media Buying TBD), vague timelines.
- `data/vendor_fluff.json` — 18,052 chars, internal timeline conflicts (6 weeks vs 18 weeks
  for Launch; 8 weeks vs 14 weeks for TVC), weak compliance claims, strategic framework fluff.

### Task 2 — Live-Regen API + PROMPT-04 Documentation

**api/app.py additions (DATA-04):**
- `GET /data/rfq`: Calls `generate_rfq()` → returns `rfq.model_dump(mode="json")`. Live regen.
- `POST /data/vendor-gen`: Accepts `VendorGenRequest(persona: str, rfq_text: str | None)`.
  Validates persona against `MESS_SPECS` keys before use (T-02-11: HTTP 400 for unknown
  persona). If `rfq_text` is omitted, generates a fresh RFQ inline. Returns
  `vendor.model_dump(mode="json")`. The optional `rfq_text` parameter is the DATA-04 design
  choice: callers can pass the same RFQ Markdown to all three vendor calls, ensuring a valid
  apples-to-apples comparison.

**docs/prompts/data-generation.md (PROMPT-04):** Full documentation for all three
data-generation prompts. Each section covers: what it does (1-sentence), why structured this
way (design rationale), how it handles unreliable/missing information, and model tier choice.
Failure example labeled "Anticipated failure-mode (no real failure occurred during authoring)"
per the D-14 decision in 02-03-SUMMARY.md — the anticipated failure is vendor-gen
over-polishing despite "omit fee" instruction, with the mitigation (imperative mess spec
language + "Critical Instruction" section) and what would trigger a v2 prompt documented.

### Task 3 — Phase Gate

All 108 tests pass (0 failures). Suite breakdown:
- `test_grounding_gate.py`: 9 EXTRACT-04 tests + normalize/source-id/non-mutation tests GREEN
- `test_sample_fixtures.py`: 5 DATA-01/02/03 tests GREEN
- `test_codegen_drift.py`: GREEN (DATA-04 schema contract)
- `test_prompt_registry.py`: 35 tests GREEN (PROMPT-04 load path)
- `test_field_envelope.py`, `test_llm_factory.py`, `test_sse_demo.py`: Phase 1 regressions GREEN

`02-VALIDATION.md` updated: `nyquist_compliant: true`, `wave_0_complete: true`, all requirement
rows set to ✅ green, Approval: complete.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] langchain.prompts import does not exist**
- **Found during:** Task 1, first run of generate_samples.py
- **Issue:** The plan specified `from langchain.prompts import ChatPromptTemplate`. The installed
  langchain version does not re-export from `langchain.prompts`; the correct import path is
  `from langchain_core.prompts import ChatPromptTemplate`.
- **Fix:** Updated import in both rfq_gen.py and vendor_gen.py to use `langchain_core.prompts`.
- **Files modified:** services/ai/agents/rfq_gen.py, services/ai/agents/vendor_gen.py
- **Commit:** bbbc922 (inline with Task 1)

**2. [Rule 3 - Blocker] .env not found in worktree root**
- **Found during:** Task 1, generate_samples.py pre-check
- **Issue:** `llm/factory.py` resolves the `.env` path as `Path(__file__).resolve().parents[3] / ".env"`.
  In the worktree (`agent-a3a063a9c2cd402ea`), this resolves to the worktree root
  `/Users/aayush/projects/aerchain/.claude/worktrees/agent-a3a063a9c2cd402ea/.env`, which
  does not exist. The `.env` file lives in the main repo root.
- **Fix:** Created a symlink from the worktree root to the main repo `.env`. The symlink is
  gitignored (`.env` is already in `.gitignore`). No source file changes needed — factory.py
  already uses `load_dotenv` which follows symlinks.
- **Impact:** Zero (worktree-only, symlink not committed)
- **Commit:** N/A (worktree setup, not committed)

## Known Stubs

None introduced in this plan. The existing P3/P4 stubs in `ExtractionResult` and
`ComparisonResult` (marked `# ponytail:` in domain.py) are pre-existing and unchanged.

## Threat Surface Scan

No new threat surface beyond what the plan's threat model covers:
- POST /data/vendor-gen: persona validated against MESS_SPECS before use (T-02-11 mitigated)
- OPENAI_API_KEY: never logged in any error message path in generate_samples.py (T-02-12 mitigated)
- T-02-13 (model-generated vendor text with fabricated claims): accept — vendor text is test data
  for the grounding gate, not a trust boundary in itself
- T-02-14 (slow synchronous LLM calls): accept — prototype scope per RESEARCH.md Open Q3

## Self-Check: PASSED

Files exist:
- [FOUND] services/ai/agents/rfq_gen.py
- [FOUND] services/ai/agents/vendor_gen.py
- [FOUND] services/ai/scripts/generate_samples.py
- [FOUND] data/rfq.json
- [FOUND] data/rfq.md
- [FOUND] data/vendor_thorough.json
- [FOUND] data/vendor_cheap.json
- [FOUND] data/vendor_fluff.json
- [FOUND] docs/prompts/data-generation.md
- [FOUND] .planning/phases/02-grounding-gate-messy-data/02-VALIDATION.md

Commits exist:
- [FOUND] bbbc922 — feat(02-04): add rfq_gen/vendor_gen agents, generate_samples CLI, and committed fixtures
- [FOUND] 8b825bb — feat(02-04): add live-regen API endpoints and PROMPT-04 documentation
- [FOUND] df62e5e — chore(02-04): phase gate — all 108 tests GREEN + VALIDATION.md complete

Tests: 108 passed, 0 failures, 1 warning (deprecation only).
