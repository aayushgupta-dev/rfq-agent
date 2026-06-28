# Phase 5: Buyer UI, Trace & Submission — Pattern Map

**Mapped:** 2026-06-28
**Files analyzed:** 18 new/modified files
**Analogs found:** 14 / 18 (4 greenfield, no close analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `apps/web/app/layout.tsx` (modify) | layout | — | `apps/web/app/layout.tsx` | exact (the file itself) |
| `apps/web/app/page.tsx` (modify) | route | request-response | `apps/web/app/page.tsx` | exact |
| `apps/web/app/(buyer)/layout.tsx` | layout | — | `apps/web/app/layout.tsx` | role-match |
| `apps/web/app/(buyer)/rfq/page.tsx` | component | request-response | `apps/web/app/page.tsx` | role-match |
| `apps/web/app/(buyer)/input/page.tsx` | component | request-response | `apps/web/app/page.tsx` | role-match |
| `apps/web/app/(buyer)/extraction/page.tsx` | component | streaming | `apps/web/app/page.tsx` | role-match |
| `apps/web/app/(buyer)/comparison/page.tsx` | component | streaming | `apps/web/app/page.tsx` | role-match |
| `apps/web/app/(buyer)/trace/page.tsx` | component | request-response | `apps/web/app/page.tsx` | role-match |
| `apps/web/app/api/traces/[name]/route.ts` | route | request-response | — | no analog |
| `apps/web/lib/sse.ts` | utility | streaming | — | no analog (greenfield) |
| `apps/web/lib/session.ts` | utility | — | — | no analog (greenfield) |
| `apps/web/lib/api.ts` | utility | request-response | — | no analog (greenfield) |
| `apps/web/contexts/BuyerContext.tsx` | provider | — | — | no analog (greenfield) |
| `apps/web/components/stage-rail.tsx` | component | — | `apps/web/components/ui/button.tsx` | partial-match |
| `apps/web/components/flag-badge.tsx` | component | — | `apps/web/components/ui/button.tsx` | partial-match |
| `apps/web/components/comparability-badge.tsx` | component | — | `apps/web/components/ui/button.tsx` | partial-match |
| `apps/web/components/evidence-snippet.tsx` | component | — | `apps/web/components/ui/button.tsx` | partial-match |
| `apps/web/components/stream-progress.tsx` | component | streaming | `apps/web/components/ui/button.tsx` | partial-match |
| `services/ai/api/app.py` (modify) | middleware + route | request-response + streaming | `services/ai/api/app.py` | exact |
| `services/ai/tests/test_file_extract.py` | test | — | `services/ai/tests/test_sse_demo.py` | role-match |
| `services/ai/tests/test_input_wrap.py` | test | — | `services/ai/tests/test_sse_demo.py` | role-match |
| `docs/qa/phase5-playwright.spec.ts` | test | — | `services/ai/tests/test_sample_fixtures.py` | partial-match |

---

## Pattern Assignments

### `apps/web/app/(buyer)/layout.tsx` (layout)

**Analog:** `apps/web/app/layout.tsx`

**Imports pattern** (lines 1–3):
```typescript
import type { Metadata } from "next";
import "./globals.css";
```

**Core pattern** — extend with stage rail wrapper:
```typescript
// Root layout: html/body only, no chrome (UI-SPEC layout architecture)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

The buyer layout (`(buyer)/layout.tsx`) wraps children with the two-column shell — stage rail + main content — without repeating `<html>/<body>`:
```typescript
// (buyer)/layout.tsx — adds the flex shell described in UI-SPEC §Layout Architecture
// No html/body here — root layout owns those
export default function BuyerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <StageRail />
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-5xl mx-auto p-8">{children}</div>
      </main>
    </div>
  );
}
```

---

### `apps/web/app/page.tsx` (modify — redirect to /rfq)

**Analog:** `apps/web/app/page.tsx` (lines 1–18, current placeholder)

Current file imports `FlagStatus` and `Button` as substrate proofs. Phase 5 replaces the body with a redirect:
```typescript
// Replace body with redirect — keep no imports except redirect
import { redirect } from "next/navigation";
export default function Home() {
  redirect("/rfq");
}
```

The `FlagStatus` import proof and `Button` demo are no longer needed once the real buyer screens exist.

---

### `apps/web/app/(buyer)/rfq/page.tsx` (component, request-response)

**Analog:** `apps/web/app/page.tsx`

**Imports pattern** — add shared-types + cn:
```typescript
import type { RFQ } from "@aerchain/shared-types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
// shadcn Card, Separator added via `npx shadcn@latest add card separator`
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
```

**Client boundary** — data-fetching pages are Server Components; use `"use client"` only when needed for interactivity (the regen button):
```typescript
// Server Component by default (App Router)
// Fetch committed rfq.json at render time — no useEffect, no spinner
import rfqData from "../../../../data/rfq.json"; // or from public/rfq.json
```

**Core pattern** — server-side data load + client island for the regen button:
```typescript
// ponytail: Server Component renders committed rfq.json instantly (D-21);
// only the Regen button needs "use client" — isolate it to a child component.
export default async function RfqPage() {
  const rfq = rfqData as RFQ;
  return (
    <>
      <RfqSummaryCard rfq={rfq} />
      <Separator className="my-6" />
      <RfqBody rfq={rfq} />
    </>
  );
}
```

---

### `apps/web/app/(buyer)/extraction/page.tsx` (component, streaming)

**Analog:** `apps/web/app/page.tsx` (structure); SSE pattern from RESEARCH.md Pattern 1

**Imports pattern:**
```typescript
"use client"; // needs useState, useEffect for SSE + session cache
import type { ExtractionResult } from "@aerchain/shared-types";
import { cn } from "@/lib/utils";
import { useBuyerContext } from "@/contexts/BuyerContext";
import { streamSSE } from "@/lib/sse";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FlagBadge } from "@/components/flag-badge";
import { EvidenceSnippet } from "@/components/evidence-snippet";
import { StreamProgress } from "@/components/stream-progress";
```

**Session-cache check before SSE** (D-02 — must not re-run if cached):
```typescript
// ponytail: check session cache first; only stream if result is absent
const { extractions, setExtraction, loadedVendors } = useBuyerContext();
const cached = extractions[selectedVendor];
// If cached → render immediately; if not → start SSE stream
```

**Error state** (D-25 — never blank screen):
```typescript
// On SSE error event: show Alert, hide Progress — never leave a blank screen
if (event.type === "error") {
  setError(event.payload.message);
  setStreaming(false);
}
// Render:
{error && (
  <Alert variant="destructive">
    <AlertDescription>
      Extraction could not complete. {error} — Try reloading or check the AI service is running.
    </AlertDescription>
  </Alert>
)}
```

---

### `apps/web/lib/sse.ts` (utility, streaming)

**Analog:** None in codebase — greenfield. Pattern from RESEARCH.md Pattern 1 (verified against Next.js docs).

**Full implementation** (copy verbatim from RESEARCH.md):
```typescript
// lib/sse.ts — ponytail: one generic parser handles all SSE endpoints
export type EventEnvelope = { type: string; payload: unknown };

