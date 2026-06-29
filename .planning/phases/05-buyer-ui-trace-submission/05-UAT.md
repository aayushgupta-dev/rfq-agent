---
status: diagnosed
phase: 05-buyer-ui-trace-submission
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-05-SUMMARY.md, 05-06-SUMMARY.md, 05-07-SUMMARY.md, 05-08-SUMMARY.md, 05-09-SUMMARY.md]
started: 2026-06-29T04:20:54Z
updated: 2026-06-29T05:08:00Z
---

## Current Test

[testing complete — major gap (test 8) fixed & verified via 05-10; see Gaps]

## Tests

### 1. Cold Start Smoke Test
expected: AI service /health returns 200 (boot-time verify_access gate for gpt-5.4/mini passed); web app serves at :3000 with no runtime errors. Primary static data (rfq.json, sample vendors, committed traces) loads.
result: pass

### 2. RFQ Overview loads (static, structured)
expected: /rfq loads instantly (static rfq.json, no live call). Shows event name, dates, summary card listing 8 line items, full structured body grouped Scope → Timelines → Line Items → Commercial Expectations → Vendor Questionnaire → Compliance. "Regenerate RFQ" button visible top-right.
result: pass
note: All 8 line items + all sections render correctly. Cosmetic: currency uses Indian digit grouping ("$16,15,000", "$1,40,000") in a USD/US-market RFQ — should be "$1,615,000". Logged as cosmetic gap.

### 3. Regenerate RFQ live (dynamic, SSE)
expected: Click "Regenerate RFQ" → summary panel shows skeleton rows → fresh LLM-generated RFQ replaces it. No blank page.
result: pass
note: Skeleton shown, content refreshed, button re-enabled, no console errors. Took ~2+ min (large reasoning generation) — slow for a live demo. Logged as minor performance gap.

### 4. Vendor Input → load sample vendor
expected: On /input, clicking "Load Sample" navigates to /extraction with that vendor extracted.
result: pass
note: Load Sample runs LIVE extraction (POST /extract/vendor, SSE) — dynamic, not hardcoded (good). The 2 ERR_ABORTED POSTs are React StrictMode dev-only double-effect aborts (one POST succeeded 200); not a prod bug.

### 5. Vendor Input → paste raw text → live extraction with streaming
expected: Paste vendor name + messy response + Submit → live extraction streams → navigates to /extraction with populated fields + evidence.
result: pass
note: Pasted "Cobalt Creative Co" → new tab appeared → extraction streamed → populated with 14 flagged issues + grounded evidence. Streaming flow works.

### 6. Extraction Review — fields + inline evidence + Gaps & Risks
expected: /extraction vendor tab shows "Gaps & Risks — N issue(s)" panel listing flagged fields. Below, 8 category cards (Scope, Pricing, Commercial Terms, Timeline, Compliance, Assumptions, Exclusions, Risks); each field row shows label | flag badge | value | inline "Source:" evidence snippet.
result: pass
note: Meridian → "Gaps & Risks — 6 issue(s)" (Total price Missing, 4 pricing Unclear matching bundled-pricing messiness, TVC scope Unsupported), all 8 categories, flag badges, inline evidence + "✓ Grounded — verbatim from vendor response" code-enforced markers.

### 7. Evidence drill-down — cited span highlighted
expected: Expanding a field's evidence reveals the full source passage with the cited span highlighted; copy button available.
result: issue
reported: "Evidence is always shown inline (verbatim snippet + 'Grounded' marker) with no click-to-expand drill-down; clicking the snippet does nothing. No full-source-passage view with highlighted cited span and no copy button on extraction evidence (UI-SPEC described these)."
severity: minor

### 8. Absence-first — missing / unclear / conflicting surfaced, no fabrication
expected: Missing → "—" + "No verified source". Unclear → amber badge with exact vague text. Conflicting → both contradictory values surfaced and flagged conflicting (no value silently chosen). All listed in Gaps panel.
result: issue
reported: "Missing/Unclear/Unsupported work well (Meridian: Total price Missing → '—' + 'No verified source'; Cobalt: Missing×24, Unclear×4, Present×11). BUT a deliberate CONFLICT was NOT flagged: Cobalt response says 'all-in program fee USD 1.2M' AND 'a total of $950,000, fully inclusive' — extraction picked USD 1.2M, marked it 'Present', and never surfaced the $950,000 contradiction. Conflicting-value detection missed a clear contradiction; AI presented one number as definitive."
severity: major

