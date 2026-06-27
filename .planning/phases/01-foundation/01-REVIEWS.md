---
phase: 1
reviewers: [codex]
reviewers_attempted: [codex, opencode, cursor]
reviewers_failed:
  - opencode: "Insufficient balance (opencode.ai billing)"
  - cursor: "Authentication required (run 'cursor agent login' or set CURSOR_API_KEY)"
reviewed_at: 2026-06-27T10:36:20Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md, 01-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 1: Foundation

> One of three requested reviewers completed. `claude` was skipped (self — running inside
> Claude Code). `opencode` and `cursor` failed before producing output (billing / auth — see
> frontmatter). `gemini`, `qwen`, `coderabbit` are not installed. With a single responding
> reviewer there is no true cross-AI consensus; the "Consensus Summary" below is a prioritized
> synthesis of the one review received, not agreement across models. Re-run after fixing
> opencode/cursor access for genuine adversarial coverage.

## Codex Review

## 01-01 — Monorepo Scaffold

**Summary**
Strong foundation plan. It correctly makes the repo layout real before downstream work, keeps Python out of the JS workspace, and proves the `apps/web` → `packages/shared-types` link early. Main risks are dependency/tooling churn around Next/ESLint and missing generated lockfiles in the file inventory.

**Strengths**
- Correctly enforces the architectural boundary: `services/ai` owned by `uv`, root owned by `pnpm`/`turbo`.
- Creates `packages/shared-types` early so Plan 02 has a real target.
- Explicitly avoids putting `services/*` in `pnpm-workspace.yaml`, which prevents turbo from owning Python.
- Good handling of generated TS by marking the initial `index.d.ts` as temporary and Prettier-exempt.

**Concerns**
- **MEDIUM:** `uv.lock` and `pnpm-lock.yaml` are not listed in `files_modified`, but this plan will create/update both and they should be committed for reproducibility.
- **MEDIUM:** Next 15 + latest ESLint may prefer flat config over `.eslintrc.json`; this could make the ESLint verification fail depending on resolved versions.
- **LOW:** Manual Next shell setup can miss expected defaults like `next-env.d.ts`, `app/globals.css`, or package scripts unless explicitly created.
- **LOW:** `test -d node_modules/json-schema-to-typescript` is a brittle verification. Prefer checking `node_modules/.bin/json2ts`.

**Suggestions**
- Add `uv.lock`, `pnpm-lock.yaml`, `next-env.d.ts`, and any generated package-manager metadata to `files_modified`.
- Pin exact JS versions after install, especially `next`, `eslint`, `eslint-config-next`, `turbo`, and `prettier`.
- Use either a known-compatible ESLint flat config or pin ESLint to a version compatible with `.eslintrc`.
- Add root/package scripts for `lint`, `format:check`, and `build` so turbo has stable task targets.

**Risk Assessment: MEDIUM**
The architecture is sound, but toolchain bootstrap plans often fail on version/config mismatches. The risk is execution friction, not conceptual design.

---

## 01-02 — Contract Primitives & Codegen

**Summary**
This is the most important plan for the phase and is mostly well designed. It directly addresses absence modeling, evidence, codegen, and drift detection. The main gap is that the `Field[T]` envelope allows invalid combinations unless validators are added, so the contract may model absence but not enforce its intended semantics.

**Strengths**
- Good use of pydantic as the single source of truth.
- Generic `Field[T]` approach is well justified by research and keeps source schemas clean.
- Drift-check is the right enforcement mechanism for PLAT-02.
- Explicitly tests `extra="forbid"` and closed SSE event taxonomy.
- Domain stubs intentionally avoid premature full schema design.

**Concerns**
- **HIGH:** `Field[T]` appears structurally typed but not semantically enforced. For example, `status="conflicting"` with empty `values`, or `status="missing"` with a value, may still validate unless explicit validators are added.
- **MEDIUM:** Path resolution for codegen/drift tests is easy to get wrong. The research example using `parents[2]` would resolve to `services/`, not the repo root.
- **MEDIUM:** The plan claims "every contract field" models absence, but Phase 1 only creates stubs. This should be scoped to every fact-like field introduced in Phase 1.
- **LOW:** Naming a class `Field` can be confused with `pydantic.Field`; imports should avoid collisions.
- **LOW:** Mutable defaults like `evidence: list[Evidence] = []` work better in pydantic than plain dataclasses, but `default_factory=list` is clearer and safer.

