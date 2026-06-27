---
phase: 02-grounding-gate-messy-data
plan: "03"
subsystem: schemas-and-prompt-pack
tags:
  - domain-schema
  - shared-types
  - prompt-pack
  - rfq-gen
  - vendor-gen
  - messy-data-gen
  - data-generation

dependency_graph:
  requires:
    - "02-01 (envelope schema, codegen infrastructure, prompt registry)"
  provides:
    - "MessSpecItem, LineItem, fleshed RFQ, fleshed VendorResponse in domain.py"
    - "Regenerated packages/shared-types/index.d.ts with four new interfaces"
    - "rfq-gen.v1.md: full RFQ generation prompt"
    - "vendor-gen.v1.md: full vendor response generation prompt with mess spec taxonomy"
    - "messy-data-gen.v1.md: definitive 8-type issue taxonomy reference"
  affects:
    - "02-04 (rfq_gen.py + vendor_gen.py agents import MessSpecItem, LineItem, RFQ, VendorResponse)"
    - "Phase 3 (ExtractionResult reads from VendorResponse.raw_text)"
    - "Phase 5 (RFQ Overview screen consumes RFQ schema; shared-types TS contract consumed by web)"

tech_stack:
  added: []
  patterns:
    - "MessSpecItem typed pydantic model replaces list[dict] (D-08/D-09, typed TS contract)"
    - "list[int] for budget_range_usd replaces tuple[int, int] (Pitfall 6: OpenAI structured output constraint)"
    - "codegen.py json2ts fallback: local node_modules path → global PATH (worktree compatibility)"
    - "Prompt bodies: system prompt with embedded taxonomy, persona + mess_spec as input parameters"

key_files:
  created: []
  modified:
    - services/ai/schemas/domain.py
    - packages/shared-types/index.d.ts
    - services/ai/prompts/rfq-gen.v1.md
    - services/ai/prompts/vendor-gen.v1.md
    - services/ai/prompts/messy-data-gen.v1.md
    - services/ai/scripts/codegen.py

decisions:
  - "No model_validator for len(line_items) — 8-item enforcement is test_rfq_fixture_valid() contract only (verbosity vs correctness tradeoff for prototype)"
  - "codegen.py falls back to global json2ts when local node_modules/.bin/json2ts absent (worktree isolation: no shared node_modules)"
  - "D-14: no authoring failure observed during prompt authoring session — prompts were authored offline, not executed against live model; plan 02-04 should label documented failure example as anticipated failure-mode, not a real observed one"

metrics:
  duration_minutes: 6
  completed_date: "2026-06-27T15:04:34Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 02 Plan 03: Domain Schema Fleshing + Prompt Pack Authoring Summary

RFQ/VendorResponse schemas replaced with real fields (MessSpecItem+LineItem+plain types per D-11/D-12); TS contract regenerated; rfq-gen/vendor-gen/messy-data-gen prompts authored with full bodies replacing TODO stubs.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Flesh out RFQ + VendorResponse schemas (with MessSpecItem) + regen TS contract | 4f10680 | domain.py, index.d.ts, codegen.py |
| 2 | Author rfq-gen, vendor-gen, and messy-data-gen prompts (PROMPT-04 foundation) | 109b725 | rfq-gen.v1.md, vendor-gen.v1.md, messy-data-gen.v1.md |

## What Was Built

### Task 1 — Schema Fleshing + TS Contract

**MessSpecItem** (new): Typed pydantic model replacing the previous `list[dict]` approach.
Fields: `line_item: str`, `issue_type: str`, `instruction: str`. Keeps the TS contract
typed (pydantic2ts generates `MessSpecItem` interface with typed fields vs an untyped array).

**LineItem** (new): RFQ line item model. Fields: `id`, `name`, `description`, `deliverables`,
`timeline_weeks`, `budget_range_usd`. The `budget_range_usd: list[int] | None` uses a
2-element convention instead of `tuple[int, int]` — OpenAI structured output does not
support Python tuples in JSON schema (Pitfall 6 from RESEARCH.md).

**RFQ** (fleshed from stub): Plain Python types per D-11 — no `Field[T]` wrappers.
Fields: `title`, `client_name`, `issue_date`, `response_deadline`, `scope_summary`,
`line_items: list[LineItem]`, `commercial_expectations`, `questionnaire: list[str]`,
`compliance_requirements: list[str]`, `budget_total_usd: int | None`. No `model_validator`
for the 8-item count — enforced by `test_rfq_fixture_valid()` (test-only contract).

**VendorResponse** (fleshed from stub): Raw text + provenance per D-12 — no pre-extracted
fields. Fields: `vendor_name`, `persona`, `mess_spec: list[MessSpecItem]`, `source_id`,
`format_label`, `raw_text`. The extraction agent reads `raw_text` and produces
`ExtractionResult`; VendorResponse itself has no structured fact fields.

**ExtractionResult + ComparisonResult**: Unchanged P3/P4 stubs preserved exactly.

**packages/shared-types/index.d.ts**: Regenerated. New interfaces: `MessSpecItem`,
`LineItem`, updated `RFQ` (plain string/number fields), updated `VendorResponse`
(plain string fields + `MessSpecItem[]`). Old stub interfaces for `FieldStr3/4`,
`FieldDecimal1/2`, `FieldInt1` removed as those stubs are no longer in domain.py.

### Task 2 — Prompt Pack Authoring

