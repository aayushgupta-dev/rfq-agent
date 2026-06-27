# Phase 01 Plan 05 — Research: Next.js 16 + Tailwind v4 + shadcn/ui

> Verified live against npm registry + official docs on 2026-06-27. All versions latest-stable
> (no canary/beta). Feeds the gsd-planner for plan 01-05. **Scope is locked: framework upgrade +
> UI substrate + ONE proof component — no speculative component set (those land in Phase 5).**

## Decision (locked with user)

- **Scope:** Substrate + 1 proof. Upgrade Next 15→16 + React 19.2; add Tailwind v4 + shadcn init
  (tokens/theme/`cn()` only); install exactly ONE shadcn component (`Button`) rendered on the
  existing page as the end-to-end integration proof (mirrors how 01-01 used the `FlagStatus`
  import to prove the workspace link). NO other components.
- **Placement:** New plan `01-05` in Phase 1 (foundation) — reopens the phase, plan count 4→5.
- **CLAUDE.md §5** already rephrased (commit d74ea83) to adopt shadcn/Tailwind — no longer a task.
- **Do NOT touch / replan 01-01..01-04** (complete and verified).
- Execute in an isolated worktree; re-verify (`next build`, `eslint .`, `tsc`, full pytest still
  green, Playwright render proof) before merge.

## Pinned versions

| Package | Exact | Note |
|---|---|---|
| `next` | 16.2.9 | latest stable (canary 16.3.0-canary.x, ignore) |
| `react` / `react-dom` | 19.2.7 (exact, not a range) | Next 16 uses React 19.2 internals; pin exact to avoid 19.1.x resolution |
| `@types/react` / `@types/react-dom` | latest 19.x | bump with React |
| `eslint-config-next` | 16.2.9 | tracks next; role changes (see ESLint note) |
| `tailwindcss` + `@tailwindcss/postcss` | 4.3.1 | **v4 — CSS-first, NO tailwind.config.js** |
| `postcss` | ^8 (shadcn pins ^8.5.6) | peer of @tailwindcss/postcss |
| `shadcn` (CLI) | 4.12.0 | `pnpm dlx shadcn@latest`; old `shadcn-ui` is dead |
| `class-variance-authority` | 0.7.1 | shadcn dep |
| `clsx` | 2.1.1 | `cn()` |
| `tailwind-merge` | 3.6.0 | `cn()` |
| `tw-animate-css` | 1.4.0 | **replaces deprecated `tailwindcss-animate`** for v4 |
| `lucide-react` | 1.21.0 | latest (now 1.x, not 0.x) |

## Next 16 migration — what affects us

Run codemod first: `pnpm dlx @next/codemod@canary upgrade latest` (the runner is pinned `@canary`
even when upgrading to `latest`). It auto-handles turbopack key move, `next lint`→ESLint CLI,
`middleware`→`proxy`, `unstable_` prefix removal.

- **🔴 `next lint` is REMOVED (not deprecated).** `next build` no longer lints. Our flat config
  (`apps/web/eslint.config.mjs` + `FlatCompat`) SURVIVES — Next 16 *defaults* to flat config, which
  is what we already have; `eslint-config-next@16` still publishes and FlatCompat still bridges it
  on ESLint 9. **Only action:** change `package.json` `lint` script from `next lint` → `eslint .`
  (codemod `next-lint-to-eslint-cli .` does this). Plan to drop FlatCompat at ESLint 10.
- **🟡 Turbopack is now the default** for `dev` and `build`. We have no custom webpack config →
  safe. `transpilePackages: ['@aerchain/shared-types']` is fully supported under Turbopack. Escape
  hatch if needed: `next build --webpack`.
- **🟡 Async request APIs fully removed (sync access gone):** `cookies()`/`headers()`/`draftMode()`
  and `params`/`searchParams` are async-only. Our 2-file shell doesn't touch them; but any NEW
  dynamic page must `await params`. Use `npx next typegen` for typed `PageProps`/`LayoutProps`.