export async function* streamSSE(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<EventEnvelope> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE lines: "data: <json>\n\n" — chunks may straddle read() calls (Pitfall 1)
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      if (part.startsWith("data: ")) {
        yield JSON.parse(part.slice(6)) as EventEnvelope;
      }
    }
  }
}
```

**Critical:** The `buf` accumulation across `read()` calls is mandatory — SSE events can straddle chunk boundaries (RESEARCH.md Pitfall 1). Do not parse each `value` independently.

---

### `apps/web/contexts/BuyerContext.tsx` (provider)

**Analog:** None in codebase — greenfield. Pattern from RESEARCH.md Pattern 2.

**Imports + shape:**
```typescript
"use client";
import { createContext, useContext, useState, useEffect } from "react";
import type { VendorResponse, ExtractionResult, ComparisonResult } from "@aerchain/shared-types";

interface BuyerState {
  loadedVendors: VendorResponse[];
  extractions: Record<string, ExtractionResult>; // keyed by vendor_name
  comparison: ComparisonResult | null;
  setLoadedVendors: (v: VendorResponse[]) => void;
  setExtraction: (name: string, r: ExtractionResult) => void;
  setComparison: (r: ComparisonResult) => void;
}
```

**sessionStorage hydration pattern** (D-02):
```typescript
// ponytail: sessionStorage is tab-scoped; correct for a single-buyer prototype (Pitfall 6)
// Hydrate from sessionStorage on mount; persist on each state change
const [extractions, setExtractionsState] = useState<Record<string, ExtractionResult>>(() => {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(sessionStorage.getItem("extractions") ?? "{}");
  } catch { return {}; }
});
```

---

### `apps/web/components/stage-rail.tsx` (component)

**Analog:** `apps/web/components/ui/button.tsx` (lines 1–54) — copy the import/cn pattern

**Imports pattern** (mirror button.tsx conventions):
```typescript
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
// lucide icons — already installed (components.json iconLibrary: lucide)
import { FileText, Upload, Search, BarChart2, GitBranch } from "lucide-react";
```

**`cn` usage pattern** (copy from `button.tsx` line 8):
```typescript
// button.tsx uses cn() for conditional class composition — copy this exactly
className={cn(
  "flex items-center gap-3 px-4 min-h-11 text-xs font-semibold rounded-md transition-colors",
  isActive
    ? "bg-primary text-primary-foreground"         // --primary accent (UI-SPEC Color §)
    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
)}
```

**Responsive collapse** (D-26 — icon-only at md, full labels at lg):
```typescript
// Stage rail width: w-60 at lg, w-[60px] at md, hidden at sm with drawer
// ponytail: responsive via Tailwind classes only — no JS resize handler
<nav className="hidden md:flex md:w-[60px] lg:w-60 shrink-0 flex-col bg-card border-r border-border">
```

---

### `apps/web/components/flag-badge.tsx` (component)

**Analog:** `apps/web/components/ui/button.tsx` — copy the `cva` variant pattern

**Core pattern** (cva variant map from button.tsx lines 7–31):
```typescript
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
// Badge component installed via: npx shadcn@latest add badge
import { Badge } from "@/components/ui/badge";
import type { FlagStatus } from "@aerchain/shared-types";

