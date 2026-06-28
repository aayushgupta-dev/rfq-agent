# UI/UX Generation Prompt Documentation

**Prompt:** `services/ai/prompts/ui-ux-gen.v1.md`
**Version:** 1
**Model tier:** cheap (gpt-5.4-mini)

---

## What It Does

The ui-ux-gen prompt generates a structured Markdown UI/UX specification for the five Bid
Desk buyer screens: RFQ Overview, Vendor Upload/Input, Extraction Review, Vendor Comparison,
and Prompt Trace. It frames the model as a procurement UX designer and produces per-screen
design contracts covering information hierarchy, key components, interactions, UX copy, and
explicit absent/error state designs for every FlagStatus value (`present`, `missing`,
`unclear`, `conflicting`, `unsupported`).

The prompt is run once to produce a captured UI/UX spec artifact — the live run artifact is
at `docs/traces/ui-ux-gen-run.md`. That artifact directly informed the shadcn/React
implementation, making the "prompt-driven UI" claim honest and traceable. The 10% UI/UX
rubric weight requires a genuine prompt artifact; a static design spec would not satisfy it.

---

## Why It Is Structured This Way

**Procurement-UX persona, not generic designer.** The prompt opens by framing the model as a
"procurement UX designer specialising in tools that help professional buyers make high-stakes
vendor selection decisions." This is not cosmetic — procurement UI has a different information
hierarchy than a typical SaaS dashboard (absence and uncertainty are primary signals, not
edge cases). A generic designer persona produces generic SaaS patterns: summary cards at top,
data tables, maybe a filter bar. A procurement persona produces absence-first designs where
missing information is unmissable.

**Product principles embedded as non-negotiables.** The five product principles from
`CLAUDE.md §1` are embedded directly in the prompt body (evidence over assertion, absence
first-class, comparability before ranking, buyer-first information hierarchy, no fabricated
claims). Each principle is paired with a specific design implication. This prevents the model
from producing a specification that is technically formatted correctly but violates the
product's core reliability rules.

**Absent-state design rule as a first-class section.** A dedicated "Absent-State Design Rule"
section specifies the exact rendering for all five FlagStatus values before the per-screen
instructions begin. This ensures that every screen specification that follows inherits the
same absence-first design vocabulary. Without this upfront rule, the model would design absent
states inconsistently across screens (or omit them from lower-priority screens).

**Cheap model tier.** ui-ux-gen uses `gpt-5.4-mini` (cheap tier) rather than `gpt-5.4`
(reasoning tier). The task is structured-output generation from a fully specified prompt —
the model is producing a formatted Markdown document following explicit section instructions,
not performing extraction reasoning or comparison reasoning. The cheap tier is sufficient and
avoids unnecessary cost for a one-time artifact capture.

**Per-screen sections with H2/H3 format constraint.** The prompt specifies the exact output
format (H2 per screen, H3 per sub-section) matching the five sub-sections each screen must
have. This format constraint ensures the output maps directly to the component tree the
React implementation follows — the artifact is a design contract, not free-form prose.

---

## How It Handles Unreliable / Missing / Conflicting Information

The ui-ux-gen prompt generates a UI specification, not a structured extraction. Unreliable
information in this context means: the model produces generic SaaS copy, omits absent states,
or designs for only the happy path. The prompt handles these failure modes explicitly:

| Scenario | Prompt Instruction | Outcome |
|---|---|---|
| Model produces generic SaaS dashboard copy ("Welcome to your dashboard") | Opening persona section re-asserts buyer context: "sense-making over decoration." "Generic SaaS dashboard patterns" are called out as anti-patterns | Copy uses procurement-professional register |
| Model omits absent states from a screen design | Absent-State Design Rule section is placed before all per-screen instructions and applies to every screen | Every screen specification includes all five FlagStatus designs |
| Model designs for only the happy path (data loaded, all present) | Each screen's "Empty / Error States" sub-section explicitly requires: no data yet, AI failed, partially available, network error | All five states are specified for every screen |
| Model produces a ranking or scoring affordance in the comparison screen | Comparability-before-ranking principle is stated as non-negotiable; the comparison screen instructions explicitly prohibit sorting vendors and require a "not a ranking" label | Comparison screen has no scoring UI |
| Model fabricates components or data sources not in the AI pipeline | Each screen's "Key Components" section specifies the exact data source (`ExtractionResult.vendor_id`, `ComparisonResult.matrix`, etc.) | Components are grounded in the real schema |

If the model produces output that violates these constraints, the failure handling is
prompt-level: the buyer context and product principles are re-stated, and the screen section
is regenerated with a stricter constraint on the failing element. A v2 prompt would add
few-shot examples of correct vs. incorrect absent-state designs for the extraction review
screen (the most complex case).
