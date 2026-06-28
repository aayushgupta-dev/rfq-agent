# UI/UX Generation — Live Run Artifact

**Prompt:** ui-ux-gen v1
**Model:** gpt-5.4-mini
**Run date:** 2026-06-28

---

## Screen 1: RFQ Overview

### Information Hierarchy
1. **Procurement summary card** at top: scope, submission deadline, expected vendor count.
2. **What vendors must respond to**: the 8 line items, each with a plain-language description and procurement intent.
3. **Commercial expectations and payment terms**: how pricing should be structured, what terms apply, what assumptions must be stated.
4. **Vendor questionnaire**: the exact questions the buyer asked vendors to answer.
5. **Compliance requirements**: regulatory clauses and mandatory checks.
6. **Primary CTA**: **Begin vendor input**.

### Key Components
- **RFQ Summary Card**
  - Purpose: confirm the event scope before any vendor data is processed.
  - Data source: `RFQ.scope_summary`, `RFQ.timeline`, vendor count expectation.
  - Contents:
    - Procurement event name
    - Scope summary
    - Submission deadline
    - Expected number of vendors
- **Line Item Requirements Table**
  - Purpose: show the 8 required workstreams the buyer will compare later.
  - Data source: `RFQ.line_items[]`
  - Columns: line item, description, response expectation
- **Commercial Expectations Panel**
  - Purpose: establish how vendors should price and what commercial assumptions matter.
  - Data source: `RFQ.commercial_expectations`
- **Vendor Questionnaire Panel**
  - Purpose: provide the buyer's exact prompts to vendors.
  - Data source: `RFQ.vendor_questionnaire[]`
- **Compliance Requirements Panel**
  - Purpose: expose mandatory legal/regulatory clauses for the bid.
  - Data source: `RFQ.compliance_requirements[]`
- **Primary Action Bar**
  - Purpose: move the buyer into vendor ingestion.
  - CTA: `Begin vendor input`

### Interactions
- **Expand/collapse sections** for questionnaire and compliance detail.
- **Sticky action bar** with `Begin vendor input`.
- **No editing on this screen** unless RFQ drafting is in scope; this view is confirmation-only.
- **Loading state**: summary card skeleton, line item table skeleton, section placeholders.
- **Error state**: show a blocking retrieval error with retry.
- **Transition**: clicking `Begin vendor input` advances to Screen 2.

### Copy
- Page title: **RFQ Overview**
- Summary card heading: **Procurement summary**
- Summary labels:
  - **Scope**
  - **Submission deadline**
  - **Expected vendors**
- Section heading: **What vendors must respond to**
- Section heading: **Commercial expectations and payment terms**
- Section heading: **Vendor questionnaire**
- Section heading: **Compliance requirements**
- CTA: **Begin vendor input**
- Loading copy: **Generating RFQ view…**
- Error heading: **RFQ could not be loaded**
- Error text: **The RFQ endpoint failed. Review the connection and try again.**
- Retry CTA: **Retry load**

### Empty / Error States
- **No data yet**
  - Copy: **RFQ content has not been loaded yet.**
  - Secondary text: **Generate or retrieve the RFQ to confirm scope before processing vendors.**
- **AI failed**
  - Not applicable as this is buyer-authored RFQ data, but if RFQ generation fails:
  - Copy: **RFQ generation failed.**
  - Secondary text: **The event brief could not be assembled from the source data.**
  - CTA: **Retry generation**
- **Data partially available**
  - Show whatever loaded sections exist.
  - Mark missing sections explicitly: **Not addressed in RFQ source**
- **Network error**
  - Copy: **RFQ could not be loaded from the server.**
  - CTA: **Retry load**

---

## Screen 2: Vendor Upload / Input

### Information Hierarchy
1. **Hero sample load action**: one-click load of the 3 committed messy vendor responses.
2. **Paste input areas**: vendor name + vendor response textarea.
3. **File upload zone**: drag-and-drop for PDF, DOCX, XLSX, PPTX.
4. **Loaded vendors list**: name, source, status, extraction-readiness warning.
5. **Run Extraction CTA**.

### Key Components
- **Sample Load Hero Button**
  - Purpose: fastest path to a realistic, testable dataset.
  - Data source: committed sample bundle.
  - Button text: `Load 3 sample vendors (GlowBite pitch)`
- **Vendor Input Cards**
  - Purpose: let the buyer paste distinct vendor responses and assign names.
  - Data source: buyer-provided text.
  - Fields:
    - Vendor name input
    - Response textarea
- **File Upload Dropzone**
  - Purpose: ingest vendor response documents.
  - Accepts: PDF, DOCX, XLSX, PPTX
  - Copy must clarify supported formats.
