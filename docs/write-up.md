# Bid Desk — Write-Up

*Generative AI Expert / Applied AI Engineer assignment submission — Aerchain / Agillos*

---

## Problem Statement

A procurement buyer running a competitive marketing-services bid receives vendor proposals in
wildly different formats. One vendor sends a polished PDF with bundled pricing and no per-item
breakdown. Another sends a Word document with contradictory timeline statements. A third responds
with a scope that covers seven of eight requested line items, with vague compliance language and
no commercial terms at all.

The buyer's real job is **sense-making under uncertainty**: which vendor actually addressed the
brief? Where is the information missing or risky? Who is even comparable before we start
evaluating? This is tedious, error-prone work that delays procurement decisions and creates the
conditions for misleading comparisons — comparing a partial proposal against a full one as if they
were equivalent.

Bid Desk automates the sense-making step. It extracts structured facts from raw, messy vendor
text, flags every gap, and compares vendors only where the evidence supports comparison — surfacing
where it does not, and generating the clarification questions the buyer needs to resolve ambiguity.

---

## Assumptions

- **Marketing services RFQ with 8 line items** (strategy & creative, TVC development, TVC
  production, social organic, paid media planning, paid media buying, kids advertising & claims
  compliance, launch program management). The sample RFQ is for a fictional brand "GlowBite."

- **Three deliberately messy vendor responses** are pre-generated and committed as sample data.
  Messiness is deliberate: one vendor bundles pricing, one provides vague compliance language with
  no substantiation, one omits several line items entirely. These stress the extraction and
  comparison agents.

- **Best-effort text extraction** from uploaded files (PDF, DOCX, XLSX, PPTX). The assignment
  brief (§11) does not require production-grade OCR. For maximum fidelity, users should load the
  committed sample responses.

- **Single-buyer session** — no authentication, no multi-user isolation. This is a 5-day prototype.

- **GPT-5.4 model family** (gpt-5.4 for reasoning-heavy work, gpt-5.4-mini for cheap tasks).
  Model access is confirmed at startup.

---

## Prompt Architecture

The Prompt Pack contains 7 versioned prompts, each a first-class source artifact in
`services/ai/prompts/` with YAML frontmatter (`id`, `version`, `intent`, `failure_handling`)
and a Markdown body.

### Prompt layering

```
rfq-gen → produces the RFQ (the evaluation target)
vendor-gen + messy-data-gen → produces ≥3 deliberately messy vendor responses
ui-ux-gen → captured the buyer UI structure as a design artifact
                ↓
extraction → per-vendor structured extraction with evidence
                ↓
clarification → drafts buyer questions for every flagged field
                ↓
comparison → compares ExtractionResult objects across 6 dimensions
```

### Why this structure

Each prompt has a single, narrow job. The extraction prompt does not evaluate vendors; the
comparison prompt does not re-extract facts. This separation keeps each prompt's contract clean
and testable: if extraction returns a fabricated field, the grounding gate catches it in code
before comparison ever sees it.

**rfq-gen.v1:** Generates a realistic procurement event — not a clean template. It includes
contradictory vendor questionnaire items and compliance requirements that stress vendor responses.
The humility instruction ("do not round or simplify budgets") forces realistic commercial terms.

**vendor-gen.v1 + messy-data-gen.v1:** vendor-gen embeds the messy-data-gen taxonomy inline —
8 mess types (bundled pricing, scope gaps, vague timelines, conflicting statements, missing
compliance, unclear assumptions, currency ambiguity, marketing fluff). This produces responses
that genuinely differ in completeness and structure, not just in vendor name.

**extraction.v1:** The reliability-critical prompt. It defines the four flag states
(present/missing/unclear/conflicting), the evidence contract (verbatim quotes, minimum 20 chars/3
words, char offsets set to 0/1 for code-side recomputation), and the per-claim list fields
(compliance_points, assumptions, exclusions, risks). The humility instruction
("prefer missing or unclear over present when uncertain") is the key prompt-design choice that
prevents fabricated confidence. The "CRITICAL" block makes the model/code boundary explicit:
the model assigns one of four states; separate code runs the grounding gate.

**comparison.v1:** Establishes comparability first, ranking never. The prompt defines six
dimensions (technical, commercial, scope, timeline, compliance, risk) and three verdicts
(comparable/partially/not_comparable). It explicitly forbids: computing numeric scores, inventing
pricing, filling gaps with assumptions. The "NOT" list in the system message is the active
hallucination guard for the comparison step.

**clarification.v1:** Given the flagged fields from an ExtractionResult or ComparisonResult,
drafts actionable questions the buyer can send to the vendor. One question per field, anchored to
the field name and the ambiguous passage — not generic follow-up questions.

**ui-ux-gen.v1:** Run once to produce a captured UI/UX design specification artifact. The output
informed the five-screen layout, information hierarchy, and copywriting contract. The React
components are hand-built; the prompt + captured artifact are the deliverable for the 10%
UI/UX-generation rubric item.

---

## Product Thinking

### Evidence over assertion

Every extracted fact is accompanied by a verbatim evidence snippet from the vendor's response.
The evidence is validated in code (the grounding gate) — if the snippet cannot be located in the
source text, the field is downgraded to `unsupported`. The model is never trusted to certify its
own evidence.

### Absence is first-class