**rfq-gen.v1.md**: Full RFQ generation system prompt. Persona: senior procurement manager
at Luminos Consumer Brands for GlowBite launch. All 8 line items specified by name with
deliverables. COPPA and claims-substantiation compliance clauses. 8-question vendor
questionnaire. Anti-hallucination instruction (fictional brand established in prompt,
then instructed not to add further inventions). JSON-only output format instruction
targeting the RFQ schema field names.

**vendor-gen.v1.md**: Vendor response generation system prompt. Input parameters: `{rfq_text}`,
`{persona}`, `{mess_spec}`. Three persona definitions (thorough-but-pricey, cheap-but-incomplete,
polished-fluff) with format diversity: formal multi-section proposal / email/letter style /
deck-outline style. Full 8-type issue taxonomy embedded inline (same as messy-data-gen but
in table form for space efficiency). Explicit "do not clean up the mess spec" instruction.
Anti-hallucination guardrail with fictional agency name suggestions per persona.

**messy-data-gen.v1.md**: Definitive issue-type taxonomy reference. All 8 types defined
with: name, description, example in vendor text, why it causes buyer problems, and
how it stresses the extraction agent. Summary table maps each type to its expected
extraction `FlagStatus` and whether a clarification question is needed. `model_tier: cheap`
(reference document, not a generation call).

## D-14 Prompt Failure Note

**No authoring failure was observed during this session.** The prompt bodies were authored
offline (written by the executor, not executed against a live model). Plan 02-04 should
therefore label any documented prompt failure example as an **anticipated failure-mode**
(derived from the taxonomy and persona design) rather than a real observed one. If plan
02-04 executes the prompts and encounters actual failures, those are the real D-14 captures.

## Prompt Quality Checklist (Self-Verified)

**rfq-gen.v1.md:**
- [x] All 8 line items listed by name (strategy & creative through launch program management)
- [x] At least one compliance clause (COPPA: 3 mentions; claims substantiation: 3 mentions)
- [x] Explicit anti-hallucination instruction ("Anti-Hallucination Instruction" section)
- [x] Output format instruction ("Respond ONLY with the JSON object")

**vendor-gen.v1.md:**
- [x] mess_spec issue-type taxonomy embedded inline (all 8 types in table)
- [x] Per-persona format diversity specified (tabular / email / deck-bullets)
- [x] Instruction to NOT clean up mess spec issues ("Do NOT Clean Up the Mess Spec" section)
- [x] Anti-hallucination guardrail ("Anti-Hallucination Guardrail" section)

**messy-data-gen.v1.md:**
- [x] All 8 issue types defined with name + description + example
- [x] model_tier set to "cheap" in frontmatter

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] codegen.py failed with missing json2ts in worktree**

- **Found during:** Task 1, running `uv run python scripts/codegen.py`
- **Issue:** codegen.py constructs `json2ts_cmd = str(root / "node_modules" / ".bin" / "json2ts")`.
  In a git worktree, `root` resolves to the worktree root which has no `node_modules` (they
  live only in the main checkout). `pydantic2ts` checks `shutil.which(json2ts_cmd)` on this
  non-existent absolute path, raises `Exception: json2ts must be installed`.
- **Fix:** Added a fallback: `json2ts_cmd = str(json2ts_bin) if json2ts_bin.exists() else "json2ts"`.
  When the local path doesn't exist, falls back to the global PATH entry (`/opt/homebrew/bin/json2ts`
  was available globally). The fix is minimal and doesn't change behavior in the main checkout
  (where `json2ts_bin.exists()` returns True and the local binary is used as before).
- **Files modified:** `services/ai/scripts/codegen.py`
- **Commit:** 4f10680

## Known Stubs

The following stubs are intentional P3/P4 contract placeholders (not blocking this plan's goals):

| Location | Stub | Reason |
|----------|------|--------|
| `services/ai/schemas/domain.py:ExtractionResult` | `vendor_name`, `scope_summary`, `total_price` with `Field[T](status="missing")` | P3 placeholder — real fields land in Phase 3 extraction agent; kept so codegen monomorphizes FieldStr/FieldDecimal (D-08) |
| `services/ai/schemas/domain.py:ComparisonResult` | `vendor_count`, `comparable` with `Field[T](status="missing")` | P4 placeholder — real fields land in Phase 4 comparison agent (D-08) |

These stubs are deliberate and marked with `# ponytail:` comments. They do not prevent this
plan's goal (schema fleshing + prompt authoring) from being achieved.

## Threat Flags

No new threat surface introduced. This plan only modifies:
- Pydantic schema definitions (no network endpoints, no auth paths)
- Prompt files committed to source control (no secrets; T-02-08: accept)
- codegen script (runs in-repo, no external input)

T-02-09 (schema tampering) mitigated: `test_codegen_drift.py` GREEN confirms the TS
contract matches the updated pydantic schemas.

## Self-Check: PASSED

Files exist:
- [FOUND] services/ai/schemas/domain.py
- [FOUND] packages/shared-types/index.d.ts
- [FOUND] services/ai/prompts/rfq-gen.v1.md
- [FOUND] services/ai/prompts/vendor-gen.v1.md
- [FOUND] services/ai/prompts/messy-data-gen.v1.md
- [FOUND] services/ai/scripts/codegen.py

Commits exist:
- [FOUND] 4f10680 — feat(02-03): flesh out RFQ+VendorResponse schemas + regen TS contract
- [FOUND] 109b725 — feat(02-03): author rfq-gen, vendor-gen, and messy-data-gen prompts

Tests: 90 passed, 1 warning (no failures).