- **Loaded Vendors List**
  - Purpose: show what has been ingested and whether it is ready for extraction.
  - Columns: vendor name, source, status, extraction quality flag
  - Status values:
    - `loaded`
    - `text-extracted`
    - `extraction-weak`
- **Extraction Quality Warning**
  - Purpose: surface weak OCR / extraction before the buyer proceeds.
  - Threshold rule: if extracted text is below threshold characters, warn inline.
- **Primary CTA**
  - Purpose: begin AI extraction across all loaded vendors.
  - Button: `Run Extraction`

### Interactions
- **Sample load**
  - Clicking `Load 3 sample vendors (GlowBite pitch)` instantly populates three vendor records.
- **Paste input**
  - Vendor name determines the record label.
  - Each textarea can be individually saved or auto-detected.
- **File upload**
  - Drag-and-drop or browse.
  - On upload, show parsing progress and extracted text preview.
- **Loaded vendor row click**
  - Expands a small preview of source text and extraction status.
- **Run Extraction**
  - Starts SSE streaming for each vendor.
- **Running state**
  - Per-vendor progress indicator:
    - `Queued`
    - `Extracting text`
    - `Extracting fields`
    - `Reviewing evidence`
- **Partially loaded state**
  - Available vendors show normally; missing vendor slots remain open.
- **Empty state**
  - Show guidance, not decoration.

### Copy
- Page title: **Vendor Upload / Input**
- Hero button: **Load 3 sample vendors (GlowBite pitch)**
- Section heading: **Paste vendor responses**
- Field label: **Vendor name**
- Field label: **Vendor response**
- Upload heading: **Upload vendor files**
- Dropzone text: **Drag and drop files here, or browse to upload PDF, DOCX, XLSX, or PPTX**
- Loaded vendors heading: **Loaded vendors**
- Status labels:
  - **Loaded**
  - **Text extracted**
  - **Extraction weak**
- Weak extraction warning: **Text extraction from this file was limited — paste the content directly for best results**
- CTA: **Run Extraction**
- Empty state text: **Load sample vendors or paste vendor proposals above to begin. Extraction runs when you click 'Run Extraction'.**
- Running state text: **Extraction in progress for loaded vendors**

### Empty / Error States
- **No vendors loaded**
  - Show the empty state copy above.
- **Partially loaded**
  - Show loaded vendors; show empty placeholders for remaining entries.
- **All loaded, ready**
  - Enable `Run Extraction`.
- **Running**
  - SSE progress bars per vendor.
- **File parse error**
  - Copy: **This file could not be read.**
  - Secondary text: **Try another format or paste the vendor text directly.**
- **Network error**
  - Copy: **Vendor input could not be processed right now.**
  - CTA: **Retry upload**

---

## Screen 3: Extraction Review

### Information Hierarchy
1. **Vendor selector / tabs** at top.
2. **Top Gaps & Risks panel** directly below selector, always visible.
3. **Category-based extraction detail**: Scope, Pricing, Commercial Terms, Timeline, Compliance, Assumptions, Exclusions, Risks.
4. **Inline evidence snippets** under every field.
5. **Source panel** on evidence click, showing the quote in context.

### Key Components
- **Vendor Tabs**
  - Purpose: switch between vendors without losing context.
  - Data source: `ExtractionResult.vendor_id`
- **Top Gaps & Risks Panel**
  - Purpose: make absence and uncertainty the first thing the buyer sees.
  - Data source: all flagged fields from the selected vendor.
  - Must include:
    - Count summary
    - Every `missing`, `unclear`, `conflicting`, `unsupported` field
- **Category Extraction Sections**
  - Purpose: show full structured extraction by procurement dimension.
  - Data source: `ExtractionResult.fields[]`
- **Field Row**
  - Purpose: render a single fact with traceable evidence.
  - Components:
    - Field name
    - Status badge or normal rendering
    - Value
    - Evidence snippet
    - Reason text where needed
    - Clarification question for missing fields
- **Conflict Comparator**
  - Purpose: show both contradictory values side by side.
  - Data source: conflicting field variants and their snippets
- **Evidence Snippet**
  - Purpose: verbatim source text inline, not hidden.
- **Source Context Drawer**
  - Purpose: show the quoted span highlighted in the source document context.
  - Opens full-width from snippet click.

### Interactions
- **Vendor tab switch**
  - Updates top gaps panel and category sections.
- **Top gaps panel click**
  - Jumps to the relevant field in the category section.
- **Evidence snippet click**
  - Opens source context drawer with highlighted quoted span.
- **Missing field question click**
  - Copies suggested clarification question for buyer use.
