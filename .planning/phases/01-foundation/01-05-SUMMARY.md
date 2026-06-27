---
phase: 01-foundation
plan: "05"
subsystem: web-frontend
tags: [framework-upgrade, nextjs-16, react-19, tailwind-v4, shadcn-ui, ui-substrate]
requires:
  - 01-01-monorepo-scaffold (pnpm workspace + @aerchain/shared-types link)
provides:
  - "apps/web on Next.js 16.2.9 + React 19.2.7 (exact pins)"
  - "Tailwind v4 CSS-first wiring (PostCSS, no config file)"
  - "shadcn/ui substrate: components.json (new-york/neutral), cn() helper, oklch token system"
  - "one proof shadcn Button rendered on the existing page"
affects:
  - apps/web (all future buyer screens build on this substrate — Phase 5)
tech-stack:
  added:
    - next@16.2.9
    - react@19.2.7
    - react-dom@19.2.7
    - eslint-config-next@16.2.9
    - tailwindcss@4.3.1
    - "@tailwindcss/postcss@4.3.1"
    - postcss@^8.5.15
    - class-variance-authority@^0.7.1
    - clsx@^2.1.1
    - tailwind-merge@^3.6.0
    - tw-animate-css@^1.4.0
    - lucide-react@^1.21.0
    - "@radix-ui/react-slot@1.3.0"
  removed:
    - "@eslint/eslintrc (FlatCompat no longer needed under native flat config)"
  patterns:
    - "Native ESLint flat config (spread eslint-config-next/core-web-vitals + /typescript)"
    - "Tailwind v4 CSS-first theming via @theme inline + oklch CSS vars (no tailwind.config.js)"
key-files:
  created:
    - apps/web/postcss.config.mjs
    - apps/web/app/globals.css
    - apps/web/components.json
    - apps/web/lib/utils.ts
    - apps/web/components/ui/button.tsx
  modified:
    - apps/web/package.json
    - apps/web/eslint.config.mjs
    - apps/web/tsconfig.json
    - apps/web/next-env.d.ts
    - apps/web/app/layout.tsx
    - apps/web/app/page.tsx
    - pnpm-lock.yaml
decisions:
  - "eslint-config-next@16 ships native flat config — replaced the FlatCompat bridge with direct spread imports (the FlatCompat path threw a circular-structure error)."
  - "shadcn CLI evolved past the new-york/neutral interactive flow; its `base-nova` preset pulls Base UI + a broken `shadcn/tailwind.css` runtime import + an injected Geist font. Reconciled to the plan's locked classic radix-based new-york substrate by hand to stay in scope."
metrics:
  duration: "~8 min"
  completed: 2026-06-27
  tasks_completed: 2
  tasks_total: 3
  files_changed: 14
---

# Phase 01 Plan 05: Next 16 + UI Substrate Summary

Upgraded `apps/web` to Next.js 16.2.9 / React 19.2.7 (exact pins) and wired the agreed UI
toolchain — Tailwind v4 (CSS-first) + a classic radix-based shadcn/ui substrate — with one styled
`<Button>` rendered on the existing page as the end-to-end integration proof, while preserving the
01-01 `FlagStatus` workspace-link proof. Tasks 1 & 2 complete; Task 3 (Playwright render proof) is a
`checkpoint:human-verify` left for the orchestrator.

## What Was Built

### Task 1 — Next 15 → 16.2.9 + React 19.2.7 (commit `873faf3`)
- `apps/web/package.json` pins **exact** strings: `next` `16.2.9`, `react` `19.2.7`,
  `react-dom` `19.2.7`, `eslint-config-next` `16.2.9`; bumped `@types/react` `^19.2.17`,
  `@types/react-dom` `^19.2.3`.
- `scripts.lint`: `next lint` → `eslint .` (Next 16 removed `next lint`; `next build` no longer lints).
- `transpilePackages: ['@aerchain/shared-types']` preserved in `next.config.mjs` (Turbopack-supported).
- `pnpm-lock.yaml` regenerated to the new pins (non-frozen install).

### Task 2 — Tailwind v4 + shadcn substrate + Button (commit `7151b94`)
- Installed `tailwindcss@4.3.1` + `@tailwindcss/postcss@4.3.1` + `postcss`.
- `postcss.config.mjs` exports `{ plugins: { "@tailwindcss/postcss": {} } }` (no autoprefixer/content).
- `app/globals.css`: `@import "tailwindcss"` + `@import "tw-animate-css"`, `@custom-variant dark`,
  `@theme inline` token map, and the neutral oklch `:root` / `.dark` variable system.
- `app/layout.tsx` imports `./globals.css`.
- `components.json` (new-york style, neutral base, rsc:true, `@/*` aliases), `lib/utils.ts` exporting
  `cn()` (= `twMerge(clsx(...))`).
- ONE proof component `components/ui/button.tsx` — classic shadcn Button (`@radix-ui/react-slot`
  `Slot`, `cva` variants). No other component under `components/ui/`.
- `app/page.tsx` renders `<Button>Bid Desk</Button>` and **keeps** the `FlagStatus` type import/usage.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1/3 — Bug/Blocking] `eslint-config-next@16` is native flat config; FlatCompat bridge broke**
- **Found during:** Task 1 (`eslint .` failed).
- **Issue:** The plan/RESEARCH assumed `apps/web/eslint.config.mjs` (FlatCompat
  `compat.extends("next/core-web-vitals", "next/typescript")`) survives the upgrade. It does not —
  `eslint-config-next@16.2.9` now exports **flat config arrays**, so FlatCompat tried to JSON-serialize
  them as legacy shareable configs and threw `TypeError: Converting circular structure to JSON`.
