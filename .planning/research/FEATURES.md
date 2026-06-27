# Feature Research

**Domain:** Prompt-driven procurement RFQ extraction + vendor-comparison AI prototype (Bid Desk) — 5-day assignment graded on a §22 rubric (prompts 30% · data gen 20% · extraction 20% · comparison 15% · UI 10% · demo/docs 5%)
**Researched:** 2026-06-27
**Confidence:** HIGH (table-stakes derived directly from the assignment brief §4–§24, which is the source-of-truth rubric; differentiators are §21 verbatim; procurement-convention context verified across multiple industry sources — see Sources)

---

## Orientation: How To Read This File

This is an **assignment prototype**, so "table stakes" is unusually well-defined: it is what the brief *requires* and what the rubric *grades*. Three feature buckets:

- **Table stakes** = rubric-required or buyer-essential. Missing one = points lost. Each is tied to its rubric area below.
- **Differentiators** = assignment §21 "Optional but Valuable" + buyer-product-thinking touches that lift the 15% comparison and 10% UI scores. Strengthen the submission; do not chase all of them.
- **Anti-features** = assignment §24 "What to Avoid" — deliberately NOT built. These are graded *against* you if present.

The features are organized along the three axes the question asked: **(A) the 5 buyer screens**, **(B) the AI agents/prompts**, **(C) the reliability layer**. A buyer-information-hierarchy section ("what to see first") and a procurement-conventions section (bid tabulation, should-cost, normalization-vs-surfacing) follow, because they directly shape the §14/§15 product-thinking grade.

---

## Procurement Domain Conventions (context that shapes the features)

These conventions, verified across procurement-industry sources, are the real-world backdrop. They explain *why* the assignment's principles are the right ones — and where the assignment deliberately diverges.

| Convention | What practitioners do | How it maps to Bid Desk |
|---|---|---|
| **Bid tabulation / bid tab** | A side-by-side comparison sheet lining up every vendor's response against the RFQ line items; deviations from RFQ terms are flagged and clarifications sought. | This *is* the Vendor Comparison screen (Screen 4). The "deviations flagged, clarifications sought" pattern maps 1:1 to our flags + clarification questions. |
| **Responsive vs. non-responsive bid** | A bid omitting critical information or not conforming to essential terms is "non-responsive" and set aside; a bid with clerical gaps is merely "incomplete" and can be cured via clarification. | Maps directly to **comparability-before-ranking**: some vendors aren't comparable yet (incomplete → clarify) vs. fundamentally non-responsive (flag, don't score). |
| **Clarification / cure letters** | Buyers send *written* clarification questions enumerating each specific deficiency; clarification confirms intent, it does not let a vendor improve their bid. | Maps to our **clarification-question generation** — one targeted question per gap/conflict, grounded in the actual missing field. |
| **Normalization for like-for-like** | Practitioners normalize units, currency, Incoterms, bundling so bids compare apples-to-apples; "apples-to-oranges masks real differences." | **Assignment §24 explicitly warns against heavy normalization.** Bid Desk's stance: *surface* the differences (different pricing bases, bundled vs. itemized, currency unstated) and flag non-comparability, rather than silently coercing everything to one baseline. We do *light* alignment (line up to RFQ's 8 items) but never invent a normalized number. This tension is a deliberate product decision and a strong write-up talking point. |
| **Should-cost / TCO** | Buyers estimate what a thing *should* cost (materials, labor, overhead) and weigh total cost of ownership, not just sticker price. | **Out of scope as a quantitative engine** (would require fabricated baselines = hallucination risk). Allowed only as a *qualitative* "buyer attention point" if grounded (e.g., "Vendor C's paid-media buying fee is stated as a % with no cap — flag for should-cost review"). Never compute a fake should-cost number. |
| **Weighted scoring models** (CBA, MCDA, TCO, BVP) | Formal evaluation assigns weights to price/quality/timeline/compliance and ranks. | **Deliberately downplayed.** The assignment rewards *comparability and sense-making*, and §24 warns against "misleading comparisons." A confident numeric score over messy/missing data *is* misleading. We may show a qualitative readiness/comparability signal, not a precision score. |
| **"Cheapest-wins is the #1 mistake"** | Choosing lowest price without checking scope/quality/risk causes downstream failure. | Reinforces buyer-first hierarchy: lead with risk/gaps/comparability, *not* a price leaderboard. |

