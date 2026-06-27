---
phase: 01-foundation
plan: "05"
type: security-audit
asvs_level: 1
block_on: open
threats_total: 3
threats_closed: 3
threats_open: 0
unregistered_flags: 0
verdict: SECURED
audited: 2026-06-27
branch: feat/next16-ui-substrate
---

# Phase 01 Plan 05 — Security Audit

Verification of the 3 declared threats in `01-05-PLAN.md` `<threat_model>` against the
implemented code. Implementation files were treated as read-only; this audit produced only
this `SECURITY.md`. Disposition-driven verification (mitigate → grep for pattern; accept →
confirm no new surface + log; transfer → n/a, none declared).

Scope reminder: this plan is pure build-time / UI tooling — Next 16.2.9 + React 19.2.7 upgrade,
Tailwind v4 (CSS-first) + shadcn substrate + one proof `Button`. No backend, runtime, auth,
network, secret, or user-input surface was introduced.

## Threat Verification Register

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-01-05-SC | Tampering (supply-chain) | mitigate | CLOSED | Exact pins + locked integrity hashes verified — see detail below |
| T-01-05-INFO | Information Disclosure | accept | CLOSED | No secret/env/PII/network surface in new code — see detail + accepted-risk log |
| T-01-05-DOS | Denial of Service (Turbopack) | accept | CLOSED | No custom webpack config; clean Turbopack default — see detail + accepted-risk log |

### T-01-05-SC — Tampering / supply-chain (mitigate) → CLOSED

Declared mitigation: exact version pins in `package.json` + committed `pnpm-lock.yaml`
(integrity-hash locked); all packages mainstream/GA; no `--force`/`--legacy-peer-deps`; no
`[ASSUMED]`/`[SUS]` packages.

Verified present in code:

- **Exact pins** in `apps/web/package.json` (no `^`/range on the security-critical four):
  - `next` `16.2.9` (line 18), `react` `19.2.7` (line 21), `react-dom` `19.2.7` (line 22),
    `eslint-config-next` `16.2.9` (line 31), `tailwindcss` `4.3.1` (line 23),
    `@tailwindcss/postcss` `4.3.1` (line 14), `@radix-ui/react-slot` `1.3.0` (line 13).
  - shadcn helper deps carry caret ranges (`class-variance-authority ^0.7.1`, `clsx ^2.1.1`,
    `tailwind-merge ^3.6.0`, `tw-animate-css ^1.4.0`, `lucide-react ^1.21.0`) — acceptable for L1
    because the lockfile pins the resolved version and integrity below.
- **Committed lockfile**: `pnpm-lock.yaml` present (lockfileVersion `9.0`), 450 `integrity:` sha512
  entries. The `apps/web` importer block resolves every specifier to the pinned version:
  `next → 16.2.9`, `react → 19.2.7`, `react-dom → 19.2.7`, `eslint-config-next → 16.2.9`,
  `tailwindcss → 4.3.1`, `@tailwindcss/postcss → 4.3.1`, `@radix-ui/react-slot → 1.3.0`,
  `class-variance-authority → 0.7.1`, `clsx → 2.1.1`, `tailwind-merge → 3.6.0`,
  `tw-animate-css → 1.4.0`, `lucide-react → 1.21.0`. All resolutions carry sha512 integrity.
- **No non-registry sources**: zero `resolution: {tarball|git|directory:}` entries for the new
  deps — every package is from the npm registry with an integrity hash.
- **No `--force` / `--legacy-peer-deps`**: no `.npmrc` exists in the repo or `apps/web`; no
  `legacy-peer-deps`/`--force`/`force=true` in any config or `package.json`.
- **No install scripts** in `apps/web/package.json` or root `package.json` (no
  `postinstall`/`preinstall`/`prepare`) — no executed-on-install code path was added.
- **Packages are mainstream/GA, no typosquats**: next (Vercel), react/react-dom (Meta),
  tailwindcss/@tailwindcss/postcss (Tailwind Labs), @radix-ui/react-slot (Radix/WorkOS),
  cva/clsx/tailwind-merge/tw-animate-css/lucide-react (established shadcn ecosystem). No
  `[ASSUMED]`/`[SUS]`/`[SLOP]` markers anywhere. SUMMARY.md confirms the executor REMOVED the
  CLI's broken/injected extras (`shadcn` runtime dep, `@base-ui/react`, broken
  `shadcn/tailwind.css` import, injected Geist font) — i.e. attack surface was reduced, not added.