- **Fix:** Rewrote `eslint.config.mjs` to the official Next 16 form — `import nextVitals from
  "eslint-config-next/core-web-vitals"` + `import nextTs from "eslint-config-next/typescript"`, spread
  both, keep the `ignores` block. Removed the now-unused `@eslint/eslintrc` dependency. Verified against
  the official Next 16 ESLint docs.
- **Files modified:** `apps/web/eslint.config.mjs`, `apps/web/package.json`.
- **Commit:** `873faf3`.

**2. [Next-16-driven] Mandatory `tsconfig.json` + `next-env.d.ts` changes**
- **Found during:** Task 1 build (`next build` reconfigured `tsconfig.json`).
- **Change:** Next 16 set `jsx: "react-jsx"` (automatic runtime, mandatory) and added
  `.next/dev/types/**/*.ts` to `include`; regenerated `next-env.d.ts` (auto-managed file). The `@/*`
  paths alias and `next` plugin are intact.
- **Files modified:** `apps/web/tsconfig.json`, `apps/web/next-env.d.ts`.
- **Commit:** `873faf3`.

**3. [Toolchain drift — reconciled to plan intent] shadcn CLI no longer offers new-york/neutral non-interactively**
- **Found during:** Task 2 (shadcn init).
- **Issue:** The current `shadcn@4.12.0` CLI replaced the `new-york`/`default` styles with named
  presets (Nova, Vega, …) selected via an **interactive** prompt that hangs in a non-TTY context.
  `-b neutral` is rejected (`-b` is the component-library base: `radix`|`base`, not a color), and the
  `radix` base path also prompts for confirmation. Running the only fully non-interactive path
  (`init -d`, the `base-nova` preset) produced output that **diverges from the locked plan**: a
  **Base UI** Button (not Radix), a `shadcn` **runtime** dependency, a **broken**
  `@import "shadcn/tailwind.css"` line (no such file in the installed package — would fail the build),
  and an injected **Geist font** in `layout.tsx` (theme/layout work the plan explicitly excluded).
- **Fix:** Kept the correct init outputs (neutral oklch token system, `cn()`, `tw-animate-css`,
  `@theme inline`) and reconciled the rest to the plan's locked classic radix-based new-york substrate
  by hand: removed the broken `shadcn/tailwind.css` import and the unused `--font-sans`/`--font-heading`
  theme self-references; removed `shadcn` and `@base-ui/react` deps, added `@radix-ui/react-slot@1.3.0`;
  rewrote `components.json` to `style: "new-york"`; rewrote `button.tsx` to the canonical new-york
  radix-Slot/`cva` Button (verified against the shadcn v4 registry source); reverted the injected Geist
  font from `layout.tsx` to keep `layout.tsx` minimal (no theme/layout work per scope).
- **Files modified:** `apps/web/components.json`, `apps/web/components/ui/button.tsx`,
  `apps/web/app/globals.css`, `apps/web/app/layout.tsx`, `apps/web/package.json`.
- **Commit:** `7151b94`.

**4. [Prettier] Formatted shadcn-generated files**
- `app/globals.css` (4-space preset indent) and `lib/utils.ts` (no semicolons) tripped Prettier;
  ran `prettier --write` on both to match the repo convention rather than carry exemptions.
- **Commit:** `7151b94`.

## Automated Verification Results (Tasks 1 & 2)

| Check | Result |
|---|---|
| `next` `16.2.9` / `react` `19.2.7` / `react-dom` `19.2.7` / `eslint-config-next` `16.2.9` exact pins | PASS |
| `scripts.lint` is `eslint .`; no `next lint` in package.json | PASS |
| `transpilePackages` present in `next.config.mjs` | PASS |
| `eslint.config.mjs` loads (native flat config) | PASS |
| `pnpm --filter @aerchain/web exec tsc --noEmit` | PASS (exit 0) |
| `pnpm --filter @aerchain/web exec eslint .` | PASS (exit 0) |
| `pnpm --filter @aerchain/web build` (Turbopack) | PASS (compiled, 3 static routes) |
| `postcss.config.mjs` has `@tailwindcss/postcss`; no `tailwind.config.*` | PASS |
| `components.json` (new-york/neutral) + `lib/utils.ts` exports `cn` | PASS |
| `components/ui/button.tsx` exists; ONLY file under `components/ui/` | PASS |
| `globals.css` has `@import "tailwindcss"` + oklch tokens via `tw-animate-css` | PASS |
| `layout.tsx` imports `./globals.css` | PASS |
| `page.tsx` imports/renders `Button` AND keeps `FlagStatus` | PASS |
| `prettier --check 'apps/web/**/*.{ts,tsx,css,json,mjs}'` | PASS (all files clean) |
| Backend `uv run pytest` (services/ai) | PASS (90 passed) |
| Backend `uv run ruff check .` (services/ai) | PASS (clean) |

## Known Stubs
None. The Button is an intentional integration proof; Phase 5 replaces the shell page with real
buyer screens (documented scope).

## Task 3 — Pending (NOT executed)
Task 3 is a `checkpoint:human-verify` (gate="blocking"): a Playwright render proof on the running dev
server per CLAUDE.md §11 — start `pnpm --filter @aerchain/web dev`, navigate the browser, confirm a
Tailwind-styled shadcn Button renders (themed, rounded — not an unstyled native button) alongside the
"workspace link verified (missing)" text, and capture a screenshot. This is left to the orchestrator
to drive; it was deliberately not run here.

## Commits
- `873faf3` — chore(01-05): upgrade apps/web to Next 16.2.9 + React 19.2.7
- `7151b94` — feat(01-05): wire Tailwind v4 + shadcn substrate + Button proof

## Self-Check: PASSED
All created files present on disk; both task commits found in git history.