// UI-SPEC Color § flag badge palette — copy these token names verbatim
const flagVariants: Record<FlagStatus, string> = {
  present:     "bg-green-100 text-green-800",
  missing:     "bg-red-100 text-red-800",      // high-visibility — absence first-class (§8)
  unclear:     "bg-amber-100 text-amber-800",
  conflicting: "bg-orange-100 text-orange-800",
  unsupported: "bg-slate-100 text-slate-600",
};

export function FlagBadge({ status }: { status: FlagStatus }) {
  return (
    <Badge className={cn("px-2 py-1 text-xs font-semibold", flagVariants[status])}>
      {status}
    </Badge>
  );
}
```

---

### `apps/web/components/comparability-badge.tsx` (component)

**Analog:** `apps/web/components/ui/button.tsx` — same cva/cn pattern

```typescript
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { ComparabilityVerdict } from "@aerchain/shared-types";

// UI-SPEC Color § comparability badge palette
const comparabilityVariants: Record<ComparabilityVerdict, string> = {
  comparable:     "bg-primary text-primary-foreground",   // accent — "all clear"
  partially:      "bg-amber-100 text-amber-800",
  not_comparable: "bg-red-100 text-red-800",
};

export function ComparabilityBadge({ verdict }: { verdict: ComparabilityVerdict }) {
  return (
    <Badge className={cn("px-2 py-1 text-xs font-semibold", comparabilityVariants[verdict])}>
      {verdict.replace("_", " ")}
    </Badge>
  );
}
```

---

### `apps/web/components/evidence-snippet.tsx` (component)

**Analog:** `apps/web/components/ui/button.tsx` (import/cn conventions)

**Collapsible pattern** (shadcn Collapsible — RESEARCH.md component list):
```typescript
"use client"; // Collapsible requires client (radix stateful)
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