**Net takeaway for product design:** real procurement already *is* "surface differences + clarify + establish responsiveness before scoring." The assignment's principles aren't contrarian — they are the mature procurement practice, minus the heavy normalization the brief tells us to skip. Build to the convention; lean into surfacing over normalizing.

---

## Buyer Information Hierarchy — What To See FIRST (rubric §14, weight 15% + 10%)

The brief asks explicitly (§14): "What the buyer should see first." This ordering is itself a graded product decision. Recommended hierarchy, most-prominent first:

1. **Comparability verdict** — "3 vendors; 2 comparable on commercials, 1 not yet comparable (pricing basis unstated)." The buyer's first question is *can I even compare these?*
2. **Risks & red flags** — conflicting statements, weak/absent compliance (esp. kids-advertising claims compliance — a legal risk line item), unsupported claims.
3. **Gaps / missing info** — what each vendor failed to provide against the RFQ's 8 line items + questionnaire.
4. **Clarification questions** — the buyer's actionable next step (the "cure letter" equivalent), one per gap/conflict.
5. **Side-by-side differences** — where comparable vendors actually differ (scope coverage, timeline, commercial completeness).
6. **(Drill-down) Full extraction + evidence snippets** — the supporting detail lives one click down, not on the front page.

Anti-pattern to avoid here: opening with a price leaderboard or an aggregate score. That violates §24 ("misleading comparisons") and the cheapest-wins fallacy. Lead with *sense-making*, push raw scoring/detail to drill-down.

---

## Feature Landscape

### Table Stakes (Rubric-Required / Buyer-Essential)

#### Axis A — The Five Buyer Screens (§6) — primarily serves UI/UX 10%, with comparison 15%

| Feature | Why Expected (rubric tie) | Complexity | Notes |
|---------|---------------------------|------------|-------|
| **Screen 1 — RFQ Overview** | §6.1 required. Shows scope, timelines, 8 item requests, commercial expectations, questionnaire, compliance. Sets what vendors must answer. | LOW | Mostly render of generated RFQ object. Make the 8 line items + compliance (kids-advertising) legible — they're the spine everything else lines up against. |
| **Screen 2 — Vendor Upload / Input** | §6.2 + §11 required. Paste or upload (PDF/Word/Excel/PPT/text/MD/JSON); output generated *dynamically*, never hardcoded. | MEDIUM | Best-effort text extraction only (§11 — full OCR not required). Risk: a hardcoded-looking demo loses the "dynamic processing" credit. Must visibly run the agent on arbitrary input. |
| **Screen 3 — Extraction Review** | §6.3 + §12 required. Per-vendor extracted fields; highlights important fields, missing/unclear/conflicting data, risks, **evidence snippets**. | MEDIUM-HIGH | This is where the 20% extraction grade is *shown*. Every fact must display its evidence snippet; flags must be visually distinct (not buried). |
| **Screen 4 — Vendor Comparison** | §6.4 + §13 required. Side-by-side across technical, commercial, scope, timeline, compliance, risk; shows who's comparable, where they differ, what needs review. | HIGH | The bid-tab. Carries the 15% comparison grade. Comparability-before-ranking is the headline. |
| **Screen 5 — Prompt Trace / Prompt Pack view** | §6.5 marked *optional* in §6 but §16 makes ≥1 trace *required* (can live in README/docs). | LOW-MEDIUM | Cheap to do in-app and lifts the 30% prompt grade + 5% demo grade. Strongly recommended as in-app even though technically the trace can be a doc. |

#### Axis B — The AI Agents / Prompt Pack (§7, §8, §12, §13, §15) — serves prompts 30%, data gen 20%, extraction 20%, comparison 15%