**Suggestions**
- Add `model_validator` rules:
  - `conflicting` requires non-empty `values`.
  - `missing` and `unsupported` suppress `value`.
  - `present` should require either `value` or a deliberate exception.
- Use `default_factory=list` for list fields.
- Centralize repo-root resolution in `scripts/codegen.py` and import that helper in the drift test.
- Adjust success wording from "every contract field" to "every Phase 1 domain fact field."
- Avoid project-specific placeholder comments like `# ponytail:` in committed contract files unless that convention already exists.

**Risk Assessment: MEDIUM**
The codegen strategy is strong, but without semantic validators the contract can allow states that violate the product's core "absence made first-class" principle.

---

## 01-03 — LLM Access & SSE Spine

**Summary**
This plan correctly treats model access and streaming as proof points rather than assumptions. The live checkpoint is appropriate because PLAT-03 cannot be faked. The biggest implementation risks are `.env` loading, brittle startup behavior, and ambiguity around model-specific ping errors.

**Strengths**
- Good separation between tier names and model IDs.
- Correctly avoids requiring live OpenAI access for unit tests.
- Explicit live proof for both model access and `curl -N` SSE.
- Keeps CORS/proxy-buffering out of scope for Phase 1.
- Security concern around not logging API keys is clearly handled.

**Concerns**
- **HIGH:** The plan mentions loading root `.env` via dotenv, but `python-dotenv` is not installed in Plan 01. Either add the dependency or avoid dotenv.
- **MEDIUM:** FastAPI startup always calling `verify_access()` can make local dev brittle during transient OpenAI outages or when running offline tests.
- **MEDIUM:** Distinguishing "no model access" from "bad request parameter" may be hard through LangChain exception wrapping. The plan requires this but does not define a robust mechanism.
- **MEDIUM:** Since Plan 03 can run in parallel with Plan 02, raw duplicated SSE taxonomy may drift from `EventEnvelope`.
- **LOW:** Live server verification should explicitly stop the uvicorn process after capturing `curl -N`.
- **LOW:** Startup checks add small latency/cost on every server start and reload.

**Suggestions**
- Add `python-dotenv` to Plan 01 dependencies, or implement explicit env-only behavior and document it.
- Add a test-only bypass such as `BID_DESK_SKIP_MODEL_ACCESS_CHECK=true`, defaulting to strict checks outside tests.
- Validate emitted SSE events against a local taxonomy constant; once Plan 02 lands, import the schema enum or shared literal source.
- Add timeout handling around access pings.
- For ping failures, report "model verification failed" with raw categorized cause instead of overclaiming "no access" when classification is uncertain.

**Risk Assessment: MEDIUM-HIGH**
The plan achieves the phase goal if credentials and model IDs are real, but external API access, model parameter ambiguity, and startup strictness make this the riskiest execution plan.

---

## 01-04 — Prompt Pack Registry

**Summary**
Clean, appropriately scoped plan. It creates the Prompt Pack as first-class source without overbuilding prompt rendering or templating. The main improvements are around testability of latest-version resolution and validating prompt IDs.

**Strengths**
- Strong alignment with PROMPT-01 and the grading rubric.
- Keeps prompts as versioned `.md` files with frontmatter, which is easy to inspect and later expose in the UI.
- Latest-version-by-filename is simple and appropriate.
- Tests cover all seven required prompt IDs.
- Avoids premature caching, templating, or runtime complexity.

**Concerns**
- **MEDIUM:** The latest-version test needs either an injectable prompt directory or a pure resolver helper; otherwise tests may write temporary prompt files into the real prompt directory.
- **LOW:** `load(prompt_id)` should validate prompt IDs with a strict regex to avoid accidental glob/path weirdness if ever called with user-controlled input.
- **LOW:** `failure_handling` stubs may become shallow unless tests assert meaningful non-empty content beyond a placeholder.
- **LOW:** `model_tier: cheap` for clarification is reasonable, but later comparison/clarification behavior may require reasoning depending on complexity.

**Suggestions**
- Implement `load(prompt_id, base_dir: Path = _DIR)` or split out `_find_latest(prompt_id, base_dir)`.
- Validate `prompt_id` against `^[a-z0-9-]+$`.
- Test that frontmatter `id` matches the filename stem before `.vN.md`.
- Make each stub's TODO name the owning phase and the future requirement ID, e.g. `TODO P3 / EXTRACT-01`.