// D-07: snippet always visible inline; Collapsible opens source passage
// Inner padding: px-2 py-1 (UI-SPEC Spacing § evidence snippet pill)
export function EvidenceSnippet({ snippet, sourcePassage }: { snippet: string; sourcePassage?: string }) {
  return (
    <Collapsible>
      <p className="text-xs text-muted-foreground px-2 py-1">
        <span className="font-semibold">Source:</span> {snippet}
      </p>
      {sourcePassage && (
        <>
          <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground">
            <ChevronDown className="size-3" /> Show in context
          </CollapsibleTrigger>
          <CollapsibleContent>
            {/* Highlighted span uses --primary underline (UI-SPEC Color §) */}
            <p className="text-xs border-l-2 border-primary pl-2 mt-1">{sourcePassage}</p>
          </CollapsibleContent>
        </>
      )}
    </Collapsible>
  );
}
```

---

### `apps/web/components/stream-progress.tsx` (component, streaming)

**Analog:** `apps/web/components/ui/button.tsx` (import/cn pattern); SSE shape from `services/ai/schemas/events.py`

```typescript
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// D-25: full-width, no horizontal padding (UI-SPEC Spacing § streaming progress bar)
// status text from SSE "status" events; value 0→100 estimated linearly across stages
export function StreamProgress({ status, value }: { status: string; value: number }) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{status}</p>
      <Progress value={value} className="w-full" />
    </div>
  );
}
```

---

### `apps/web/app/api/traces/[name]/route.ts` (route, request-response)

**Analog:** None in codebase. Pattern: Next.js App Router Route Handler (filesystem read).

```typescript
// ponytail: Route Handler avoids duplicating trace files into public/ (RESEARCH.md §Trace Screen)
import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs/promises";

export async function GET(_req: NextRequest, { params }: { params: { name: string } }) {
  // Sanitize: only allow alphanumeric + underscore + hyphen + dot (no path traversal)
  const name = params.name.replace(/[^a-zA-Z0-9_.-]/g, "");
  const filePath = path.resolve(process.cwd(), "../../docs/traces", name);
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return new NextResponse(content, { headers: { "Content-Type": "application/json" } });
  } catch {
    return NextResponse.json({ error: "trace not found" }, { status: 404 });
  }
}
```

**Note:** `process.cwd()` behavior on Vercel must be validated during Wave 0 (RESEARCH.md Pitfall 4 / Open Question 1). If it resolves to `apps/web/` instead of monorepo root, copy traces to `apps/web/public/traces/` and read from there.

---

### `services/ai/api/app.py` (modify — CORS + 2 new endpoints)

**Analog:** `services/ai/api/app.py` itself — the file is the analog; add to its existing patterns.

**CORS addition** (Pattern 5 from RESEARCH.md — insert after `app = FastAPI(...)` line 58):
```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://*.vercel.app",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

**New endpoint — file text extraction** (Pattern 3 from RESEARCH.md):
```python
from fastapi import UploadFile, File
# Requires python-multipart in pyproject.toml (RESEARCH.md Pitfall 2)

@app.post("/extract/file-text")
async def extract_file_text(file: UploadFile = File(...)) -> dict:
    """Extract plain text from an uploaded vendor file (best-effort, no OCR).

    Returns {"text": str, "filename": str, "chars": int}.
    < 200 chars = weak extraction; caller shows paste-fallback Alert (D-05).
    Security: only file bytes + extension used; filename discarded from _extract_text
    to prevent path traversal (T-path in RESEARCH.md security domain).
    """
    content = await file.read()
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    text = _extract_text(content, suffix)
    return {"text": text, "filename": file.filename, "chars": len(text)}
```