| Feature | Why Expected (rubric tie) | Complexity | Notes |
|---------|---------------------------|------------|-------|
| **RFQ Generation agent** | §7.1, §8. One realistic marketing-services RFQ, 8 line items, all sections. Feeds data-gen 20%. | MEDIUM | Must "feel like a real procurement event, not a clean sample" (§8). Prompt goes in Prompt Pack. |
| **Vendor Response Generation agent** | §7.2, §8. ≥3 vendor responses, varying completeness/clarity/commercial detail. Data-gen 20%. | MEDIUM | No UI screen needed (§7.2), but prompt is *required* in Prompt Pack. |
| **Messy / complex-data generation** | §9 + §15.3. Inject missing pricing, unclear tax/currency, partial scope, vague timelines, weak compliance, bundled pricing, marketing fluff, contradictions. | MEDIUM | This is what makes extraction *worth testing*. §24 forbids "unrealistically clean test data." The messiness is graded. Treat as its own prompt (or a controlled variation layer over vendor-gen). |
| **UI/UX Generation prompt(s)** | §7.3, §10, §15.4. Prompt-driven dashboard structure, comparison views, risk/evidence/clarification sections, UX copy. | LOW-MEDIUM | The *prompt* and its output artifacts are the deliverable (§20.4), captured in docs/prompts. Reflects buyer product thinking, not visual polish. |
| **Extraction agent** | §7.4, §12. Structured per-vendor extraction (scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, risks) + evidence + flags. Never fills missing info. | HIGH | 20% of grade. Must be structured (pydantic/JSON-schema), buyer-readable, grounded. The reliability core. |
| **Comparison agent** | §7.5, §13. Compares using extracted facts + evidence; comparability first; buyer attention points + clarification needs; never misleads. | HIGH | 15% of grade. Consumes extraction output. Must establish comparability before any difference/ranking view. |
| **Clarification / exception-handling prompt** | §15.7 *required* in Prompt Pack. Generates targeted clarification questions for missing/unclear/conflicting fields. | MEDIUM | Often under-built — it's an explicit Prompt Pack item (part of the 30%). One grounded question per gap. Maps to the procurement "cure letter" convention. |
| **The Prompt Pack itself** | §15 — "Prompt writing is the core." All 7 prompt categories, each documented (what / why / how it handles unreliable info). | MEDIUM | 30% — the single largest rubric area. Versioned, first-class source (CLAUDE.md §7). Per-prompt rationale doc is required, not optional. |
| **≥1 Prompt Trace** | §16 required. input → prompt → model output → final structured/displayed output. | LOW | Easy points toward 30% + 5%. Capture at least one extraction or comparison trace end-to-end. |

#### Axis C — The Reliability Layer (§8 brief, §12, §13, §17) — serves extraction 20% + comparison 15% (and underpins the whole 70% AI grade)

| Feature | Why Expected (rubric tie) | Complexity | Notes |
|---------|---------------------------|------------|-------|
| **Evidence snippets on every fact** | §12, §17, §23. Each extracted fact carries a source span from the vendor response. | MEDIUM | "Evidence over assertion" is the product's core value. Untraceable fact = not shown as fact. |
| **Code-enforced grounding** | CLAUDE.md §8, PROJECT.md. Validate each evidence span actually exists in source text — not the model's word for it. | MEDIUM-HIGH | The headline reliability differentiator and a strong write-up point. Never trust an LLM "verified" flag (CLAUDE.md §2). Implement as a post-LLM code check that rejects/flags spans not found in source. |
| **Missing / unclear / conflicting / unsupported flags** | §12, §17, §23. Explicit, prominent states — never silently filled or hidden. | MEDIUM | "Absence is first-class." Four distinct flag types, each visually distinct. §24 forbids "ignoring missing or contradictory information." |
| **Comparability-before-ranking** | §13, §17. Tell the buyer who is *even comparable* before differences/scoring. Flag "not yet comparable — needs clarification." | MEDIUM-HIGH | The product-thinking centerpiece (15%). Maps to procurement's responsive/non-responsive distinction. |
| **Clarification questions surfaced to buyer** | §13, §17, §20.5. Buyer attention points + clarification needs as an output, not buried. | MEDIUM | The actionable next step. Deliverable §20.5 explicitly lists "clarification questions." |
| **No hallucinated commercial/technical claims** | §17, §23, §24. The non-negotiable. When info is missing/conflicting → flag + propose clarification, never fabricate. | (enforced via the above) | This is *the* thing being graded across all 70% AI weight. It is achieved by the four features above working together, not a separate feature. |

