---
phase: 01-foundation
plan: "01"
subsystem: monorepo-scaffold
tags: [scaffold, pnpm, turbo, next.js, python, uv, ruff, eslint, prettier]
dependency_graph:
  requires: []
  provides:
    - pnpm+turbo JS workspace root
    - services/ai Python uv env with all runtime+dev deps
    - packages/shared-types @aerchain/shared-types pnpm link
    - apps/web Next.js 15 App Router shell
    - json2ts binary (Plan 02 codegen)
    - python-dotenv (Plan 03 env loading)
  affects:
    - All Phase 1 plans (this is Wave 1 — nothing else can run before this)
tech_stack:
  added:
    - turbo@2.10.0 (root devDependency)
    - prettier@3.9.0 (root devDependency)
    - json-schema-to-typescript@15.0.4 (root devDependency — json2ts binary for Plan 02)
    - next@15.5.19 (apps/web)
    - react@19.0.0, react-dom@19.0.0 (apps/web)
    - eslint@9.39.4 + eslint-config-next@15.5.19 + @eslint/eslintrc (apps/web devDependency)
    - typescript@5.8.3 (apps/web devDependency)
    - pydantic@2.13.4 (services/ai runtime)
    - langgraph@1.2.6 (services/ai runtime)
    - langchain@1.3.11 + langchain-openai@1.3.3 (services/ai runtime)
    - fastapi@0.138.1 + uvicorn@0.49.0 (services/ai runtime)
    - sse-starlette@3.4.5 (services/ai runtime)
    - python-frontmatter@1.3.0 (services/ai runtime)
    - python-dotenv@1.2.2 (services/ai runtime)
    - pydantic-to-typescript@2.0.0 (services/ai devDependency)
    - ruff@0.15.20 (services/ai devDependency)
    - pytest@9.1.1 (services/ai devDependency)
  patterns:
    - pnpm workspace:* link (apps/web -> @aerchain/shared-types)
    - uv managed Python venv in services/ai
    - turbo.json minimal pipeline (lint/build tasks; depth deferred to P5)
    - ESLint 9 flat config via FlatCompat (legacy eslint-config-next bridge)
