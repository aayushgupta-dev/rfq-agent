# Messy Data Generation Prompt Documentation

**Prompt:** `services/ai/prompts/messy-data-gen.v1.md`
**Version:** 1
**Model tier:** cheap (gpt-5.4-mini)

---

## What It Does

The messy-data-gen prompt serves as the definitive issue-type taxonomy reference for the Bid
Desk data generation pipeline. It documents the 8 deliberate flaw types that can be injected
into vendor responses via the mess spec: missing price, bundled scope, vague timeline,
weak compliance claim, internal conflict, partial scope, currency ambiguity, and fluff
substitution. Each type includes its name, description, an example of how it appears in
vendor prose, why it causes buyer problems, and how it stresses the extraction agent.

This prompt is the canonical reference artifact — it is not a live generation call in the
current pipeline. The taxonomy content is embedded inline in `vendor-gen.v1.md` (as a
condensed table) for efficiency; messy-data-gen is the versioned, human-readable source.

---

## Why It Is Structured This Way

**Dedicated taxonomy reference with FlagStatus mapping.** The prompt exists as a standalone
Prompt Pack entry so reviewers can trace from mess spec instruction to expected extraction
output without reading the full vendor-gen prompt. Each issue type is mapped to its expected
`FlagStatus` (`missing`, `unclear`, `conflicting`, `unsupported`) and whether it should
trigger a clarification question. This bridge between data-generation and extraction layers
is a rubric differentiator: the §21 evaluation criteria reward making the AI behavior
traceable and explained.

**No input parameters.** messy-data-gen has no `{variable}` slots. It is a reference
document, not a parameterized generation prompt. This is intentional: the taxonomy is
version-controlled and reviewable as a first-class artifact, but the actual generation
(producing messy vendor responses) happens through vendor-gen which receives the mess spec
as structured input. Keeping the taxonomy separate prevents it from becoming stale when
vendor-gen's instructions are updated.

**FlagStatus mapping as a calibration record.** The summary table mapping each issue type to
its expected extraction result serves as a calibration record: if the extraction agent
consistently produces different FlagStatus values than the table predicts for a given flaw
type, it indicates either a taxonomy mismatch or an extraction agent reliability gap. The
table is consulted during Phase 3 extraction agent development to confirm coverage of each
flaw type.

---

## How It Handles Unreliable / Missing / Conflicting Information

As a reference document rather than a generation prompt, messy-data-gen itself does not
process vendor input. Its reliability role is structural: it defines what "unreliable
information" looks like in vendor responses so that both the generation agents (vendor-gen)
and the extraction agent know the expected surface forms.

| Scenario | Role in messy-data-gen | Outcome |
|---|---|---|
| Taxonomy describes a flaw that the extraction agent misses | The FlagStatus mapping in the table serves as the specification for what the extraction agent must surface | If extraction misses the flaw, the mismatch is detectable by comparing extraction output against the table |
| Messiness assertions fail on regeneration (model drift) | The flaw type descriptions are concrete enough to generate new mess spec instructions or to author a v2 vendor-gen prompt | Regeneration produces flaws assertable by the same test suite |
| New flaw type is discovered during extraction agent development | Add the new type to messy-data-gen first (versioned reference), then update vendor-gen's taxonomy table and the test assertions | Taxonomy change is traceable from the reference document |

A v2 prompt would be triggered by: (1) new issue types identified during extraction agent
development, (2) FlagStatus mapping changes when the ExtractionResult schema is extended,
or (3) the taxonomy becoming inadequate for new vendor response formats encountered in
live use.