---

### Differentiators (Optional but Valuable — §21 + buyer product-thinking lifts)

| Feature | Value Proposition (rubric tie) | Complexity | Notes |
|---------|-------------------------------|------------|-------|
| **Architecture diagram** | §21. Lifts demo/docs 5% + signals system thinking. | LOW | Cheap; goes in docs/architecture. High ROI. |
| **Prompt versioning + prompt evaluation notes** | §21 + reinforces the 30% prompt grade — shows iterative prompt craft. | LOW-MEDIUM | CLAUDE.md §7 already mandates versioned prompts; documenting the *evaluation* of them is the §21 bonus. |
| **Prompt failure examples + the fix** | §21. Demonstrates real prompt engineering maturity (30%). | LOW-MEDIUM | "Here's a prompt that hallucinated, here's how we constrained it." Powerful in the write-up + demo. |
| **More vendor responses / more document formats** | §21. Stress-tests extraction; more impressive demo. | LOW each | Diminishing returns past ~3–4 vendors; breadth of *messiness* matters more than count. |
| **OCR support** | §21. Handles scanned PDFs. | HIGH | Explicitly *not required* (§11). Low ROI for 5 days; skip unless time is abundant. |
| **Human review workflow** | §21. Buyer can accept/override a flag or mark a clarification as sent. | MEDIUM | Strong product-thinking signal (15%) but stateful → tempts scope creep (DB). Keep in-memory/session if attempted. |
| **Structured schemas** | §21 — and CLAUDE.md already mandates pydantic schemas as the contract. | (already core) | We get this "for free" via the architecture; document it to claim the §21 credit. |
| **Feedback loop design** | §21. Describe (don't necessarily build) how buyer corrections would refine extraction. | LOW (as design) | A write-up "what's next" item; cheap credit without building it. |
| **Better UI polish** | §21 — but only 10% weight, and §24 warns polish without AI behavior is penalized. | MEDIUM | Polish *after* AI behavior is solid. Risk-laden — see anti-features. |
| **Comparability matrix / readiness signal (not a score)** | Product-thinking lift (15%): a per-dimension "comparable / not yet / non-responsive" grid instead of a numeric leaderboard. | MEDIUM | The defensible alternative to weighted scoring — surfaces readiness without misleading precision. |
| **"Same RFQ line item, different vendor framing" alignment view** | Product-thinking lift (15%): line up each of the 8 items across vendors so bundled/partial/missing scope is obvious. | MEDIUM | Light alignment to the RFQ spine — *not* numeric normalization. The honest version of a bid tab. |

---

### Anti-Features (Assignment §24 — Deliberately NOT Built)

| Feature | Why It Seems Appealing | Why Problematic (graded against you) | Alternative |
|---------|------------------------|--------------------------------------|-------------|
| **Hardcoded outputs / canned demo** | Easiest path to a "working" demo. | §24 #1 + §11 require *dynamic* processing. A hardcoded demo fails the core expectation and is obvious to evaluators. | Run agents live on arbitrary pasted/uploaded input; commit samples as *inputs*, not as faked outputs. |
| **Static dashboard** | Looks complete. | §24 #2 — defeats the "active AI processing" purpose. | Stream live agent output over SSE; show the AI working. |
| **Generic prompts** | Faster to write. | §24 #3 — prompts are 30% of the grade; generic = low score. | Domain-specific, role-rich, failure-handling prompts with documented rationale. |
| **Unrealistically clean test data** | Easier to extract from. | §24 #4 + §9 — clean data doesn't test extraction; defeats the 20% data-gen purpose. | Inject the §9 messiness deliberately (missing pricing, currency/tax ambiguity, bundling, contradictions, vague timelines). |
| **Unsupported AI claims** | Makes the UI look confident/complete. | §24 #5 + §17 — the single biggest reliability failure. | Evidence on every fact; flag absence; code-enforced grounding. |
| **Heavy normalization** | Procurement convention says normalize for like-for-like. | §24 #6 — explicitly warned against; risks fabricating normalized numbers (= hallucination). | *Surface* differences, light-align to the 8 RFQ items, flag non-comparability. Never coerce to a fabricated baseline. |
| **Ignoring missing/contradictory info** | Tidier UI. | §24 #7 — directly opposite to "absence is first-class." | Make missing/unclear/conflicting/unsupported prominent, first-class states. |
| **Misleading vendor comparisons (e.g., confident numeric score over messy data)** | A leaderboard feels decisive and "product-y." | §24 #8 — a precise score over incomplete/non-comparable data misleads the buyer; cheapest-wins fallacy. | Comparability verdict + qualitative readiness, scoring deferred until comparable. |
| **UI polish without strong AI behavior** | UI is the visible, satisfying part. | §24 #9 — UI is only 10%; polishing it while AI is weak inverts the rubric. | Get the 70% AI behavior solid first; polish UI last and only enough to make AI legible. |
| **Database / queue / vector store / auth** | "Real apps have these." | Out of scope (PROJECT.md, CLAUDE.md §10); no 5-day feature needs persistence. | Files + in-memory/session state. |
| **Quantitative should-cost engine** | Sophisticated procurement feature. | Requires baselines we'd have to invent → hallucination. | Qualitative, grounded "attention point" only, if at all. |

---

## Feature Dependencies

```
RFQ Generation agent
    └──feeds──> Vendor Response Generation agent (vendors respond TO the RFQ's 8 items)
                    └──enhanced-by──> Messy/complex-data generation (injects §9 complexity)
                            └──produces──> sample data (committed) + live-generated input

Vendor input (paste/upload, Screen 2)
    └──feeds──> Extraction agent (Screen 3)
                    ├──requires──> Evidence snippets  ──validated-by──> Code-enforced grounding
                    └──produces──> Missing/unclear/conflicting/unsupported flags
                            └──feeds──> Comparison agent (Screen 4)
                                    ├──requires──> Comparability-before-ranking (gate before any difference view)
                                    └──triggers──> Clarification questions (per gap/conflict)

Prompt Pack (all 7 prompts) ──underpins──> every agent above
    └──surfaced-by──> Prompt Trace / Prompt Pack view (Screen 5)

UI/UX Generation prompt ──guides──> Screens 1–5 structure + copy
```

### Dependency Notes

- **Comparison requires Extraction (hard):** comparison is grounded in extracted facts + evidence. Extraction must be solid before comparison is meaningful — phase ordering must put extraction first.
- **Comparability-before-ranking gates the comparison view:** the "who's comparable" verdict must be computed before any side-by-side difference or readiness signal is shown. It's a gate, not a panel.
- **Code-enforced grounding validates evidence snippets:** these ship together; an evidence snippet with no code validation is just an LLM assertion (the thing we're guarding against).
- **Messy-data gen depends on vendor-gen:** messiness is a controlled variation layer over the base vendor responses; it can't exist without them.
- **Clarification questions depend on flags:** a clarification question is generated *from* a missing/unclear/conflicting flag — no flags, nothing to clarify.
- **Vendor-gen depends on RFQ-gen:** vendors respond to a specific RFQ; the 8 line items are the shared spine that makes the comparison line up.

---

## MVP Definition

### Launch With (v1 — the gradeable core, ~70% of rubric)

- [ ] **RFQ Generation agent** — the spine everything aligns to (data-gen 20%).
- [ ] **Vendor-gen + messy-data injection** — ≥3 deliberately messy responses (data-gen 20%; §24 forbids clean data).
- [ ] **Extraction agent with evidence snippets + 4 flag types** — the 20% extraction core.
- [ ] **Code-enforced grounding** — the headline reliability claim; without it, evidence is just assertion.
- [ ] **Comparison agent with comparability-before-ranking + clarification questions** — the 15% comparison core.
- [ ] **The Prompt Pack (all 7 prompts) + per-prompt rationale** — the 30% single largest area.
- [ ] **≥1 Prompt Trace** — required §16, cheap, lifts 30% + 5%.
- [ ] **Screens 1–4** rendering the above legibly (UI 10%) + **Screen 5 / trace view**.
- [ ] **Dynamic processing** — live agent runs on pasted/uploaded input (§11; not hardcoded).

### Add After Core Works (v1.x — §21 high-ROI lifts)

- [ ] **Architecture diagram** — trigger: core done, polishing docs (5% demo/docs, cheap).
- [ ] **Prompt failure examples + fixes** — trigger: prompts stabilized; strong 30% lift.
- [ ] **Comparability matrix / readiness signal view** — trigger: comparison agent solid; lifts 15%.
- [ ] **Per-RFQ-line-item alignment view** — trigger: extraction stable across vendors.
- [ ] **More document formats / 4th vendor** — trigger: time remains after core.

### Future Consideration (defer — low ROI for 5 days)

- [ ] **OCR support** — defer: §11 says not required; HIGH cost.
- [ ] **Human review workflow (stateful)** — defer: tempts DB/scope creep; describe as "what's next" instead.
- [ ] **Feedback loop (built)** — defer: describe the *design* in the write-up for §21 credit without building.
- [ ] **Quantitative should-cost / weighted scoring** — defer/avoid: hallucination + misleading-comparison risk.

---

## Feature Prioritization Matrix

| Feature | Buyer/Rubric Value | Implementation Cost | Priority |
|---------|--------------------|---------------------|----------|
| Prompt Pack (7 prompts + rationale) | HIGH (30%) | MEDIUM | P1 |
| Extraction agent + evidence + flags | HIGH (20%) | HIGH | P1 |
| Code-enforced grounding | HIGH (reliability headline) | MEDIUM-HIGH | P1 |
| Vendor-gen + messy-data injection | HIGH (20%) | MEDIUM | P1 |
| RFQ Generation agent | HIGH (20%, the spine) | MEDIUM | P1 |
| Comparison agent + comparability-first | HIGH (15%) | HIGH | P1 |
| Clarification-question generation | HIGH (15% + §15.7 required) | MEDIUM | P1 |
| Screens 1–4 (legible buyer UI) | MEDIUM (10%) | MEDIUM | P1 |
| ≥1 Prompt Trace | MEDIUM (required, cheap) | LOW | P1 |
| Screen 5 / Prompt Pack in-app view | MEDIUM (30% + 5% support) | LOW-MEDIUM | P1/P2 |
| Buyer info-hierarchy (risk/gaps first) | HIGH (15% product thinking) | LOW (design discipline) | P1 |
| Architecture diagram | MEDIUM (5%) | LOW | P2 |
| Prompt failure examples + fixes | MEDIUM (30% lift) | LOW-MEDIUM | P2 |
| Comparability matrix / readiness signal | MEDIUM (15% lift) | MEDIUM | P2 |
| Per-line-item alignment view | MEDIUM (15% lift) | MEDIUM | P2 |
| More formats / 4th vendor | LOW-MEDIUM (20% lift) | LOW | P2/P3 |
| Human review workflow | MEDIUM | MEDIUM (stateful) | P3 |
| OCR | LOW (not required) | HIGH | P3 |
| Should-cost / weighted scoring | NEGATIVE (misleading risk) | HIGH | Avoid |

**Priority key:** P1 = must-have for submission · P2 = add when core is solid · P3 = nice-to-have / future.

---

## Competitor / Convention Feature Analysis

Bid Desk has no direct "competitor" (it's an assignment), so this compares against **how procurement tools / practice handle the same job**, to show where Bid Desk deliberately conforms vs. diverges.

| Feature | Traditional bid-tab / Excel | Procurement software (e.g. ProQsmart, PurchaserAI) | Bid Desk approach |
|---------|-----------------------------|----------------------------------------------------|-------------------|
| Side-by-side comparison | Manual spreadsheet, error-prone | Auto bid comparison, 500+ line items | AI-extracted + evidence-grounded side-by-side, ≤4 vendors |
| Handling missing data | Blank cells, manually chased | Flagged as exceptions | First-class missing/unclear/conflicting/unsupported flags, prominently surfaced |
| Normalization | Manual unit/currency normalization | Auto-normalize to a baseline | **Deliberately light** — surface differences + flag non-comparability (§24); no fabricated baseline |
| Scoring | Weighted scoring, ranked | Weighted scoring models (MCDA/TCO/BVP) | Comparability-first; qualitative readiness over numeric score (avoids §24 misleading-comparison) |
| Clarifications | Cure letters / written queries | Workflow-managed clarification | AI-drafted, gap-grounded clarification questions |
| Trust / auditability | Human-checked | Software audit trail | Evidence snippet per fact + code-enforced grounding (no fabrication) |

---

## Open Questions for Roadmap / Phase Planning

- **Where does Screen 5 live?** In-app vs. README/docs (§6 says optional, §16 says ≥1 trace required somewhere). Recommend in-app for demo value, but it can slip to docs if time-pressed.
- **Comparability signal representation:** matrix vs. narrative vs. badge per dimension — a product-thinking decision worth resolving in the comparison phase (touches 15%).
- **How much line-item alignment counts as "light" vs. "heavy normalization":** lining bids up to the RFQ's 8 items is fine; converting currencies/units into one number is the §24 trap. Draw this boundary explicitly during comparison-agent planning.

---

## Sources

- Assignment brief — `docs/assignment.md` §4–§24 (source of truth for table-stakes, §21 differentiators, §24 anti-features). HIGH confidence.
- [Bid evaluation models in sourcing (CBA, MCDA, TCO, BVP)](https://blog.learnhowtosource.com/bid-evaluation-models-in-sourcing/) — MEDIUM.
- [What is RFQ Bid Evaluation? Process & metrics (Hyperbots)](https://www.hyperbots.com/glossary/rfq-bid-evaluation) — MEDIUM.
- [Auto Bid Comparison / bid tabulation (ProQsmart)](https://proqsmart.com/blog/auto-bid-comparison-comparing-500-line-item-bids-without-manual-entry-proqsmart/) — MEDIUM.
- [Excel vs. Procurement Software: 2026 Buyer's Guide to RFQ/Bid Comparison (PurchaserAI)](https://purchaser.ai/blog/excel-vs-procurement-software-buyers-guide-rfq-bid-comparison/) — MEDIUM.
- [Critical importance of price benchmarking / normalization (Maple Sourcing)](https://www.maplesourcing.com/the-critical-importance-of-benchmarking-prices-with-competitors-in-modern-procurement.html) — MEDIUM (normalization / apples-to-oranges).
- [Total Cost of Ownership (TCO) framework (Umbrex)](https://umbrex.com/resources/frameworks/supply-chain-frameworks/total-cost-of-ownership-tco/) — MEDIUM (should-cost / TCO context).
- [How to handle a non-responsive bid (RFPverse)](https://www.rfpverse.com/faqs/how-do-you-handle-a-non-responsive-bid) — MEDIUM (responsive vs. non-responsive, clarification/cure letters).
- [Maryland Procurement Manual — Review & Evaluation Process](https://procurement.maryland.gov/mpm-6-review-and-evaluation-process/) — MEDIUM (cure letters / clarification workflow).
- [Key strategies for competitive bid analysis (4castplus)](https://4castplus.com/key-strategies-for-a-successful-competitive-bid-analysis-when-awarding-an-rfq/) — MEDIUM.

---
*Feature research for: prompt-driven procurement RFQ extraction + vendor-comparison AI prototype (Bid Desk)*
*Researched: 2026-06-27*