key_files:
  created:
    - package.json (workspace root — turbo, prettier, json-schema-to-typescript)
    - pnpm-workspace.yaml (apps/*, packages/* only — not services/*)
    - turbo.json (minimal lint/build pipeline)
    - .prettierrc.json (100-char width, standard defaults)
    - .prettierignore (exempts packages/shared-types/index.d.ts)
    - services/ai/pyproject.toml (name=aerchain-ai, all runtime+dev deps)
    - services/ai/.python-version (3.12)
    - services/ai/__init__.py (package marker)
    - services/ai/uv.lock (committed for reproducibility)
    - packages/shared-types/package.json (@aerchain/shared-types contract package)
    - packages/shared-types/index.d.ts (placeholder — GENERATED header, exports FlagStatus)
    - apps/web/package.json (@aerchain/web with workspace:* dep)
    - apps/web/next.config.mjs (transpilePackages: [@aerchain/shared-types])
    - apps/web/tsconfig.json (App Router defaults, bundler module resolution)
    - apps/web/eslint.config.mjs (flat config via FlatCompat — ESLint 9)
    - apps/web/app/layout.tsx (minimal RootLayout)
    - apps/web/app/page.tsx (imports FlagStatus — workspace link proof)
    - apps/web/next-env.d.ts (generated on first next build, committed)
    - pnpm-lock.yaml (committed for reproducibility)
  modified:
    - .gitignore (deleted root main.py/pyproject.toml; un-ignore apps/web/next-env.d.ts)
  deleted:
    - main.py (root placeholder — D-02)
    - pyproject.toml (root — relocated to services/ai/ as D-02)
decisions:
  - "ESLint 9 flat config uses FlatCompat bridge because eslint-config-next@15 still exports legacy CommonJS format — FlatCompat is the official migration path"
  - "@eslint/eslintrc added as apps/web devDependency (FlatCompat runtime requirement — not bundled transitively)"
  - "next-env.d.ts committed; .gitignore updated with negation rule !apps/web/next-env.d.ts"
  - "services/ai/pyproject.toml uses [dependency-groups] for dev deps (uv native) instead of [project.optional-dependencies]"
metrics:
  duration_min: 6
  tasks_completed: 2
  tasks_total: 2
  files_created: 19
  files_modified: 1
  files_deleted: 2
  completed_date: "2026-06-27"
---

# Phase 01 Plan 01: Monorepo Scaffold Summary

**One-liner:** pnpm+turbo JS workspace root with Next.js 15 shell proving `@aerchain/shared-types` link; Python project relocated to `services/ai` with uv env, ruff, pytest, and all runtime+dev deps.

## What Was Built

### Task 1: Python project relocation + JS workspace root

The root Python project (`name=aerchain`, empty deps) was relocated into `services/ai/` as `name=aerchain-ai` with the full runtime dependency stack (pydantic, langgraph, langchain-openai, fastapi, uvicorn, sse-starlette, python-frontmatter, python-dotenv) and dev tools (pydantic-to-typescript==2.0.0, ruff, pytest). Root `main.py` and `pyproject.toml` were deleted per D-02.

The repo root was initialized as a pnpm+turbo JS workspace: `pnpm-workspace.yaml` lists `apps/*` and `packages/*` only (not `services/*` — turbo never touches the Python service). Root devDependencies: `turbo@2.10.0`, `prettier@3.9.0`, `json-schema-to-typescript@15.0.4` (the `json2ts` binary Plan 02 codegen depends on). Both lockfiles (`uv.lock`, `pnpm-lock.yaml`) are committed.

### Task 2: shared-types contract package + Next.js App Router shell

`packages/shared-types` is the `@aerchain/shared-types` contract package. `index.d.ts` is a minimal hand-stubbed placeholder (exports `FlagStatus` as the 5-state union, marked with a `GENERATED` header) — Plan 02 codegen overwrites it and the drift test owns it thereafter.

`apps/web` is a Next.js 15 App Router shell that imports `FlagStatus` from `@aerchain/shared-types` via `workspace:*` — proving the pnpm link resolves end-to-end and the cross-package import type-checks. ESLint uses the flat config format (`eslint.config.mjs` via FlatCompat bridge); no `.eslintrc.json`. TypeScript, ESLint, and Prettier all pass clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `@eslint/eslintrc` as apps/web devDependency**
- **Found during:** Task 2 ESLint verification
- **Issue:** `eslint.config.mjs` uses `FlatCompat` from `@eslint/eslintrc` but the package was not a direct dependency — ESLint errored with `ERR_MODULE_NOT_FOUND: Cannot find package '@eslint/eslintrc'`. The package exists in the pnpm store (pulled transitively) but ESLint's ESM loader requires it as a direct dependency.
- **Fix:** `pnpm --filter @aerchain/web add -D @eslint/eslintrc` — added as a direct devDependency.
- **Files modified:** `apps/web/package.json`, `pnpm-lock.yaml`
- **Commit:** 353ade7

**2. [Rule 3 - Blocking] Updated .gitignore to un-ignore `apps/web/next-env.d.ts`**
- **Found during:** Task 2 — next-env.d.ts commit staging
- **Issue:** The pre-existing `.gitignore` had a bare `next-env.d.ts` rule that blocked tracking the file anywhere in the repo. The plan explicitly lists it in `files_modified` and the acceptance criteria require it committed.
- **Fix:** Changed the ignore rule to a negation `!apps/web/next-env.d.ts` — the generated file is committed (it's a plan deliverable) while still being regenerable by Next.js.
- **Files modified:** `.gitignore`
- **Commit:** 353ade7

**3. [Rule 1 - Bug] Removed dangling `[project.optional-dependencies]` block from services/ai/pyproject.toml**
- **Found during:** Task 1 — `uv add --dev` appended a `[dependency-groups]` section, making `[project.optional-dependencies]` redundant and potentially confusing.
- **Fix:** Removed the `[project.optional-dependencies]` block; uv's canonical dev-dep section (`[dependency-groups]`) is the source of truth.
- **Files modified:** `services/ai/pyproject.toml`
- **Commit:** 14c16d4

## Known Stubs

- `packages/shared-types/index.d.ts` — intentional placeholder stub marked with `// GENERATED` header. Contains only `FlagStatus` (5-state union). Plan 02 codegen overwrites this with the full pydantic-derived contract. This stub is the exact design intent; it is NOT a data-flow gap for this plan's goal (proving the workspace link).

## Threat Flags

No new threat surface introduced beyond what the Plan 01-01 threat model covers (dependency supply-chain surface mitigated by pinned lockfiles).

## Self-Check: PASSED

- `services/ai/pyproject.toml` exists with `name = "aerchain-ai"` — FOUND
- Root `main.py` deleted — CONFIRMED
- Root `pyproject.toml` deleted — CONFIRMED
- `pnpm-workspace.yaml` has `apps/*` + `packages/*`, no `services/*` — CONFIRMED
- `node_modules/.bin/json2ts` executable — CONFIRMED
- `node_modules/.bin/turbo` executable — CONFIRMED
- `.prettierignore` lists `packages/shared-types/index.d.ts` — CONFIRMED
- `python-dotenv` in `services/ai/pyproject.toml` runtime deps — CONFIRMED
- `pnpm-lock.yaml` committed (14c16d4 + 353ade7) — CONFIRMED
- `services/ai/uv.lock` committed (14c16d4) — CONFIRMED
- `apps/web/eslint.config.mjs` exists; `.eslintrc.json` absent — CONFIRMED
- `packages/shared-types/index.d.ts` has GENERATED header + exports FlagStatus — CONFIRMED
- `apps/web/app/page.tsx` imports from `@aerchain/shared-types` — CONFIRMED
- `pnpm exec tsc --noEmit` in apps/web — PASSES
- `pnpm exec eslint .` in apps/web — PASSES
- `pnpm exec prettier --check 'apps/web/**/*.{ts,tsx}'` — PASSES
- `uv run ruff check .` in services/ai — PASSES
- `apps/web/next-env.d.ts` committed — CONFIRMED

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | 14c16d4 | `chore(01-01): relocate Python project to services/ai; init pnpm+turbo workspace` |
| Task 2 | 353ade7 | `feat(01-01): add shared-types package and Next.js App Router shell (D-01, D-03)` |