- **Loading state**
  - Fields stream in progressively by SSE.
  - Show skeleton rows as they arrive.
- **Partial state**
  - Some vendors complete while others continue streaming.
- **Error state**
  - Show extraction failure banner with retry.

### Copy
- Page title: **Extraction Review**
- Top panel heading: **Top Gaps & Risks**
- Count summary example: **3 fields missing, 2 unclear, 1 conflicting**
- Missing badge: **Not addressed**
  - Helper text: **Vendor did not address this field**
- Unclear badge: **Unclear**
  - Helper text: **Reason for ambiguity shown below**
- Conflicting badge: **Conflicting**
  - Helper text: **Both statements shown side by side**
- Unsupported badge: **Unverified by source**
  - Helper text: **AI generated this value but no source text confirmed it**
- Missing-field inline prompt: **Suggested clarification question**
- Evidence drawer heading: **Source context**
- Evidence drawer label: **Quoted span in context**
- Loading copy: **Reviewing vendor response…**
- Error heading: **Extraction failed**
- Error text: **We could not complete extraction for this vendor. No results are shown until the issue is resolved.**
- Retry CTA: **Retry extraction**

### Absent-State Rendering Rules
- `present`
  - Show value + evidence snippet inline.
- `missing`
  - Badge: amber `Not addressed`
  - Show: **Vendor did not address this field**
  - Include suggested clarification question.
- `unclear`
  - Badge: amber `Unclear`
  - Show vague evidence snippet
  - Show reason: **The source mentions this, but not in a precise enough form to verify.**
- `conflicting`
  - Badge: red `Conflicting`
  - Show both values side by side
  - Show evidence for each value separately
- `unsupported`
  - Badge: red `Unverified by source`
  - Show: **AI generated this value but no source text confirmed it**

### Empty / Error States
- **No extraction started**
  - Copy: **No extraction results yet. Run extraction to review vendor responses.**
- **Loading**
  - Copy: **Extraction results are streaming in.**
- **Partial**
  - Copy: **Some vendors are complete; others are still processing.**
- **Error**
  - Copy: **Extraction failed for this vendor. Review the source file or rerun extraction.**

---

## Screen 4: Vendor Comparison

### Information Hierarchy
1. **Comparability Matrix** hero.
2. **Buyer Attention Points** panel directly below the matrix.
3. **Clarification Questions** panel grouped by vendor, then by dimension.
4. **Data readiness indicator** below matrix.
5. **Per-dimension drill-down** with narrative, vendor detail, evidence references.
6. **Stable vendor order note**.

### Key Components
- **Comparability Matrix**
  - Purpose: show where vendors can be compared, and where they cannot.
  - Data source: `ComparisonResult.matrix`
  - Rows: technical, commercial, scope, timeline, compliance, risk
  - Columns: vendors in stable input order
  - Cell content:
    - Verdict badge
    - One-line reason
- **Comparability Verdict Badge**
  - `comparable` → green
  - `partially_comparable` → amber
  - `not_comparable` → red
- **Buyer Attention Points Panel**
  - Purpose: surface issues requiring buyer action before selection.
  - Data source: `ComparisonResult.attention_points[]`
- **Clarification Questions Panel**
  - Purpose: show buyer-sendable questions, grouped by vendor and dimension.
  - Data source: `ComparisonResult.clarification_questions[]`
- **Data Readiness Row**
  - Purpose: state comparability coverage without implying ranking.
  - Data source: computed readiness counts
- **Dimension Drill-down**
  - Purpose: show narrative and evidence behind a row.
- **Vendor Order Note**
  - Purpose: prevent ranking interpretation.
  - Copy: vendors shown in input order.

### Interactions
- **Matrix cell click**
  - Opens dimension drill-down for that row.
- **Attention point click**
  - Jumps to the triggering field or dimension.
- **Question click**
  - Opens the source field and allows copy to clipboard.
- **Dimension drill-down**
  - Shows full narrative, per-vendor detail, and evidence references.
- **Running state**
  - Dimension-by-dimension SSE progress.
- **No comparison yet**
  - Prompt the buyer to run extraction first.
- **Error state**
  - Show explicit comparison error, not a blank matrix.

### Copy
- Page title: **Comparison results — 3 vendors, 6 dimensions**
- Matrix title: **Comparability Matrix**
- Column note: **Vendors are shown in the order they were provided — this is not a ranking.**
- Cell reason examples:
  - `comparable`: **Enough information to compare directly**
  - `partially_comparable`: **Some fields match, but key details are missing**
  - `not_comparable`: **One or more vendors did not provide enough information for a valid comparison**