### 9. Comparison — comparability matrix (code-determined, stable order)
expected: /comparison shows vendor-by-dimension matrix (vendors as columns in stable input order; 6 dimensions as rows). Each cell = comparability badge. Caption: "Comparability determined in code from evidence — not a model verdict".
result: pass
note: Matrix = Dimension × {Meridian, Cobalt} (stable order). 6 dimensions (Technical, Commercial, Scope, Timeline, Compliance, Risk) with Comparable/Partially/Not Comparable badges. Caption "Comparability determined in code from evidence — not a model verdict" present.

### 10. Comparison — Needs Attention + clarifications + readiness-not-a-rank
expected: "Needs Attention — N item(s)" card lists attention points + generated clarification questions. Data readiness shown as comparability count, not a sorted score/rank.
result: pass
note: "Needs Attention — 5 item(s)"; grounded, specific clarification questions per vendor; "Data readiness: 2/6 dimensions comparable; blocked on technical, commercial, scope, timeline" — framed as readiness not a rank, vendors in stable order. Minor: clarification questions reference line items by zero-based index ("line item 0/1/2") instead of name — less buyer-friendly.

### 11. Comparison — line-item offer table with flags
expected: "Offer Details"/line-item table (line items as rows, vendors as columns); each cell shows pricing value + flag badge.
result: pass
note: "Show line-item offers (8 items)" expander → table Line Item × {Meridian, Cobalt}; cells show value + flag (e.g. Strategy & Creative: Meridian "— Unclear", Cobalt "$120,000 Present"; TVC Production: Meridian "USD 488,500 Present", Cobalt "— Missing"). Minor cosmetic: some cells render leftover markdown pipe fragments ("| Total TVC Production | USD 488,500 |").

### 12. Prompt Trace — pipeline + code-overruled-model diff
expected: /trace shows pipeline Input → Prompt (id+version) → Raw model output (monospace, scrollable) → Grounded/clamped final, with code-overruled-model rows highlighted.
result: pass
note: 6 trace tabs (Comparison 1/2, Vendor Thorough/Cheap/Fluff, Adversarial). Comparison 1: raw output model_proposed "comparable" for all + "...before code clamp" narratives; 7 amber-highlighted elements mark code-overruled verdicts. "Copy raw output" button present. Adversarial extraction fixture shows "GROUNDED/CLAMPED FINAL — 0 field(s) downgraded".

### 13. Prompt Pack — prompts listed
expected: On /trace, a Prompt Pack list shows the prompts, each with id, version, one-line intent, link to docs.
result: pass
note: 7 prompts listed with intents — rfq-gen, vendor-gen, messy-data-gen, ui-ux-gen, extraction, comparison, clarification. "View prompt in Prompt Pack ↓" links present.

### 14. Stage rail navigation + empty states
expected: Left rail shows 5 items; clicking navigates; active item highlighted. /extraction with no vendor shows guidance + link to /input. /comparison with insufficient vendors shows guidance.
result: pass
note: Rail = 5 items; active link has aria-current="page" + bg-secondary highlight. /comparison empty: "Run extraction on at least one vendor before comparing. Go to Extraction". /extraction empty: "Select or load a vendor on the Input screen to begin extraction."

### 15. Responsive layout (mobile)
expected: At <768px, stage rail hidden + hamburger opens drawer; main content full-width; no horizontal body overflow.
result: pass
note: At 375px: rail hidden (width 0), "Open menu" hamburger opens a drawer with all 5 nav links, no horizontal body overflow (scrollWidth == viewport 375).

## Summary