**New endpoint — raw-text wrapper** (Pattern 4 from RESEARCH.md):
```python
class RawTextInput(BaseModel):
    vendor_name: str = pydantic_Field(max_length=200)
    raw_text: str = pydantic_Field(max_length=200_000)

@app.post("/input/raw-text")
async def wrap_raw_text(req: RawTextInput) -> dict:
    """Wrap buyer-supplied raw text into a minimal VendorResponse (D-06).

    Feeds the existing /extract/vendor contract without any agent change.
    The extraction agent does all structuring — the buyer only names the vendor.
    """
    vendor = VendorResponse(
        vendor_name=req.vendor_name,
        persona="buyer-upload",
        mess_spec=[],
        source_id=f"upload-{req.vendor_name[:20]}",
        format_label="text",
        raw_text=req.raw_text,
    )
    return vendor.model_dump(mode="json")
```

**Follow the existing request model pattern** (lines 61–65 of `app.py`):
```python
# Existing pattern: pydantic BaseModel + pydantic_Field with max_length
class VendorGenRequest(BaseModel):
    persona: str = pydantic_Field(max_length=64)
    rfq_text: str | None = pydantic_Field(default=None, max_length=200_000)
# Copy this exact style for RawTextInput — same import, same field style
```

---

### `services/ai/tests/test_file_extract.py` (test)

**Analog:** `services/ai/tests/test_sse_demo.py` (lines 1–160)

**Test structure to copy:**
```python
# Copy these patterns from test_sse_demo.py:
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from api.app import app  # TestClient without context manager — skips lifespan

class TestFileExtractRoute:
    """POST /extract/file-text — tests for each format."""

    def test_pdf_returns_text(self) -> None: ...
    def test_docx_returns_text(self) -> None: ...
    def test_weak_extraction_returns_chars_not_error(self) -> None:
        # < 200 chars is NOT an error — caller decides to show Alert
        ...
```

**Fixture pattern** (from `test_sample_fixtures.py` lines 22–29):
```python
from scripts.codegen import repo_root
_DATA_DIR = repo_root() / "data"
# Use real fixture files from data/ for integration; use synthetic bytes for unit
```

---

### `services/ai/tests/test_input_wrap.py` (test)

**Analog:** `services/ai/tests/test_sse_demo.py`

```python
from fastapi.testclient import TestClient
from api.app import app
from schemas.domain import VendorResponse

def test_raw_text_wrap_returns_valid_vendor_response() -> None:
    client = TestClient(app)
    r = client.post("/input/raw-text", json={
        "vendor_name": "Test Vendor",
        "raw_text": "We offer marketing services. Price: $10,000. Timeline: 6 weeks.",
    })
    assert r.status_code == 200
    # Must deserialize to VendorResponse — proves the output feeds /extract/vendor
    vendor = VendorResponse.model_validate(r.json())
    assert vendor.vendor_name == "Test Vendor"
    assert vendor.raw_text is not None
```

---

### `docs/prompts/*.md` (5 new prompt docs — PROMPT-02)

**Analog:** `docs/prompts/extraction-prompt-doc.md` (lines 1–40, already written)

**Structure to copy verbatim:**
```markdown
# [Prompt Name] Prompt Documentation

**Prompt:** `services/ai/prompts/[id].v1.md`
**Version:** 1
**Model tier:** reasoning | cheap

---

## What It Does
[2–3 sentences]

---

## Why It Is Structured This Way
[rationale paragraphs — same depth as extraction-prompt-doc.md]

---

## How It Handles Unreliable / Missing / Conflicting Information
[specific handling — maps to failure_handling frontmatter field]
```

**Frontmatter source** for each prompt's `intent` and `failure_handling` fields — read from the corresponding `.v1.md` in `services/ai/prompts/`. The extraction prompt frontmatter (lines 1–20 of `extraction.v1.md`) is the model — same YAML keys (`id`, `version`, `intent`, `model_tier`, `failure_handling`) for all 7 prompts.

---

## Shared Patterns

### Import: `cn` for class composition
**Source:** `apps/web/lib/utils.ts` (lines 1–6)
**Apply to:** Every component in `apps/web/components/` and every page in `app/(buyer)/`
```typescript
import { cn } from "@/lib/utils";
// Usage: className={cn("base-classes", conditional && "conditional-class")}
```
Never use string concatenation for Tailwind classes — `cn()` handles deduplication via tailwind-merge.