- Buyer panel heading: **Buyer Attention Points**
- Questions panel heading: **Clarification Questions**
- Data readiness label: **Data readiness: 4/6 dimensions comparable**
- Tooltip: **Data readiness measures how many dimensions have enough information to compare — it does not indicate which vendor is better.**
- Drill-down heading: **Dimension detail**
- No-run state: **Run extraction first to see comparability across vendors.**
- Running copy: **Comparison is in progress…**
- Error heading: **Comparison could not be completed**
- Error text: **The comparison agent failed. The matrix is not shown until a valid result is available.**

### Empty / Error States
- **No comparison run yet**
  - Copy: **Run extraction first to compare vendors.**
- **Running**
  - Show matrix skeleton with progressive fill.
  - Show per-dimension status updates.
- **Complete**
  - Show full matrix, attention points, and questions.
- **Error**
  - Copy: **Comparison could not be completed.**
  - Secondary text: **Please review vendor extraction results and try again.**

### Absent-State Design in the Matrix and Drill-down
- If a dimension is not comparable, the cell must state why inline, e.g.:
  - **Not comparable: Vendor A omitted pricing structure; Vendor B bundled pricing across all workstreams**
- If partially comparable:
  - **Partially comparable: comparable on scope, unclear on timeline**
- Clarification questions must be shown even when based on missing information.
- If a question assumes unsupported context, show warning text:
  - **This question relies on an unverified assumption.**

---

## Screen 5: Prompt Trace

### Information Hierarchy
1. **Full Trace** section showing one complete pipeline trace by default.
2. **Prompt Pack** section listing all 7 prompts.
3. **Run your own trace** affordance as a secondary CTA.

### Key Components
- **Full Trace Timeline**
  - Purpose: show the end-to-end path from vendor text to final extraction result.
  - Data source: committed trace JSON.
  - Stages:
    - Input excerpt
    - Prompt ID + version
    - AI draft
    - Source verification result
    - Final result
    - Revised by source check diff
- **Input Excerpt Panel**
  - Purpose: show the raw vendor response fragment used in the trace.
- **Prompt Metadata Chip**
  - Purpose: show prompt id and version.
- **AI Draft Panel**
  - Purpose: show raw model output, collapsed by default.
- **Final Result Panel**
  - Purpose: show the code-enforced, source-checked result.
- **Revised by Source Check Diff**
  - Purpose: highlight where code changed the AI draft.
  - Exact story: **Model said `present`, code said `unsupported`**
- **Prompt Pack Cards**
  - Purpose: list all prompts used in the pipeline.
  - Data source: `services/ai/prompts/`
  - Each card includes:
    - prompt id
    - version
    - model tier
    - intent
    - docs link
- **Run Your Own Trace CTA**
  - Purpose: let a user paste a vendor response and watch the pipeline.

### Interactions
- **Expand AI draft**
  - Default collapsed.
- **Expand diff**
  - Shows field-level revision explanation.
- **Prompt card click**
  - Opens docs prompt reference.
- **Run your own trace**
  - Opens an input panel as secondary path.
- **Trace load error**
  - Keep prompt pack visible even if trace fails.

### Copy
- Page title: **Prompt Trace**
- Full trace heading: **Full Trace**
- Stage labels:
  - **Input**
  - **Prompt used**
  - **AI draft**
  - **Source verification**
  - **Final result**
  - **Revised by source check**
- AI draft label: **AI draft**
- Final result label: **Final result after source check**
- Diff heading: **Revised by source check**
- Diff example text: **Model said `present`, code said `unsupported`**
- Prompt pack heading: **Prompt Pack**
- Prompt card fields:
  - **Prompt ID**
  - **Version**
  - **Model tier**
  - **Intent**
  - **Docs**
- Secondary CTA: **Run your own trace**
- Trace load error heading: **Trace could not be loaded**
- Trace load error text: **The committed trace file is unavailable. The prompt pack is still shown below.**

### Empty / Error States
- **No trace loaded**
  - Show a committed trace by default.
- **Trace load error**
  - Keep the Prompt Pack section fully visible.
  - Show a non-blocking error banner above Full Trace.
- **No trace data available for a prompt**
  - Show: **Trace not available**
  - Explain: **This prompt did not produce a committed trace file.**
- **Partial trace**
  - Show available stages and mark missing stages explicitly:
    - **Not captured in trace**

### Absent-State Rules for Trace Content
- `present`
  - Show the trace stage content with source references.
- `missing`
  - Show: **Not captured in trace**
- `unclear`
  - Show the ambiguous output and why it was ambiguous.
- `conflicting`
  - Show both AI draft and source-verified versions side by side.
- `unsupported`
  - Show: **AI draft had no source confirmation**
  - Highlight that the source check removed or revised the claim.