`missing`, `unclear`, `conflicting`, and `unsupported` are explicit states that render
prominently in the UI with color-coded badges. They are never silently filled or hidden to make
the UI look tidy. The extraction screen's top panel lists every flagged field first — buyer-first
information hierarchy. A vendor with twelve missing fields looks different from one with two,
and the buyer sees exactly why.

### Comparability before ranking

The comparison agent outputs three verdicts (comparable/partially/not_comparable) per dimension
per vendor. A comparability clamp in code sets a ceiling: if a vendor has `missing` fields on a
dimension, the code ceiling caps the verdict at `not_comparable` regardless of what the model
proposed. The Trace screen's "Code vs. Model" section shows every clamp where the model proposed
`comparable` and the code overruled it. No numeric scoring, no leaderboard — the buyer sees a
data-readiness indicator and clarification questions.

### What assignment §24 anti-patterns we avoided and why

- **No hardcoded outputs:** Extraction and comparison run the live OpenAI pipeline on demand.
  Committed trace files are pre-captured for the Prompt Trace screen only — clearly labelled
  as fixture data.
- **No static dashboard:** Every field is extracted from actual vendor text; the comparison
  matrix reflects actual extractions, not pre-populated cells.
- **No generic prompts:** Each prompt has a narrow contract, specific output schema, and
  explicit failure handling (what to do when evidence is absent or ambiguous).
- **No unrealistically clean test data:** The three sample vendors were generated with
  deliberate mess — bundled pricing, partial scope, vague compliance, and contradictory timelines.
- **No unsupported AI claims:** Every comparison verdict is grounded in ExtractionResult fields;
  the clamp ensures the model cannot claim comparability where evidence is absent.
- **No misleading comparisons:** Non-comparable vendors are flagged explicitly; the "not a
  ranking or score" affordance is visible on the comparison screen.
- **No UI polish without strong AI behavior:** The most-designed surfaces are evidence snippets,
  flag badges, and the comparability matrix — places where UI design makes AI behavior legible.

---

## Extraction Approach

The extraction agent (LangGraph) takes a `VendorResponse` (raw text + source ID) and the RFQ
as input. It calls GPT-5.4 via the OpenAI structured-output path with the `ExtractionResult`
pydantic schema, which enforces the `Field[T]` envelope on every extracted value.

The grounding gate runs in Python code after the model returns:

1. Walk every `Field[T]` in the result tree.
2. For each field with status `present`, `unclear`, or `conflicting`: locate the evidence
   snippet in the source text. If not found (fuzzy threshold 90%), downgrade to `unsupported`.
3. Recompute `char_start` / `char_end` offsets from the located position — model-supplied
   offsets are discarded (they are placeholder values by design in the prompt).
4. Return the grounded result.

The SSE endpoint streams status events ("Aligning to RFQ… Extracting fields… Grounding evidence…")
so the buyer sees live progress rather than a blank loading screen.

---

## Comparison Approach

The comparison agent receives a list of `ExtractionResult` objects and the RFQ. It calls GPT-5.4
to produce verdicts (comparable/partially/not_comparable) per vendor per dimension, plus
narratives and clarification questions.

The comparability clamp in Python runs after the model returns:

1. For each vendor × dimension, compute a ceiling from the vendor's `FlagStatus` values on
   relevant fields.
2. If the model proposed a better verdict than the ceiling allows, clamp it down.
3. Record every clamp in the trace as a `ClampEntry`.

This means the model's comparability claims are always code-verified — the model cannot assert
`comparable` where the evidence does not support it.

---

## UI/UX Decisions

Five buyer screens via Next.js App Router under `app/(buyer)/`:

1. **RFQ Overview** — committed `data/rfq.json` renders instantly; "Regenerate RFQ" proves live
   generation without stalling the demo's opening screen.
2. **Vendor Input** — one-click sample load (hero path for demo reliability), paste, and
   best-effort file upload.
3. **Extraction Review** — gaps & risks panel always visible at top; evidence snippets inline
   under each field; collapsible drill-down to source passage.
4. **Comparison** — comparability matrix first; clarifications panel always visible; stable vendor
   order (no sort); explicit "not a ranking" labelling.
5. **Prompt Trace** — pipeline timeline (4 stages), amber-highlighted clamp diff, full raw output
   in a scroll area, browsable Prompt Pack list.

Session caching (sessionStorage) means re-visiting a screen is instant — no re-run.

---

## Limitations

- **Best-effort text extraction** — PDF/DOCX/XLSX/PPTX parsing is library-based; complex layouts
  or scanned PDFs will produce degraded text. Paste is the most reliable input path.
- **Single-buyer session** — no server-side state persistence. Refreshing the page clears
  in-flight results.
- **Demo cold-start** — Render free instances spin down after inactivity. Warm the instance
  before recording by hitting any endpoint (e.g. `GET /data/rfq`).
- **GPT-5.4 family only** — switching to a cheaper model without re-tuning the extraction and
  comparison prompts may produce lower-quality extractions.

---

## What's Next

- **Stateful clarification loop** — buyer submits a clarification question; vendor responds;
  re-extraction updates the comparison. The `clarification.v1` prompt already produces
  question drafts; the loop infrastructure is the gap.
- **Production OCR** — layout-aware document parsing (e.g. Azure Document Intelligence) for
  complex PDFs and spreadsheets with merged cells.
- **Multi-buyer sessions** — lightweight session store (Redis or similar) to support concurrent
  procurement events without page-refresh data loss.