- **🟢 Caching:** `revalidateTag` 2nd arg, `cacheLife`/`cacheTag` de-`unstable_`, PPR behind
  `cacheComponents: true`. None touches a minimal shell — note for later.
- **🟢 Minimums:** Node 20.9+ (have 26 ✅), TS 5.1+ (have ^5.7 ✅), React 19 (pinning ✅).
- **🟢 next.config.mjs:** keep `transpilePackages`; future turbopack opts go top-level `turbopack:{}`.

## Tailwind v4 setup (App Router, `apps/web`)

CSS-first, no config file. Auto source-detection (respects `.gitignore`); theme via CSS `@theme`.

1. `pnpm add tailwindcss@4.3.1 @tailwindcss/postcss@4.3.1 postcss` (inside apps/web)
2. `apps/web/postcss.config.mjs`:
   ```js
   const config = { plugins: { "@tailwindcss/postcss": {} } };
   export default config;
   ```
3. `apps/web/app/globals.css`: `@import "tailwindcss";` (shadcn init expands this)
4. Ensure `globals.css` imported in `app/layout.tsx`. No `content:[]`, no config, no autoprefixer.

## shadcn init (substrate)

shadcn 4.12.0 supports Tailwind v4 + React 19 + Next 16; **no peer flags on pnpm**. Run from
`apps/web` (NOT repo root, NOT `--monorepo`):

```bash
pnpm dlx shadcn@latest init      # base color: neutral; style: new-york (default is deprecated)
pnpm dlx shadcn@latest add button   # the ONE proof component
```

Generates: `components.json` (rsc:true, tsx:true, iconLibrary lucide, cssVariables:true, `@/*`
aliases), `lib/utils.ts` (`cn()` = twMerge(clsx(...))), rewrites `globals.css` with v4 tokens
(`@import "tailwindcss"`, `@import "tw-animate-css"`, `@custom-variant dark`, `@theme inline` block,
`:root`+`.dark` oklch vars, `@layer base`). Installs cva/clsx/tailwind-merge/tw-animate-css/lucide.

## Monorepo / ESLint notes

- Run init with **`apps/web` as cwd** (pnpm-workspace detection gotcha if run at root). Components
  live in `apps/web/components/ui` with `@/*` aliases.
- **Verify `apps/web/tsconfig.json` has `compilerOptions.paths {"@/*":["./*"]}`** BEFORE init — init
  errors if it can't resolve the alias.
- No interaction with `transpilePackages` (shadcn is local source). Tailwind v4 auto-detects sources
  from `globals.css` outward; add `@source "../../packages/..."` only if we later pull shared UI.

## Pitfalls (+ mitigation)

- `next lint` in scripts breaks → switch to `eslint .` (codemod).
- Turbopack fail-fast on stray webpack config → we have none; confirm clean `next build`.
- New dynamic routes forgetting `await params` → use `next typegen` in Phase 5.
- Installing `tailwindcss-animate` out of habit → use `tw-animate-css` for v4.
- npm `--legacy-peer-deps` muscle memory → not needed on pnpm; don't `--force` reflexively.
- Expecting `tailwind.config.js` → v4 has none; edit tokens in `globals.css`.
- Pin react/react-dom to exact 19.2.7 (not range) to avoid 19.1.x mismatch.

## Confidence / verify-at-init

- **High:** all versions (live npm), Next 16 breaking list + codemods, Tailwind v4 install, shadcn
  dep set + cn()/components.json/globals.css shape (official docs).
- **Verify interactively:** exact `components.json` style/baseColor the 4.12.0 CLI writes (pick
  `new-york` + `neutral`); confirm `rsc:true`. Watch init output for any non-fatal peer warning vs
  `next@16.2.9` (none found; React-19/Tailwind-v4 support is GA).

Sources: nextjs.org/docs/app/guides/upgrading/version-16 · tailwindcss.com/docs/installation/framework-guides/nextjs
· ui.shadcn.com/docs/{installation/next, tailwind-v4, monorepo, react-19} · npm registry (live 2026-06-27).
