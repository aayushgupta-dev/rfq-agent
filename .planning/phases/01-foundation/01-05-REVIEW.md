---
phase: 01-foundation
plan: 01-05
reviewed: 2026-06-27T00:00:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - apps/web/package.json
  - apps/web/eslint.config.mjs
  - apps/web/next.config.mjs
  - apps/web/tsconfig.json
  - apps/web/postcss.config.mjs
  - apps/web/app/globals.css
  - apps/web/lib/utils.ts
  - apps/web/components/ui/button.tsx
  - apps/web/app/layout.tsx
  - apps/web/app/page.tsx
  - apps/web/components.json
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: clean
---

# Plan 01-05: Code Review Report — Next 16 Upgrade + UI Substrate

**Reviewed:** 2026-06-27
**Depth:** deep (cross-file + live gate verification)
**Files Reviewed:** 11 (+ pnpm-lock.yaml inspected)
**Status:** clean

## Summary

Adversarial review of the Next 15 → 16.2.9 + React 19.2.7 upgrade and the Tailwind v4 +
shadcn/ui substrate (one proof `Button`) on `feat/next16-ui-substrate`. I verified the changes
not by trusting the passing gates, but by re-running them and inspecting the actual resolved
dependency graph and generated build output.

**Verdict: clean.** Every correctness concern in scope was checked and held up. No BLOCKER and no
WARNING findings. One INFO note (a harmless leftover in the pnpm store, self-healing on next
install) is recorded below for completeness.

### What I verified (not assumed)

- **ESLint config rewrite is correct and idiomatic for Next 16.** The FlatCompat/`@eslint/eslintrc`
  bridge is fully gone (`grep` confirms zero remaining references). The new config imports the
  native flat-config subpaths `eslint-config-next/core-web-vitals` and `eslint-config-next/typescript`.
  I confirmed both subpaths exist in `eslint-config-next@16.2.9`'s `exports` map and that each
  resolves to a spreadable default array (`...nextVitals`, `...nextTs` are valid). `core-web-vitals`
  internally re-exports the base `./index` config, so nothing was lost vs. the old
  `next/core-web-vitals` + `next/typescript` composition. `pnpm lint` (`eslint .`) runs clean.
- **`next lint` → `eslint .` migration is complete.** Next 16 removed `next lint`; the script swap
  is required and correct. No `next lint` reference remains anywhere in `apps/web`.
- **`transpilePackages` survived.** `next.config.mjs` still carries
  `transpilePackages: ["@aerchain/shared-types"]` — the workspace link is intact, and `page.tsx`
  still imports `FlagStatus` from it. Build resolves it cleanly.
- **tsconfig changes are correct.** `jsx: "react-jsx"` (the modern automatic runtime) is right for
  React 19 and does not break `layout.tsx`'s bare `React.ReactNode` reference — `tsc --noEmit`
  exits 0 because the global `react` types are pulled via `next-env.d.ts`. The `.next/dev/types/**`
  include and `next-env.d.ts`'s `import "./.next/dev/types/routes.d.ts"` match Next 16's new type
  output location — I confirmed `next build` actually generates `.next/dev/types/routes.d.ts`. The
  `@/*` path alias is preserved.
- **Tailwind v4 wiring is correct end-to-end.** `postcss.config.mjs` uses the v4 `@tailwindcss/postcss`
  plugin; `globals.css` uses the v4 `@import "tailwindcss"` + `@theme inline` token model with the
  shadcn oklch tokens; `layout.tsx` imports `globals.css`. I inspected the generated CSS chunk and
  confirmed the oklch tokens and Button utility classes (`inline-flex`, `--primary`, etc.) actually
  compile — the substrate flows input → tokens → rendered styles.
- **Button is a correct shadcn/Radix Slot button.** Classic radix `new-york` variant: `cva` variants,
  `@radix-ui/react-slot` `Slot` for `asChild`, `cn` from `@/lib/utils`, `data-slot="button"`. No Base
  UI, no broken imports, no unstyled fallback. `cn` (`twMerge(clsx(inputs))`) is the canonical helper.
- **Dependencies are legitimate, not supply-chain risks.** `lucide-react@^1.21.0` looked suspicious
  (lucide-react was historically 0.x) but `1.21.0` is the genuine current `latest` on npm — not a
  typo or squat. `@radix-ui/react-slot@1.3.0`, `tailwind-merge@3.6.0`, `cva@0.7.1`,
  `tw-animate-css@1.4.0`, `tailwindcss@4.3.1` all resolve to expected versions with React 19.2.7
  satisfying peers. No new secrets, network surface, or runtime code paths introduced — purely
  build-time/UI tooling, as expected.
- **No scope creep.** Exactly one component (`Button`), no extra screens, no theme toggler, no
  premature infra. `components.json` is standard shadcn config. The `@custom-variant dark` + `.dark`
  token block ships without a `.dark` toggler, but that is the stock shadcn substrate (the dark
  tokens are inert until a theme is wired in Phase 5) — correct kept-substrate, not dead code to flag.

## Info

### IN-01: Stale `eslint-config-next@15.5.19` lingering in the pnpm content-addressable store

**File:** `pnpm-lock.yaml` (store artifact, not an importer entry)
**Issue:** The pnpm store still contains an `eslint-config-next@15.5.19` directory under
`node_modules/.pnpm/`. This is a leftover from the pre-upgrade install, **not** a real dependency:
the `apps/web` importer in the lockfile correctly declares only `eslint-config-next@16.2.9`, and no
`package.json` in the repo references v15. It carries no security or correctness impact and does not
affect lint/build/typecheck (all pass clean).
**Fix:** Optional cosmetic cleanup — `pnpm install` (or `pnpm prune`) on a clean checkout drops the
orphaned store entry. No action required for this PR; flagged only so it isn't mistaken for a real
dual-version situation later.

## Gate Verification (re-run, not trusted)

| Gate | Result |
|---|---|
| `pnpm lint` (`eslint .`) | clean, exit 0 |
| `npx tsc --noEmit` | clean, exit 0 |
| `pnpm build` (`next build`, Turbopack) | success, 3 routes prerendered, generates `.next/dev/types` |
| Generated CSS contains oklch tokens + Button utilities | confirmed |

---

_Reviewed: 2026-06-27_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
