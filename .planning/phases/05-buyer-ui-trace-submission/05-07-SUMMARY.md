---
phase: "05"
plan: "07"
subsystem: buyer-ui-trace-submission
tags: [trace-screen, prompt-pack, readme, write-up, architecture-docs, demo-script, submission]
dependency_graph:
  requires: ["05-04", "05-05"]
  provides: ["UI-05", "SHIP-02", "SHIP-03", "SHIP-04", "SHIP-05"]
  affects: []
tech_stack:
  added: []
  patterns:
    - "Server Component reads public/traces/ via fs.readdir at request time"
    - "Client-only TraceTabs for tab switching interactivity (minimal 'use client' surface)"
    - "Static PROMPT_PACK const in page.tsx — avoids Python shell-out at build time"
    - "Amber bg-amber-50 row highlighting for model_proposed != clamped_to in clamp diff"
    - "Mermaid diagrams in docs/architecture/ — renders on GitHub, no tooling required"
key_files:
  created:
    - apps/web/app/(buyer)/trace/page.tsx
    - apps/web/app/(buyer)/trace/trace-tabs.tsx
    - README.md
    - docs/write-up.md
    - docs/architecture/system-diagram.md
    - docs/architecture/ai-pipeline-diagram.md
    - docs/demo/demo-script.md
  modified: []
decisions:
  - "Static PROMPT_PACK const in page.tsx (not fs.readdir on Python files): avoids cross-language file parsing at build time; values derived from registry.py frontmatter"
  - "trace-tabs.tsx split from page.tsx: minimal 'use client' boundary — Server Component fetches all traces, client component handles tab switching only"
  - "Demo script uses behavioral narration throughout: 'observe on screen', 'may vary run-to-run' — no hard-coded verdicts per D-02 and D-19"
  - "docs/architecture/ directory created fresh (did not exist in worktree)"
metrics:
  duration: "~35 min"
  completed_date: "2026-06-28"
  tasks_completed: 2
  files_created: 7
  files_modified: 0
---

# Phase 05 Plan 07: Prompt Trace Screen + Submission Package Summary

Trace screen (UI-05) and complete submission documentation (SHIP-02..05) delivered.
The trace screen is the "code disproves model" proof: amber-highlighted clamp diffs show
every place the comparability clamp overruled the model's verdict.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Prompt Trace screen (UI-05, D-15) | 45e1404 | apps/web/app/(buyer)/trace/page.tsx, trace-tabs.tsx |
| 2 | README + write-up + architecture diagrams + demo script (SHIP-02..05) | b0121ea | README.md, docs/write-up.md, docs/architecture/system-diagram.md, docs/architecture/ai-pipeline-diagram.md, docs/demo/demo-script.md |

## What Was Built

### Task 1 — Prompt Trace screen

`apps/web/app/(buyer)/trace/page.tsx` is a Next.js Server Component that:
- Reads `public/traces/` via `fs.readdir` at request time — picks up all 6 trace files,
  deduplicated, in canonical order (comparison traces first per D-19 demo arc)
- Embeds a static `PROMPT_PACK` const with the 7 prompts' id/version/intent/docs_url
  (derived from `registry.py` frontmatter — no Python shell-out needed)
- Passes parsed `TraceData[]` to `TraceTabs` (client component, minimal boundary)

`apps/web/app/(buyer)/trace/trace-tabs.tsx` ("use client"):
- `Tabs` + `TabsList`/`TabsTrigger`/`TabsContent` from shadcn for tab switching
- `TracePanel`: pipeline timeline (4 stages: Input → Prompt → Raw output → Final)
- `ClampDiff`: comparison traces — rows where `model_proposed !== clamped_to` get
  `bg-amber-50`; header: "Code overruled the model on N verdict(s)"
- `DowngradeDiff`: extraction traces — same pattern for `downgrade_report.entries`
- `ScrollArea` wraps the raw model output JSON block (`font-mono text-xs`)
- `CopyButton`: `navigator.clipboard.writeText` for raw output
- `data-testid="trace-diff"` on both diff cards for Playwright

TypeScript check: `pnpm tsc --noEmit` exits 0 (verified via main repo node_modules).

### Task 2 — Submission documentation