**Risk Assessment: LOW**
This is scoped well and has few moving parts. The only meaningful risk is minor test fragility around latest-version resolution.

---

## Overall Assessment

The phase plan is coherent and mostly complete. It maps well to the Phase 1 success criteria: scaffold, contract/codegen, model access, SSE, and Prompt Pack skeleton. The strongest parts are the contract/codegen strategy and the deliberate proof-oriented verification.

The main fixes I would make before execution are: add lockfiles to file inventories, add or avoid `python-dotenv`, add semantic validators to `Field[T]`, harden codegen path resolution, and make the Next/ESLint setup version-compatible. With those addressed, overall Phase 1 risk drops from **MEDIUM** to **LOW-MEDIUM**.

---

## OpenCode Review

_Not collected — `opencode run` failed: **Insufficient balance** (opencode.ai billing). Top up the workspace or switch the configured model to a provider with credit, then re-run `/gsd-review --phase 1 --opencode`._

---

## Cursor Review

_Not collected — `cursor agent` failed: **Authentication required**. Run `cursor agent login` (or set `CURSOR_API_KEY`), then re-run `/gsd-review --phase 1 --cursor`._

---

## Consensus Summary

> Single-reviewer caveat: only Codex responded, so the items below are a **priority ranking of one
> review**, not multi-model agreement. Treat HIGH items as the must-fix list before `/gsd:execute-phase 1`.

### Highest-Priority Fixes (HIGH severity)

1. **`Field[T]` has no semantic enforcement (01-02).** The envelope is structurally typed but a row like `status="missing"` + a populated `value`, or `status="conflicting"` + empty `values`, still validates. This directly undercuts the product's "absence is first-class / no silent fill" principle (PLAT-01, CLAUDE.md §1/§8). Add `model_validator` rules so the absence enum is enforced in code, not just declared.
2. **`python-dotenv` used but not installed (01-03).** Plan 03 loads root `.env` via dotenv, but Plan 01 never adds the dependency. Either add it to the `uv` deps in 01-01 or drop dotenv for explicit env-only reads. Concrete cross-plan dependency gap that will fail execution.

### Agreed Strengths

- Proof-oriented foundation: real layout, live model-access ping, and `curl -N` SSE proof before any agent is built — reliability machinery is verified, not assumed.
- Clean architectural boundary (`uv`-owned `services/ai` vs. `pnpm`/`turbo` root) that keeps turbo from owning Python.
- pydantic-as-source-of-truth with a codegen drift-check is the right enforcement for PLAT-02.
- Prompt Pack (01-04) scoped as first-class versioned source without over-building templating.

### Agreed Concerns (MEDIUM, worth addressing)

- **Reproducibility:** `uv.lock` / `pnpm-lock.yaml` (and `next-env.d.ts`) missing from 01-01 `files_modified`.
- **Codegen path resolution:** research example's `parents[2]` resolves to `services/`, not repo root — centralize root resolution in `scripts/codegen.py` and import it in the drift test.
- **Startup brittleness (01-03):** unconditional `verify_access()` on FastAPI startup breaks offline/transient-outage dev; add a test/offline bypass defaulting to strict.
- **SSE taxonomy drift:** 01-03 runs parallel to 01-02 with a duplicated event taxonomy — validate against a shared constant, import `EventEnvelope` once 01-02 lands.
- **Toolchain version risk (01-01):** Next 15 + latest ESLint may require flat config over `.eslintrc.json`; pin versions or use a known-compatible flat config.
- **Scope wording (01-02):** "every contract field models absence" overclaims for a stubs-only phase — reword to "every Phase 1 domain fact field."
- **Test isolation (01-04):** latest-version resolver needs an injectable `base_dir` so tests don't write into the real prompt directory.

### Divergent Views

None — single reviewer. Note one reviewer suggestion conflicts with a project convention: Codex flags the `# ponytail:` comment in committed contract files as a "project-specific placeholder to avoid." Per CLAUDE.md §2, `# ponytail:` marking deliberate kept-complexity **is** the established convention here — keep it. Disregard that one suggestion.

---

## How to Incorporate

```
/gsd:plan-phase 1 --reviews
```

For genuine cross-AI coverage, fix opencode billing / cursor auth and re-run `/gsd-review --phase 1 --all`.