### Import: Shared types
**Source:** `apps/web/app/page.tsx` line 5
**Apply to:** All buyer screen pages and context
```typescript
import type { ExtractionResult, ComparisonResult, FlagStatus, ComparabilityVerdict } from "@aerchain/shared-types";
// Use `import type` — these are purely type imports (no runtime cost)
```

### Component structure: shadcn new-york style
**Source:** `apps/web/components/ui/button.tsx` (lines 1–54)
**Apply to:** All custom components in `apps/web/components/`
- Use `import * as React from "react"` (not `import React from "react"`)
- Export as named function (not default), matching the shadcn pattern
- Use `data-slot="<name>"` attribute on the root element
- Prop type: `React.ComponentProps<"element"> & CustomProps` for native element wrappers

### FastAPI endpoint: pydantic request model + validation
**Source:** `services/ai/api/app.py` lines 61–65, 103–138
**Apply to:** `POST /extract/file-text`, `POST /input/raw-text`
```python
from pydantic import BaseModel
from pydantic import Field as pydantic_Field

class RequestModel(BaseModel):
    field: str = pydantic_Field(max_length=N)
# Use model_validator for cross-field constraints (see ExtractionRequest lines 125–138)
```

### FastAPI endpoint: SSE streaming response
**Source:** `services/ai/api/app.py` lines 233–250
**Apply to:** Any future streaming endpoints (none new in Phase 5 — existing endpoints unchanged)
```python
from sse_starlette import EventSourceResponse
from collections.abc import AsyncGenerator
from schemas.events import EventEnvelope

async def _generate() -> AsyncGenerator[dict, None]:
    async for chunk in graph.astream(..., stream_mode="custom"):
        yield {"data": EventEnvelope(**chunk).model_dump_json()}
    yield {"data": EventEnvelope(type="done", payload={}).model_dump_json()}

return EventSourceResponse(_generate())
```

### FastAPI test: TestClient without lifespan
**Source:** `services/ai/tests/test_sse_demo.py` lines 37–43
**Apply to:** `test_file_extract.py`, `test_input_wrap.py`
```python
# No context manager — skips lifespan (startup OpenAI access check)
# Allows unit tests to run without a live API key
client = TestClient(app, raise_server_exceptions=True)
```

### Color tokens: CSS variable names
**Source:** `apps/web/app/globals.css` lines 47–60
**Apply to:** All components — never use raw oklch values, always the semantic token name
```typescript
// Correct: use semantic token names
"bg-card", "text-foreground", "text-muted-foreground", "border-border", "bg-primary", "text-primary-foreground"
// Wrong: "bg-[oklch(0.985_0_0)]" or any raw color value
```

### Typography: two weights, four roles
**Source:** `apps/web/.planning/phases/05-buyer-ui-trace-submission/05-UI-SPEC.md` §Typography
**Apply to:** All buyer screen pages and components
```
text-sm       → body (14px, weight-400)   — field values, evidence snippets
text-xs font-semibold → label (12px, 600) — badges, table headers, metadata
text-xl font-semibold → heading (20px, 600) — section headings, panel titles
text-3xl font-semibold → display (28px, 600) — one page title per screen
text-muted-foreground → secondary text
// Never use text-base (16px) — see UI-SPEC §Typography Rules
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `apps/web/lib/sse.ts` | utility | streaming | No client-side SSE consumer exists in the codebase; greenfield `fetch+ReadableStream` pattern |
| `apps/web/lib/session.ts` | utility | — | No session management exists in the codebase |
| `apps/web/contexts/BuyerContext.tsx` | provider | — | No React Context exists in the codebase |
| `apps/web/app/api/traces/[name]/route.ts` | route | request-response | No Next.js Route Handlers exist yet |

For these four files, use the patterns in RESEARCH.md §Architecture Patterns directly — they are grounded in Next.js/React conventions, not codebase-specific patterns.

---

## Metadata

**Analog search scope:** `apps/web/`, `services/ai/api/`, `services/ai/tests/`, `services/ai/schemas/`, `services/ai/prompts/`, `docs/prompts/`, `packages/shared-types/`
**Files scanned:** 14
**Pattern extraction date:** 2026-06-28