**README.md** (SHIP-02): Setup, env vars table (OPENAI_API_KEY, MODEL_REASONING, MODEL_CHEAP,
NEXT_PUBLIC_AI_BASE_URL), local run instructions, sample flow, tests, deployment (Vercel + Render),
assumptions, model/API requirements.

**docs/write-up.md** (SHIP-03): 1686 words covering problem statement, assumptions, prompt
architecture (7-prompt layer diagram in text), product thinking (§24 anti-patterns avoided),
extraction approach (grounding gate), comparison approach (comparability clamp), UI/UX decisions,
limitations, what's next.

**docs/architecture/system-diagram.md** (SHIP-05 part 1): Mermaid `flowchart LR` — browser
to Vercel/Next.js to Render/FastAPI to OpenAI. Shows CORS boundary, SSE path, session cache,
env seam, trace file route handler.

**docs/architecture/ai-pipeline-diagram.md** (SHIP-05 part 2): Mermaid `flowchart TD` — full
agent pipeline from rfq-gen/vendor-gen through extraction agent + grounding gate +
comparison agent + comparability clamp + clarification agent → SSE → browser. Grounding gate
and clamp labelled "code-enforced." Includes Prompt Pack summary table.

**docs/demo/demo-script.md** (SHIP-04): 5-section storyboard with timestamps and narration
copy. Arc is rubric-driven per D-19: messy vendor → gaps + evidence → non-comparable matrix →
trace "code disproves model" moment → Prompt Pack. Behavioral narration throughout — no
hard-coded verdicts (satisfies D-02 live-model requirement).

## Deviations from Plan

None — plan executed exactly as written.

The `trace_vendor_cheap` count in page.tsx is 2 (one in the order array, one in the filter),
but this produces exactly 1 tab — the deduplication logic (`order.filter` + `jsonFiles.filter`)
is correct. The acceptance criteria (≤1 tab rendered) is met.

## Known Stubs

None. The Trace screen renders real trace data from `public/traces/*.json`. The Prompt Pack
list is a static const derived from real frontmatter values. Documentation is complete prose,
not placeholders.

## Threat Flags

None. README contains only env var names (no values). Trace file path sanitization was
implemented in Plan 05-04 (T-05-04-A); this plan adds no new network endpoints or trust
boundaries.

## Self-Check

**Commits exist:**
- 45e1404: `feat(05-07): add Prompt Trace screen (UI-05, D-15)` — FOUND
- b0121ea: `docs(05-07): add README, write-up, architecture diagrams, demo script (SHIP-02..05)` — FOUND

**Files created:**
- apps/web/app/(buyer)/trace/page.tsx — FOUND
- apps/web/app/(buyer)/trace/trace-tabs.tsx — FOUND
- README.md — FOUND
- docs/write-up.md — FOUND
- docs/architecture/system-diagram.md — FOUND
- docs/architecture/ai-pipeline-diagram.md — FOUND
- docs/demo/demo-script.md — FOUND

**Acceptance criteria:**
- `grep -c "Code overruled the model"` trace-tabs.tsx: 2 (in ClampDiff + DowngradeDiff) — PASS
- `grep -c "bg-amber-50"` trace-tabs.tsx: 2 — PASS
- `grep -c "ScrollArea"` trace-tabs.tsx: 3 — PASS
- `grep -c "Prompt Pack"` page.tsx: 2 — PASS
- `grep -c 'data-testid="trace-diff"'` trace-tabs.tsx: 2 — PASS
- `pnpm tsc --noEmit` exits 0 — PASS
- `grep -c "OPENAI_API_KEY"` README.md: 4 — PASS
- `grep -c "pnpm dev"` README.md: 1 — PASS
- `grep -ci "prompt architecture"` write-up.md: 1 — PASS
- `grep -c "mermaid"` system-diagram.md: 1 — PASS
- `grep -c "mermaid"` ai-pipeline-diagram.md: 1 — PASS
- `grep -ci "code disproves"` demo-script.md: 3 — PASS
- `wc -w docs/write-up.md`: 1686 ≥ 800 — PASS
- behavioral narration in demo-script.md: "observe on screen", "may vary", "find.*amber": 3 — PASS
- no hard-coded verdicts in demo-script.md: 0 — PASS

## Self-Check: PASSED