total: 15
passed: 13
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "A contradiction in a vendor response (two different totals: USD 1.2M vs $950,000) is flagged 'conflicting' with both values surfaced, never silently resolved to one number."
  status: failed
  reason: "User reported: extraction picked USD 1.2M, marked total price 'Present', and never surfaced the explicit '$950,000, fully inclusive' contradiction. No 'conflicting' flag produced for a clear contradiction."
  severity: major
  test: 8
  root_cause: "Same-field 'conflicting' is 100% prompt-driven model judgment; the grounding gate only DOWNGRADES (present/unclear/conflicting → unsupported), never upgrades present → conflicting (correct by §8 — code must not invent the dropped claim). The model missed it under two prompt pressures: total_price is framed as a single decimal ('extract it as a decimal number', extraction.v1.md:128-129), and the only conflicting few-shot is a TIMELINE narrative — there is no numeric/price conflict example. Systemic: no committed sample or test feeds a same-field total contradiction and asserts conflicting."
  artifacts:
    - path: "services/ai/prompts/extraction.v1.md"
      issue: "Lines 128-129 bias total_price to a single decimal; conflicting guidance (54-57) + only few-shot (241-275) is timeline-only — no price-conflict anchor."
    - path: "services/ai/grounding/gate.py"
      issue: "ground_field (236-317) is one-directional; cannot detect/upgrade a contradiction (by design)."
    - path: "data/vendor_fluff.json / data/vendor_thorough.json"
      issue: "No committed same-field total_price contradiction; conflicting path behaviorally untested."
  missing:
    - "In extraction.v1.md total_price bullet: if >1 distinct grand-total is stated anywhere, return conflicting with one values[] entry per total — never pick one."
    - "Add a price/numeric conflicting few-shot beside the timeline one."
    - "Add a same-field total_price contradiction to a committed sample + an extraction-agent test asserting conflicting (behavioral coverage)."
  debug_session: ".planning/debug/conflicting-not-flagged.md"
  resolution: "FIXED & VERIFIED via plan 05-10 (commits d273376, 1d26bde, e58ef44). Prompt-side fix only (extraction.v1.md total_price conflict branch + Example 5 price few-shot); gate.py untouched (§8). Verified: (1) live test test_total_price_conflict_live passed against real gpt-5.4 — model emits total_price=conflicting with both 1.2M and 950k in values[]; (2) non-live suite 149 passed, no regression; (3) END-TO-END buyer UI — loaded vendor_fluff, /extraction now shows 'Gaps & Risks — Total price → Conflicting' with two contradictory totals surfaced + evidence (screenshot docs/qa/uat-evidence/05-10-total-price-conflicting.png). Note: with full fluff (4 total figures) the model surfaced the indicative-vs-envelope range pair rather than the injected 1.2M/950k pair — both are genuine contradictions; the in-process live test confirms the injected pair specifically. Core promise holds: contradictory totals flagged conflicting, both surfaced, none silently chosen."

- truth: "Extraction evidence offers a drill-down to the full source passage with the cited span highlighted (per UI-SPEC D-07)."
  status: failed
  reason: "User reported: evidence is always shown inline (verbatim + grounded marker) but there is no click-to-expand drill-down, no full-passage view with highlighted span."
  severity: minor
  test: 7
  root_cause: "Never-built feature (not a regression). evidence-snippet.tsx has 3 branches and never reads char_start/char_end; FieldRow (extraction/page.tsx:68-101) discards offsets+source_id past .snippet. UI-SPEC D-07 (05-UI-SPEC.md:99,142,234,243) specced a Collapsible drill-down with the cited span underlined in accent color. (Copy button on extraction was a UAT embellishment — spec only requires copy on the Trace screen.) All data needed is already client-side: Evidence offsets survive normalization, and VendorResponse.raw_text (full source) is in BuyerContext."
  artifacts:
    - path: "apps/web/components/evidence-snippet.tsx"
      issue: "3 branches; no Collapsible, no offset usage, no highlighted span."
    - path: "apps/web/app/(buyer)/extraction/page.tsx"
      issue: "FieldRow (68-101) passes only snippet+value to EvidenceSnippet; discards offsets/source_id."
  missing:
    - "OPTIONAL (~30 lines, no backend): pass full Evidence + active vendor raw_text into EvidenceSnippet; add a Collapsible 4th branch rendering raw_text.slice(start-120,start) + <span underline accent>slice(start,end)</span> + slice(end,end+120); guard with raw_text.slice(start,end)===snippet fallback. Reuse trace-tabs.tsx CopyButton (174-190)."
  debug_session: ""

- truth: "Currency amounts render with standard thousands grouping appropriate to a USD/US-market RFQ (e.g. $1,615,000)."
  status: failed
  reason: "RFQ Overview renders Indian lakh-style digit grouping ('$16,15,000', '$1,40,000') for a USD marketing RFQ. Cosmetic but reads as a formatting bug to a buyer."
  severity: cosmetic
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Live RFQ regeneration completes promptly enough for a live demo."
  status: failed
  reason: "Regenerate RFQ took ~2+ minutes (large reasoning generation). Functionally correct (skeleton, no blank page, no error) but slow for a ≤5-min demo; warming/streaming or a smaller scope would help."
  severity: minor
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