Verdict: mitigation present in code. CLOSED.

### T-01-05-INFO — Information Disclosure (accept) → CLOSED

Declared disposition: accept — no secrets, env vars, API keys, or PII touched; CSS-first build
tooling + local UI source; no new network/trust surface.

Verified: a grep of `apps/web/{app,components,lib}` for `process.env`, `fetch(`,
`XMLHttpRequest`, `<script`, CDN/`googleapis`/`fonts.gstatic`, `next/font`, `crossorigin`,
`eval(`, and `dangerouslySetInnerHTML` returned **none**. The new source is:
`lib/utils.ts` (pure `cn()` class-merge), `components/ui/button.tsx` (local cva/Radix-Slot
component), `app/page.tsx` (renders the Button + a static `FlagStatus` string literal),
`app/layout.tsx` (static metadata, local `globals.css` import), `app/globals.css` (oklch CSS
tokens), and config files. No secret/env/PII handling and no network egress added.

Accepted-risk log entry (see Accepted Risks section). CLOSED.

### T-01-05-DOS — Denial of Service / Turbopack (accept) → CLOSED

Declared disposition: accept — no custom webpack config exists, so Turbopack's fail-fast on
stray config does not apply.

Verified: no `webpack` key in `apps/web/next.config.mjs` (only
`transpilePackages: ['@aerchain/shared-types']`), and no `tailwind.config.*` file exists.
Turbopack runs on its clean default. Build success was gated in Task 2 verification
(SUMMARY.md records `pnpm --filter @aerchain/web build` PASS).

Accepted-risk log entry (see Accepted Risks section). CLOSED.

## Unregistered Flags (new attack surface with no threat mapping)

None. SUMMARY.md has no `## Threat Flags` section. The deviations it records (native flat-config
ESLint migration, mandatory Next-16 `tsconfig`/`next-env.d.ts` changes, hand-reconciled shadcn
substrate, Prettier formatting) are build-time tooling reconciliations that reduce surface
(removed `shadcn` runtime dep, `@base-ui/react`, broken CSS import, injected font, unused
`@eslint/eslintrc`) — none introduce a runtime, network, secret, or input boundary.

## Independent Surface Scan (threats the model did not declare)

Light scan for surface this diff might introduce regardless of the register:

- `dangerouslySetInnerHTML` — absent.
- External script / font CDN fetch (`<script>`, googleapis, gstatic, `next/font`) — absent;
  the injected Geist font was reverted (SUMMARY.md deviation 3).
- `eval(` / dynamic code — absent.
- New `postinstall`/`preinstall`/`prepare` install scripts — absent.
- Network calls (`fetch`/`XMLHttpRequest`) or `process.env` reads in web source — absent.

Informational note (not a finding): `lucide-react@1.21.0` is the genuine Lucide icon package
(registry-resolved, sha512-locked, react-peer-bound) — its 1.x line is legitimate, not a
typosquat of the older 0.x line. It is also currently unimported by any source file (only
`@radix-ui/react-slot` is used by `Button`), so no icon code path executes in this phase.

## Accepted Risks Log

| ID | Risk | Rationale | ASVS L1 fit |
|----|------|-----------|-------------|
| T-01-05-INFO | UI substrate + build config could in principle expose data | No secrets/env/API keys/PII touched; CSS-first build tooling + local UI source only; no network/trust surface added (verified by grep). Low-value, build-time-only. | Acceptable — no in-scope L1 confidentiality control applies to static build tooling. |
| T-01-05-DOS | Turbopack (now default) build availability | No custom webpack config exists, so Turbopack fail-fast-on-stray-config does not apply; `next build --webpack` is the documented escape hatch if a future build breaks. Build success gated in Task 2. | Acceptable — build-time only, no production-availability dependency in this phase. |

## Verdict

**SECURED.** 3/3 threats closed (1 mitigate verified present in code, 2 accept verified as
genuinely low/no-surface and logged). `threats_open: 0`. No unregistered flags. The independent
surface scan found nothing the threat model missed. Phase may ship under `block_on: open`.
