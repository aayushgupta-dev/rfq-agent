# Phase 2: Grounding Gate & Messy Data - Research

**Researched:** 2026-06-27
**Domain:** Python text-span matching / offset remapping; pydantic v2 model traversal; LangChain structured + plain-text LLM calls; messy data generation
**Confidence:** HIGH (all critical claims verified via official docs, Context7, or live code probes)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Grounding match strategy (EXTRACT-04)**
- D-01: Search & recompute, never trust model offsets. Gate ignores model-supplied `char_start`/`char_end`, searches source text for the snippet, rewrites REAL offsets on hit.
- D-02: Moderate normalization before matching: collapse whitespace/newlines, case-fold, Unicode NFKC, normalize smart quotes & dashes — keep letters/digits/currency symbols intact. NOT aggressive (no full punctuation stripping — `$1,200` must not match `1200`).
- D-03: Fuzzy fallback = `rapidfuzz.partial_ratio` (substring-aware) over a sliding window, accept only at ~90/100. Fires only when normalized-exact misses. Exact threshold tuned in tests.
- D-04 (flagged for research): offset remapping from normalized to original space — solved here.

**Grounding gate contract**
- D-05: Pure single-field core `ground_field(field, sources)` + schema-agnostic recursive walker.
- D-06: Pure function returning NEW object + structured downgrade report (field path, original status, reason).
- D-07: Sources supplied as `dict[str, str]` keyed by `Evidence.source_id`.

**Vendor-gen pipeline (DATA-02/03)**
- D-08: One-pass generation. `vendor-gen(RFQ, persona, mess_spec)` emits messy response directly. `messy-data-gen` is the taxonomy/reference the prompt embeds.
- D-09: Mess specs are hand-authored in code, one per persona.
- D-10: Exactly 3 complementary personas: (1) thorough-but-pricey, (2) cheap-but-incomplete, (3) polished-fluff.

**Generated document shape (DATA-01/02/04)**
- D-11: RFQ = structured pydantic `RFQ` (8 line items + scope + timelines + questionnaire + compliance) via structured output, PLUS rendered Markdown. Schema fleshed out this phase.
- D-12: VendorResponse = raw messy text + provenance metadata (`vendor_name`, `persona`, `mess_spec`, `source_id`, `format_label`). NOT pre-extracted. 3 different formats (letter/email vs tabular proposal vs deck-style outline).

**Messiness testing (DATA-03)**
- D-13: Tests run against COMMITTED sample fixtures (deterministic, CI-safe). Live regen is a separate smoke path, not content-asserted.

**Prompt Pack (PROMPT-04)**
- D-14: Capture ≥1 documented prompt failure example + fix from real vendor-gen/rfq-gen authoring. In Prompt Pack docs with versioning/eval notes.

### Claude's Discretion
- Module layout within `services/ai` for the gate (e.g. `services/ai/grounding/`), exact function names/signatures beyond D-05–D-07, and the downgrade report data structure.
- The precise normalization pipeline ordering and exact fuzzy threshold (tuned in tests).
- Persona prose styles / format-divergence details beyond the 3 failure profiles.
- How sample fixtures are stored under `data/` and the live-regen API surface.

### Deferred Ideas (OUT OF SCOPE)
- File upload (PDF/Word/Excel/PPT) — Phase 5.
- RFQ Overview / Vendor Input screen rendering — Phase 5.
- Extraction agent that produces `Field[T]` facts the gate validates — Phase 3.
- 4th vendor persona (multi-currency/tax-ambiguous) — possible later.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXTRACT-04 | Grounding enforced in code — evidence spans verified via normalized exact → fuzzy; unlocatable facts downgraded to `unsupported` | D-01..D-07; offset remapping technique (§Offset Remapping); rapidfuzz API (§Fuzzy Fallback) |
| DATA-01 | Generate one realistic marketing-services RFQ via prompt — 8 line items, scope, timelines, commercials, questionnaire, compliance | D-11; LangChain `with_structured_output` pattern; RFQ schema design (§Standard Stack / §Architecture Patterns) |
| DATA-02 | Generate ≥3 deliberately messy vendor responses via prompt, each driven by explicit per-vendor mess spec | D-08..D-10; D-12; one-pass generation pattern (§Architecture Patterns) |
| DATA-03 | Inject real-world complexity; messiness asserted in tests | D-09; D-13; mess-spec design; deterministic fixture approach |
| DATA-04 | Commit generated RFQ + ≥3 vendor responses as sample data AND regenerable live in-app | D-12; live-regen API surface (§Architecture Patterns) |
| PROMPT-04 | ≥1 documented prompt failure + fix; versioning/eval notes | D-14; Prompt Pack registry patterns already in place |
</phase_requirements>

---

## Summary

Phase 2 has two independent work streams that converge at the sample data: the **grounding gate** (pure Python, LLM-free) and the **messy data generators** (LLM-driven). Both are well-understood technically — the main novelty is in D-04's offset remapping and the exact rapidfuzz API surface needed to recover source indices from a fuzzy hit.

**Grounding gate:** The offset remapping problem (D-04) has a clean, verified solution: build a `norm_to_orig: list[int]` array char-by-char during normalization, where `norm_to_orig[i]` = index in the original string that produced normalized character `i`. Lookups are O(1). This was live-tested against the `ﬁ` ligature (U+FB01 → "fi", length 1→2) and confirmed working. The `rapidfuzz.fuzz.partial_ratio_alignment` API returns a `ScoreAlignment` namedtuple with `score`, `src_start`, `src_end`, `dest_start`, `dest_end` — the `dest_start`/`dest_end` are the matching region indices in the LONGER string (the normalized source text), which then feed back through `norm_to_orig` to recover original offsets. There is no need for a manual sliding window.

**Data generation:** For structured RFQ output, LangChain's `.with_structured_output(RFQ)` on `ChatOpenAI` uses the gpt-5.4 "reasoning" tier cleanly with pydantic v2 models. For vendor-gen, a plain `.invoke()` returning `AIMessage.content` (string) is used since vendor responses are deliberately unstructured messy text — NOT structured output. The RFQ schema requires non-trivial fleshing out to carry 8 line items with all mandatory sub-fields; this is the most complex schema change in the phase and propagates through `shared-types` codegen.

**Primary recommendation:** Implement the grounding gate as `services/ai/grounding/gate.py` with a `_normalize()` helper that returns both the normalized string and the `norm_to_orig` map; wire `partial_ratio_alignment` as the fuzzy fallback using `dest_start`/`dest_end` → `norm_to_orig` for offset recovery. Implement the recursive walker using pydantic v2's `model_fields` + `isinstance(value, Field)` duck-typing.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Grounding gate (span verification) | Backend / AI service | — | Pure code, LLM-free; has no frontend presence in P2 |
| Downgrade report | Backend / AI service | Data layer (fixtures) | Report used in tests and later passed to SSE in P3 |
| RFQ generation | Backend / AI service | — | LLM call via LangChain; structured output lands in `data/` |
| Vendor response generation | Backend / AI service | — | LLM call via LangChain; plain-text output lands in `data/` |
| Sample fixture storage | Data layer (`data/`) | Backend (live-regen API) | Committed files serve tests; API endpoint serves in-app regen |
| Schema extension (RFQ, VendorResponse) | Backend / AI service | Contract (`shared-types`) | pydantic is source of truth; TS contract regenerated after every schema change |
| Prompt Pack authoring | Backend / AI service | `docs/prompts/` | Source in `services/ai/prompts/`; documentation in `docs/prompts/` per CLAUDE.md §14 |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `rapidfuzz` | 3.13.0 (PyPI latest) | Fuzzy span matching with alignment | MIT, ~25M weekly downloads, de-facto Python fuzzy lib; `partial_ratio_alignment` gives exact `dest_start`/`dest_end` offsets without hand-rolling sliding window |
| `unicodedata` (stdlib) | Python 3.12 built-in | NFKC normalization + offset map | No extra dependency; `unicodedata.normalize('NFKC', text)` is the standard |
| `pydantic` v2 | ≥2.13.4 (already in pyproject) | Schema definition + model_fields traversal | Already installed; `model_fields` dict enables schema-agnostic walker |
| `langchain-openai` | ≥1.3.3 (already installed) | Structured output (`with_structured_output`) + plain-text completion | Already installed; `.with_structured_output(RFQ)` for DATA-01, `.invoke()` for DATA-02 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | ≥9.1.1 (already in dev deps) | Grounding gate unit tests + messiness assertions | All EXTRACT-04 and DATA-03 tests |
| `python-frontmatter` | ≥1.3.0 (already installed) | Load authored prompt stubs from `prompts/*.v1.md` | RFQ-gen + vendor-gen prompt loading |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rapidfuzz.fuzz.partial_ratio_alignment` | Manual sliding-window over `fuzz.ratio` | Manual window is O(N²) and returns no offset information — must re-scan to find the match window; no benefit vs built-in |
| `unicodedata.normalize` char-by-char loop | `re.sub` + difflib post-hoc remapping | difflib Ratcliff-Obershelp does not guarantee minimum edits; post-hoc remap requires a second O(N) pass; char-by-char loop is O(N) and exact |
| `langchain-openai` `.with_structured_output` | Raw `openai` SDK structured output | LangChain already installed and provides LangGraph integration; raw SDK is lower-level with no added benefit for this phase |

**Installation (new dependency only):**
```bash
# From services/ai/
uv add rapidfuzz
```

**Version verification (confirmed):**
```bash
pip3 index versions rapidfuzz   # → rapidfuzz (3.13.0) — confirmed 2026-06-27
```

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `rapidfuzz` | PyPI | ~6 years (v0.1.0: 2020) | ~25M/week | github.com/rapidfuzz/RapidFuzz | N/A (slopcheck unavailable) | Approved — confirmed MIT, 6-year history, 25M/wk downloads, official org, Context7 HIGH source reputation |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

*slopcheck binary was unavailable at research time (CLI PATH mismatch), but `rapidfuzz` was independently verified via:*
- *PyPI: `pip3 index versions rapidfuzz` → 3.13.0, 6+ year release history*
- *GitHub: github.com/rapidfuzz/RapidFuzz — org-owned, Max Bachmann maintainer, MIT license confirmed*
- *Context7: Source Reputation HIGH, 391 code snippets*
- *Download stats: ~25M weekly (pypistats.org)*

*All packages above are tagged [VERIFIED: PyPI + official GitHub] for rapidfuzz.*

---

## Architecture Patterns

### System Architecture Diagram

```
RFQ Generation path:
  rfq-gen.v1.md (Prompt Pack)
         │
         ▼
  ChatOpenAI ("reasoning") ──with_structured_output(RFQ)──▶  RFQ (pydantic)
         │                                                         │
         │                                                         ▼
         │                                                  render_rfq_md()
         │                                                         │
         └───────────────────────────────────────────────▶  data/rfq.json
                                                          data/rfq.md (Markdown)

Vendor Generation path (×3 personas):
  vendor-gen.v1.md (embeds messy-data-gen taxonomy)
         │
         ▼
  ChatOpenAI ("reasoning") ──.invoke()──▶ AIMessage.content (raw messy text)
         │                                        │
         │                                        ▼
         │                               VendorResponse(raw_text=..., persona=...,
         │                                              mess_spec=..., source_id=...)
         └────────────────────────────▶  data/vendor_{n}.json (raw text + provenance)

Live-regen API path (DATA-04):
  FastAPI GET /data/rfq or POST /data/vendor-gen
         │
         ▼
  Same generation logic as above (no fixtures, LLM called live)

Grounding Gate path (EXTRACT-04):
  ExtractionResult (any pydantic model with Field[T] fields)
    + dict[source_id, source_text]
         │
         ▼
  ground_model(obj, sources) — recursive walker
         │
         ├─ for each Field[T] instance found in obj:
         │      ground_field(field, sources[field.evidence.source_id])
         │            │
         │            ├─ _normalize(source_text) → (norm_text, norm_to_orig[])
         │            ├─ _normalize(snippet) → (norm_snippet, _)
         │            ├─ exact search: norm_text.find(norm_snippet)
         │            │    HIT  → recompute char_start/char_end via norm_to_orig
         │            │    MISS → fuzzy fallback
         │            │            partial_ratio_alignment(norm_snippet, norm_text)
         │            │                → ScoreAlignment(score, dest_start, dest_end)
         │            │            score >= threshold → recompute offsets
         │            │            score < threshold  → DOWNGRADE
         │            └─ return new Field[T] (replaced or downgraded) + DowngradeEntry
         │
         └─ returns (new_obj, DowngradeReport)
```

### Recommended Project Structure

```
services/ai/
├── grounding/
│   ├── __init__.py        # exports: ground_model, ground_field, DowngradeReport
│   ├── gate.py            # core: _normalize(), _match_exact(), _match_fuzzy(), ground_field(), ground_model()
│   └── report.py          # DowngradeReport / DowngradeEntry dataclasses
├── agents/
│   ├── _demo.py           # (existing)
│   ├── rfq_gen.py         # RFQ generation agent (LangGraph node or plain function)
│   └── vendor_gen.py      # Vendor response generation agent
├── schemas/
│   ├── envelope.py        # (existing — Field[T], Evidence, etc.)
│   ├── domain.py          # RFQ + VendorResponse fleshed out; ExtractionResult/ComparisonResult stay stubs
│   └── events.py          # (existing)
├── prompts/
│   ├── rfq-gen.v1.md      # → authored (stub exists)
│   ├── vendor-gen.v1.md   # → authored (stub exists)
│   └── messy-data-gen.v1.md # → authored as taxonomy reference (stub exists)
├── api/
│   └── app.py             # add /data/rfq and /data/vendor-gen endpoints (DATA-04)
├── scripts/
│   └── generate_samples.py # CLI: python scripts/generate_samples.py → writes data/
data/
├── rfq.json               # committed sample RFQ (pydantic dump)
├── rfq.md                 # committed sample RFQ (rendered Markdown)
├── vendor_thorough.json   # persona: thorough-but-pricey
├── vendor_cheap.json      # persona: cheap-but-incomplete
└── vendor_fluff.json      # persona: polished-fluff
```

### Pattern 1: NFKC Offset Mapping (D-04 — the critical technique)

**What:** Build a `norm_to_orig: list[int]` array during normalization. Each entry maps a position in the normalized string back to the character position in the original string that produced it. NFKC can expand 1 char → N chars (e.g., `ﬁ` U+FB01 → "fi", length 1→2), so a naive `find()` position in normalized space != position in original space.

**When to use:** Any time a match is found in `norm_text` and the gate needs to recompute `char_start`/`char_end` in the original `source_text`.

**Verified:** Live-tested with Python 3.12 on the `ﬁ` ligature (U+FB01). Output confirmed `norm_to_orig[4]` = 4, `norm_to_orig[5]` = 4 (both norm chars map to same orig char), and `source_text[4:7]` = `'ﬁrm'` correctly recovered. [VERIFIED: live probe 2026-06-27]

```python
# Source: live verified 2026-06-27
import unicodedata

def _normalize(text: str) -> tuple[str, list[int]]:
    """Return (normalized_text, norm_to_orig).

    norm_to_orig[i] = index in `text` that produced normalized char i.
    Handles NFKC multi-char expansions (e.g. ligature ﬁ → fi).
    """
    norm_chars: list[str] = []
    norm_to_orig: list[int] = []
    for i, ch in enumerate(text):
        norm_ch = unicodedata.normalize("NFKC", ch)
        # Smart quotes/dashes normalization (D-02)
        norm_ch = (
            norm_ch
            .replace("‘", "'").replace("’", "'")  # ' '
            .replace("“", '"').replace("”", '"')  # " "
            .replace("–", "-").replace("—", "-")  # – —
        )
        # Whitespace collapse: \n, \t, multiple spaces → single space
        # (done as post-process on the full string to preserve word boundaries)
        norm_chars.append(norm_ch)
        norm_to_orig.extend([i] * len(norm_ch))
    raw = "".join(norm_chars)
    # Case-fold and collapse runs of whitespace/newlines into single space
    raw = " ".join(raw.casefold().split())
    # After whitespace collapse, norm_to_orig is no longer 1:1 with `raw`.
    # The whitespace-collapse step requires a SECOND mapping pass.
    # Simplest approach: skip whitespace collapse in the index-building pass;
    # only casefold and NFKC (no length change). Handle whitespace by building
    # a separate collapsed_to_pre_collapse map. See Pattern 2.
    return raw, norm_to_orig
```

**IMPORTANT implementation note:** whitespace collapse changes string length again, so it must be handled in a second mapping pass (see Pattern 2 below). The safe approach is to build the `norm_to_orig` map from NFKC + casefold only (neither changes character count in the same direction that breaks 1:1 mapping at the NFKC step), and handle whitespace by building a second `collapsed_to_pre_collapse` map of surviving character positions.

### Pattern 2: Two-Stage Normalization With Dual Mapping

**What:** NFKC + casefold first (with `norm_to_orig`), then whitespace collapse second (with `collapsed_to_norm`). Compose the two maps: `collapsed_to_norm[i]` → `norm_to_orig[collapsed_to_norm[i]]` = original index.

```python
# Source: derived from verified NFKC probe + Python stdlib docs [VERIFIED: live probe]
import unicodedata
import re

def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Return (normalized, orig_indices) where orig_indices[i] = original char index.

    Two-stage:
      Stage 1: NFKC + smart-quote/dash normalization + casefold (may expand chars)
      Stage 2: whitespace collapse (removes chars, shifts indices)
    Compose both maps so orig_indices[i] always points into the original `text`.
    """
    # Stage 1: NFKC + casefold per char, build stage1 map
    stage1_chars: list[str] = []
    stage1_to_orig: list[int] = []
    for orig_i, ch in enumerate(text):
        n = unicodedata.normalize("NFKC", ch)
        n = (
            n.replace("‘", "'").replace("’", "'")
             .replace("“", '"').replace("”", '"')
             .replace("–", "-").replace("—", "-")
        )
        n = n.casefold()
        stage1_chars.append(n)
        stage1_to_orig.extend([orig_i] * len(n))

    stage1 = "".join(stage1_chars)

    # Stage 2: whitespace collapse — keep positions of surviving chars
    surviving_positions: list[int] = []
    final_chars: list[str] = []
    prev_was_space = False
    for s1_i, ch in enumerate(stage1):
        if ch in (" ", "\t", "\n", "\r"):
            if not prev_was_space:
                final_chars.append(" ")
                surviving_positions.append(s1_i)
            prev_was_space = True
        else:
            final_chars.append(ch)
            surviving_positions.append(s1_i)
            prev_was_space = False

    normalized = "".join(final_chars).strip()
    # Compose: final_i -> stage1_i -> orig_i
    orig_indices = [stage1_to_orig[s1_i] for s1_i in surviving_positions[:len(normalized)]]
    return normalized, orig_indices
```

### Pattern 3: rapidfuzz.fuzz.partial_ratio_alignment — Offset Recovery

**What:** `partial_ratio_alignment` finds the best substring of the longer string that matches the shorter string and returns a `ScoreAlignment` with `score`, `src_start`, `src_end`, `dest_start`, `dest_end`.

**Key semantics (verified from official type stub and docs):**
- `s1` = needle (shorter = normalized snippet), `s2` = haystack (normalized source text)
- `dest_start`/`dest_end` = indices into `s2` (the haystack) of the matched region
- `src_start`/`src_end` = indices into `s1` (the needle)
- Score is in [0, 100]; returns `None` when score < `score_cutoff`

[VERIFIED: rapidfuzz docs + type stub at github.com/rapidfuzz/RapidFuzz/blob/main/src/rapidfuzz/distance/_initialize.pyi]

```python
# Source: rapidfuzz official docs + verified type stub
from rapidfuzz.fuzz import partial_ratio_alignment

def _match_fuzzy(
    norm_snippet: str,
    norm_source: str,
    threshold: float,
    orig_indices: list[int],
) -> tuple[int, int] | None:
    """Return (char_start, char_end) in original source text, or None.

    Uses partial_ratio_alignment to find best-matching substring of
    norm_source for norm_snippet, then maps dest indices back through
    orig_indices to recover original string offsets.
    """
    result = partial_ratio_alignment(
        norm_snippet,          # s1 = shorter needle
        norm_source,           # s2 = longer haystack
        score_cutoff=threshold,
    )
    if result is None:
        return None
    # dest_start/dest_end are indices into norm_source (the haystack)
    orig_start = orig_indices[result.dest_start]
    # dest_end is exclusive; last char of match is at dest_end - 1
    orig_end = orig_indices[result.dest_end - 1] + 1
    return orig_start, orig_end
```

**Threshold tuning:** Start at 90. Test against the three committed sample vendor responses: a genuine evidence span should score ≥90; a completely fabricated snippet should score <90. The threshold is a module-level constant tunable per-test. [ASSUMED: 90 is the starting point from D-03; actual calibration is in tests against real data]

### Pattern 4: Schema-Agnostic Recursive Field[T] Walker (D-05)

**What:** Use pydantic v2's `model_fields` dict (returns `{field_name: FieldInfo}`) combined with `model.__dict__` / `getattr` to get values. Check `isinstance(value, Field)` to detect grounding targets. Recurse into nested `BaseModel` instances.

[VERIFIED: pydantic v2 official docs via Context7 — model_fields returns FieldInfo, iteration via `for name, value in model` or `model.model_fields`]

```python
# Source: pydantic v2 docs (Context7 HIGH reputation source)
from pydantic import BaseModel
from schemas.envelope import Field as EnvelopeField, FlagStatus, Evidence

def _walk_and_ground(
    obj: BaseModel,
    sources: dict[str, str],
    path: str = "",
) -> tuple[BaseModel, list["DowngradeEntry"]]:
    """Recursively find every Field[T] in obj, ground each, return new obj + report.

    Works without knowing obj's concrete type — only uses model_fields.
    """
    updates: dict[str, object] = {}
    report: list[DowngradeEntry] = []

    for field_name, field_info in obj.model_fields.items():
        value = getattr(obj, field_name)
        field_path = f"{path}.{field_name}" if path else field_name

        if isinstance(value, EnvelopeField):
            # This is a grounding target
            grounded, entries = ground_field(value, sources, field_path)
            updates[field_name] = grounded
            report.extend(entries)

        elif isinstance(value, BaseModel):
            # Recurse into nested model
            grounded_sub, sub_entries = _walk_and_ground(value, sources, field_path)
            updates[field_name] = grounded_sub
            report.extend(sub_entries)

        elif isinstance(value, list):
            # Handle list[Field[T]] and list[BaseModel]
            new_list = []
            for i, item in enumerate(value):
                item_path = f"{field_path}[{i}]"
                if isinstance(item, EnvelopeField):
                    grounded_item, item_entries = ground_field(item, sources, item_path)
                    new_list.append(grounded_item)
                    report.extend(item_entries)
                elif isinstance(item, BaseModel):
                    grounded_item, item_entries = _walk_and_ground(item, sources, item_path)
                    new_list.append(grounded_item)
                    report.extend(item_entries)
                else:
                    new_list.append(item)
            updates[field_name] = new_list

    # Return new object (pydantic v2 model_copy with updates)
    return obj.model_copy(update=updates), report
```

**pydantic v2 `model_copy(update=...)` note:** The `model_copy(update={...})` method is the correct v2 way to produce a new instance with changed fields without mutation. [VERIFIED: pydantic v2 docs via Context7]

### Pattern 5: LangChain Structured Output (RFQ — DATA-01)

**What:** `.with_structured_output(RFQ)` on `ChatOpenAI` returns a validated `RFQ` pydantic instance directly. Use the "reasoning" tier from the existing `get_llm("reasoning")` factory.

[VERIFIED: LangChain docs via Context7 — method="json_schema" is the recommended approach with pydantic v2]

```python
# Source: LangChain docs (Context7 HIGH)
from langchain_core.prompts import ChatPromptTemplate
from prompts.registry import load
from llm.factory import get_llm
from schemas.domain import RFQ

def generate_rfq() -> RFQ:
    prompt_post = load("rfq-gen")
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_post.content),
        ("human", "Generate the RFQ now."),
    ])
    llm = get_llm("reasoning")
    chain = prompt | llm.with_structured_output(RFQ, method="json_schema")
    return chain.invoke({})
```

### Pattern 6: Plain-Text LLM Call (VendorResponse — DATA-02)

**What:** Vendor responses are deliberately unstructured messy text. Use plain `.invoke()` returning `AIMessage.content`. Do NOT use structured output — that would work against D-08's "organically messy" design intent.

```python
# Source: LangChain docs (Context7 HIGH)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from prompts.registry import load
from llm.factory import get_llm
from schemas.domain import VendorResponse

def generate_vendor_response(rfq_text: str, persona: str, mess_spec: list[dict]) -> VendorResponse:
    prompt_post = load("vendor-gen")
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_post.content),
        ("human", "RFQ:\n{rfq_text}\n\nPersona: {persona}\n\nMess spec:\n{mess_spec}"),
    ])
    llm = get_llm("reasoning")
    chain = prompt | llm
    result: AIMessage = chain.invoke({
        "rfq_text": rfq_text,
        "persona": persona,
        "mess_spec": str(mess_spec),
    })
    raw_text: str = result.content  # type: ignore[assignment]
    return VendorResponse(
        vendor_name=persona,
        persona=persona,
        mess_spec=mess_spec,
        source_id=f"vendor_{persona}",
        format_label="letter",  # varies by persona
        raw_text=raw_text,
    )
```

### Pattern 7: RFQ Schema Design (D-11 — flesh out this phase)

The RFQ schema needs to carry 8 line items with structured sub-fields. Key constraint: `model_config = ConfigDict(extra="forbid")` must stay; `# noqa: UP046` is needed on any `Generic[T]` class (established pattern from envelope.py). The schema MUST NOT use `Field[T]` wrapper — the RFQ is our own clean artifact, not a grounded extraction.

```python
# Sketch — concrete field names to be determined during implementation
class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str                     # e.g. "strategy-creative"
    name: str
    description: str
    deliverables: list[str]
    timeline_weeks: int | None = None
    budget_range_usd: tuple[int, int] | None = None

class RFQ(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    client_name: str
    issue_date: str
    response_deadline: str
    scope_summary: str
    line_items: list[LineItem]   # exactly 8 for the sample; no hard constraint
    commercial_expectations: str
    questionnaire: list[str]
    compliance_requirements: list[str]
    budget_total_usd: int | None = None
```

**codegen impact:** Adding real fields to `RFQ` and `VendorResponse` triggers the pydantic2ts drift-check test (PLAT-02). The plan must include a step to run `uv run python scripts/codegen.py` and commit the updated `packages/shared-types` TS output alongside the schema change.

### Anti-Patterns to Avoid

- **Using model-supplied `char_start`/`char_end` directly:** The gate's entire purpose is to IGNORE these (D-01). Never pass them through without re-grounding.
- **Single-pass normalization + offset assumption:** Whitespace collapse and NFKC can both change string length. Build the two-stage map; don't assume normalized position = original position.
- **Calling `partial_ratio` (score only) instead of `partial_ratio_alignment`:** `partial_ratio` returns a float with no location info. You need `partial_ratio_alignment` to get `dest_start`/`dest_end`.
- **Structured output for vendor-gen:** Using `with_structured_output` for vendor responses defeats the "organically messy" requirement. Vendor text must be raw unstructured prose.
- **Mutating `Field[T]` in-place:** The envelope has `model_validator` that will reject invalid states. Always produce a new instance via `model_copy(update=...)` or constructor (D-06).
- **Asserting messiness via live LLM calls in CI:** Tests must run against committed fixtures only (D-13). LLM nondeterminism + API cost make live-gen tests unreliable in CI.
- **Importing `pydantic.Field` directly in gate.py:** The project has established the `# ponytail: class named Field shadows pydantic.Field — alias import` pattern. Use `from schemas.envelope import Field as EnvelopeField` and `from pydantic import Field as pydantic_Field`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy substring match with offset return | Sliding window + manual scoring loop | `rapidfuzz.fuzz.partial_ratio_alignment` | Returns `ScoreAlignment.dest_start`/`dest_end` directly; O(N) internal implementation; handles short/long needle separately |
| Unicode normalization | Custom char-mapping table | `unicodedata.normalize('NFKC', text)` (stdlib) | NFKC is the correct Unicode standard form for compatibility normalization; stdlib handles all Unicode edge cases |
| NFKC offset mapping | Post-hoc difflib remapping | Char-by-char `norm_to_orig` array (Pattern 2) | difflib Ratcliff-Obershelp is not minimum-edit; char-by-char is O(N), exact, and simple |
| LLM structured output validation | Manual JSON parsing + field assignment | `llm.with_structured_output(RFQ, method="json_schema")` | LangChain wraps schema generation, JSON mode enforcement, and pydantic instantiation; no manual parsing |
| Prompt file loading | `open(f"prompts/{id}.md")` with custom frontmatter parse | `prompts.registry.load(id)` (already exists) | Registry handles version resolution + `python-frontmatter` parsing; already tested |

**Key insight:** The offset remapping is the hardest custom logic in this phase. Everything else (fuzzy matching, structured output, prompt loading) has a well-maintained library solution already in the stack.

---

## Common Pitfalls

### Pitfall 1: Whitespace Collapse Breaks the norm_to_orig Map
**What goes wrong:** Building `norm_to_orig` in a single pass that includes whitespace collapse produces wrong indices because collapse removes characters (runs of spaces → single space), shifting all subsequent positions.
**Why it happens:** NFKC expands chars (length can grow); whitespace collapse contracts them (length can shrink). Combining both in one pass creates a non-monotonic index map.
**How to avoid:** Two-stage normalization (Pattern 2): build `stage1_to_orig` from NFKC+casefold only (no length reduction), then build `collapsed_to_stage1` from whitespace collapse, then compose.
**Warning signs:** Unit tests where a real snippet fails to ground when the source text has multiple consecutive spaces or newlines.

### Pitfall 2: partial_ratio_alignment dest_end Is Exclusive
**What goes wrong:** Using `orig_indices[result.dest_end]` instead of `orig_indices[result.dest_end - 1] + 1` for `char_end` produces an off-by-one error.
**Why it happens:** Python slice convention — `dest_end` is exclusive, so the last matched character in `s2` is at `dest_end - 1`.
**How to avoid:** Always use `orig_indices[result.dest_end - 1] + 1` for the exclusive end offset. Write a unit test asserting that `source_text[char_start:char_end] == original_snippet_text`.
**Warning signs:** Evidence span highlights that are one character short or extend one character past the actual text.

### Pitfall 3: Fabricated Snippet Scores High on partial_ratio
**What goes wrong:** A short fabricated snippet (e.g., "yes" or "$0") scores ≥90 against almost any source text because `partial_ratio` is substring-aware and very short strings match trivially.
**Why it happens:** `partial_ratio` finds the BEST matching substring of the longer string, so a 3-character needle will almost always find a high-scoring window.
**How to avoid:** Add a minimum snippet length guard (e.g., reject snippets shorter than 20 chars as too-short-to-ground; mark them `unsupported` directly). Make this length threshold a constant tested explicitly.
**Warning signs:** Fabricated snippets like "Q3" or single words never getting downgraded despite being clearly fabricated.

### Pitfall 4: pydantic2ts Drift on RFQ Schema Change
**What goes wrong:** RFQ and VendorResponse fields change in `domain.py` but the TS types in `packages/shared-types` aren't regenerated, causing the drift-check test to fail.
**Why it happens:** The Phase 1 codegen drift-check runs `python scripts/codegen.py` and diffs the output. Any change to domain.py fields silently breaks the check until codegen is re-run.
**How to avoid:** Every plan wave that touches `domain.py` must include a task to re-run codegen and commit the updated TS output. This is a Phase 1 established pattern (PLAT-02).
**Warning signs:** `test_codegen_drift.py` failing in CI.

### Pitfall 5: ConflictingValue Fields in ground_field
**What goes wrong:** A `Field[T]` with `status=conflicting` has `values[]` where each `ConflictingValue[T]` carries its own `evidence` list. The walker must ground EACH `ConflictingValue.evidence[i]` individually, not just the top-level `evidence: list[Evidence]` (which is empty for `conflicting` fields per the envelope invariant).
**Why it happens:** The envelope's semantic rules mean `conflicting` fields carry no top-level `evidence` — evidence is inside each `ConflictingValue`. A gate that only checks `field.evidence` misses this case entirely.
**How to avoid:** `ground_field()` must branch on `field.status == conflicting` and iterate `field.values` to ground each `cv.evidence` list.
**Warning signs:** Conflicting fields never get downgraded even when their evidence snippets are fabricated.

### Pitfall 6: RFQ Structured Output Schema Complexity
**What goes wrong:** `with_structured_output(RFQ)` may hit OpenAI's JSON schema constraints if the RFQ model has deeply nested types or `tuple[int, int]` fields (OpenAI structured output has a subset-of-JSON-schema restriction).
**Why it happens:** OpenAI strict structured output doesn't support all JSON Schema features (e.g., `tuple` types, certain `anyOf` patterns, `minLength`/`maxLength`).
**How to avoid:** Use only `str`, `int`, `float`, `bool`, `list[T]`, and nested `BaseModel` in the RFQ schema. Avoid Python `tuple` — use `list[int]` with a 2-element convention. Avoid `Decimal` in RFQ (use `int` for USD cents or `float` for ranges). Test the schema before authoring the full prompt. [ASSUMED: gpt-5.4 follows the same subset constraints as gpt-4o-2024-08-06]

---

## NFKC Length-Change Gotchas

[VERIFIED: live Python 3.12 probe + unicodedata stdlib docs]

| Character | Unicode | NFKC result | Len change | Impact on offset map |
|-----------|---------|-------------|------------|---------------------|
| `ﬁ` (fi ligature) | U+FB01 | "fi" | 1→2 | `norm_to_orig[i]` = `norm_to_orig[i+1]` = orig_i |
| `ﬂ` (fl ligature) | U+FB02 | "fl" | 1→2 | Same as fi ligature |
| `½` (one half) | U+00BD | "1/2" | 1→3 | 3 norm chars all map to same orig_i |
| `μ` (micro sign) | U+00B5 | "μ" (U+03BC) | 1→1 | 1:1, but code point changes |
| `™` (trade mark) | U+2122 | "TM" | 1→2 | Both norm chars → orig_i |
| Full-width ASCII | U+FF01–U+FF5E | ASCII | 1→1 | 1:1 (code point changes only) |
| Combining marks (precomposed) | e.g., U+00E9 (é) | "é" (U+00E9) | 1→1 | No change; NFC/NFKC same here |
| NFD precomposed → composed | e.g., "e" + U+0301 | "é" | 2→1 | NFKC composes! Two orig chars map to one norm char — THIS IS THE REVERSE CASE |

**Reverse case (NFD decomposed → NFKC composed):** If the source text has "e" + combining acute (U+0301) as two separate code points, NFKC composes them to é (1 char). The `norm_to_orig` map in Pattern 2 handles this correctly because `stage1_to_orig[norm_i] = orig_i` of the BASE character; the combining mark's orig index is never inserted into the map (it's merged into the base char's NFKC output). The result is conservative — the offset points to the base char — which is acceptable for grounding.

**Summary:** The char-by-char `norm_to_orig` approach handles all cases correctly by construction. The only tricky case is NFD → NFC compositions (2 orig chars → 1 norm char), where the map naturally drops the combining mark's contribution (pointing both-or-just-one to the base char's orig index). This is correct since the evidence snippet will contain the composed form.

---

## Code Examples

### Grounding Gate: Core Logic Sketch

```python
# Source: Pattern 1-3 above (derived from rapidfuzz docs + Python stdlib)
from schemas.envelope import Field, FlagStatus, Evidence
from rapidfuzz.fuzz import partial_ratio_alignment

FUZZY_THRESHOLD = 90.0  # tuned in tests (D-03)
MIN_SNIPPET_LEN = 15     # Pitfall 3 guard — short snippets can't be reliably grounded

def ground_field(
    field: "Field[T]",
    sources: dict[str, str],
    field_path: str = "",
) -> tuple["Field[T]", list["DowngradeEntry"]]:
    """Ground one Field[T] against its source text. Return new field + downgrade entries."""
    if field.status in (FlagStatus.missing, FlagStatus.unsupported):
        return field, []  # already absent; nothing to ground

    if not field.evidence:
        # present/unclear/conflicting with no evidence — not our problem to downgrade here
        # (envelope validator should have caught this; pass through)
        return field, []

    new_evidence: list[Evidence] = []
    downgrade_entries: list[DowngradeEntry] = []

    for ev in field.evidence:
        source_text = sources.get(ev.source_id)
        if source_text is None:
            downgrade_entries.append(DowngradeEntry(field_path, ev, "source_id not in sources"))
            continue  # will trigger downgrade below

        grounded_ev = _ground_evidence(ev, source_text)
        if grounded_ev is not None:
            new_evidence.append(grounded_ev)
        else:
            downgrade_entries.append(DowngradeEntry(field_path, ev, "snippet not locatable"))

    if downgrade_entries:
        # Any failed evidence → downgrade entire field to unsupported
        return Field(status=FlagStatus.unsupported), downgrade_entries

    return field.model_copy(update={"evidence": new_evidence}), []
```

### RFQ Generation: Quick Test Sketch (DATA-01)

```python
# Verifies with_structured_output returns a valid RFQ instance
# Run once during development to confirm schema compatibility
from llm.factory import get_llm
from schemas.domain import RFQ

llm = get_llm("reasoning")
structured = llm.with_structured_output(RFQ, method="json_schema")
rfq: RFQ = structured.invoke("Generate a marketing services RFQ with 8 line items.")
assert isinstance(rfq, RFQ)
assert len(rfq.line_items) == 8
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `fuzzywuzzy.partial_ratio` (FuzzyWuzzy) | `rapidfuzz.fuzz.partial_ratio_alignment` | ~2020 (rapidfuzz v1.0) | 5–100× faster; MIT license (FuzzyWuzzy was GPL-conditional); `_alignment` variant adds offset return |
| pydantic v1 `__fields__` dict | pydantic v2 `model_fields` dict | Pydantic v2.0 (2023) | `model_fields` returns `FieldInfo`, not `ModelField`; walker uses `getattr(obj, name)` for values |
| pydantic v1 `.copy(update=...)` | pydantic v2 `.model_copy(update=...)` | Pydantic v2.0 (2023) | `.copy()` is deprecated in v2; use `.model_copy()` |

**Deprecated/outdated:**
- `fuzzywuzzy`: replaced by rapidfuzz; do not introduce as a dependency.
- pydantic v1 `__fields__`: use `model_fields` in this codebase (already on pydantic v2).
- Manual JSON-mode prompting for structured output: replaced by `with_structured_output(method="json_schema")`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | rapidfuzz fuzzy threshold of ~90 is a good starting point (D-03) | Fuzzy Fallback / Pitfall 3 | If too low: fabricated snippets pass grounding. If too high: legitimate fuzzy matches (minor typos, whitespace diffs) get downgraded. Calibrate in tests against real messy data. |
| A2 | gpt-5.4 follows the same OpenAI structured output JSON schema subset constraints as gpt-4o-2024-08-06 | Pitfall 6 | If gpt-5.4 has fewer constraints: no issue. If more: RFQ schema may need further simplification. Test with a schema smoke-call before full authoring. |
| A3 | Minimum snippet length of 15 chars guards against trivial fuzzy matches (Pitfall 3) | Pitfall 3 / Pattern 3 | If real evidence snippets are shorter than 15 chars: legitimate grounding fails. Review min-length against the actual extraction agent output in P3 and adjust. |
| A4 | NFD combining-mark sequences are rare in real vendor PDF-extracted text | NFKC Gotchas | If vendor PDFs contain lots of NFD text: the "base char origin tracking" behavior (combining mark dropped from map) is correct for grounding purposes but may cause a 1-char mismatch in the displayed highlight. Acceptable for P2; monitor in P5 with real file uploads. |
| A5 | `method="json_schema"` in with_structured_output works with the gpt-5.4 reasoning tier | Pattern 5 | If gpt-5.4 doesn't support json_schema mode via LangChain: fall back to `method="function_calling"`. Test at RFQ-gen authoring time. |

---

## Open Questions (RESOLVED)

1. **Minimum snippet length threshold (Pitfall 3)**
   - What we know: very short snippets score near-100 against any text via partial_ratio
   - What's unclear: what is the shortest real evidence snippet the extraction agent will produce? (Phase 3 concern)
   - Recommendation: Set minimum length to 15 chars for P2, mark with a `# ponytail:` comment explaining it's calibrated against P3 output, revisit in P3.

2. **RFQ line_items count enforcement**
   - What we know: D-11 specifies "8 line items" but the pydantic schema won't enforce `len(line_items) == 8` without a custom validator
   - What's unclear: should the schema enforce exactly 8, or treat 8 as a generation target?
   - Recommendation: For a 5-day prototype, treat 8 as a prompt instruction, not a hard schema constraint. Add `model_validator` only if tests show the model consistently produces the wrong count.

3. **Live-regen API surface (DATA-04) — HTTP vs CLI**
   - What we know: data must be regenerable in-app per DATA-04; existing `api/app.py` exposes FastAPI endpoints
   - What's unclear: should live regen be a GET endpoint (no RFQ input), a POST (accepts parameters), or a background task with SSE progress?
   - Recommendation: For P2, expose two simple GET endpoints (`/data/rfq`, `/data/vendor-gen`) that run synchronously. SSE is for extraction (P3); generation is fast enough to buffer. Mark as Claude's Discretion per CONTEXT.md.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All of services/ai | Check via `python3 --version` | Set in pyproject.toml `requires-python = ">=3.12"` | — |
| `uv` | Package management | Assumed (used in P1) | — | `pip` |
| `rapidfuzz` | Grounding gate (EXTRACT-04) | Not yet installed | 3.13.0 on PyPI | None — must be added via `uv add rapidfuzz` |
| `pydantic` ≥2.13.4 | All schemas | Already installed (pyproject.toml) | 2.13.4 | — |
| `langchain-openai` ≥1.3.3 | RFQ/vendor generation | Already installed | 1.3.3 | — |
| OpenAI API key | RFQ/vendor generation (DATA-01/02) | Confirmed in P1 (PLAT-03 ping) | — | None — required |

**Missing dependencies with no fallback:**
- `rapidfuzz` — must be added to `services/ai/pyproject.toml` before grounding gate implementation.

**Missing dependencies with fallback:**
- None.

---

## Validation Architecture

> `nyquist_validation: true` in `.planning/config.json` — section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥9.1.1 |
| Config file | `services/ai/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd services/ai && uv run pytest tests/test_grounding_gate.py -x -q` |
| Full suite command | `cd services/ai && uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXTRACT-04 — fabricated downgrade | A fabricated snippet (not in source text) is downgraded to `unsupported`, value suppressed | unit | `uv run pytest tests/test_grounding_gate.py::test_fabricated_span_is_downgraded -x` | ❌ Wave 0 |
| EXTRACT-04 — genuine passes | A genuine snippet present in source text keeps `status=present` and gets recomputed offsets | unit | `uv run pytest tests/test_grounding_gate.py::test_genuine_span_passes_grounding -x` | ❌ Wave 0 |
| EXTRACT-04 — offset recompute | Recomputed `char_start`/`char_end` point to a region that `source_text[start:end]` confirms contains the snippet | unit | `uv run pytest tests/test_grounding_gate.py::test_offsets_are_recomputed_not_trusted -x` | ❌ Wave 0 |
| EXTRACT-04 — conflicting field | A `Field[T]` with `status=conflicting` grounds each `ConflictingValue.evidence` independently | unit | `uv run pytest tests/test_grounding_gate.py::test_conflicting_field_grounded_per_value -x` | ❌ Wave 0 |
| EXTRACT-04 — fuzzy hit | A snippet with minor whitespace/normalization differences (real fuzzy match) grounds successfully above threshold | unit | `uv run pytest tests/test_grounding_gate.py::test_fuzzy_match_above_threshold_grounds -x` | ❌ Wave 0 |
| EXTRACT-04 — fuzzy miss | A snippet with score below threshold is downgraded | unit | `uv run pytest tests/test_grounding_gate.py::test_fuzzy_match_below_threshold_downgrades -x` | ❌ Wave 0 |
| EXTRACT-04 — NFKC ligature | A snippet containing `ﬁ` ligature is matched against source text with "fi" (and vice versa), offsets correct | unit | `uv run pytest tests/test_grounding_gate.py::test_nfkc_ligature_offset_mapping -x` | ❌ Wave 0 |
| EXTRACT-04 — walker | Recursive walker finds all `Field[T]` instances in a nested pydantic model and re-grounds each | unit | `uv run pytest tests/test_grounding_gate.py::test_walker_grounds_nested_fields -x` | ❌ Wave 0 |
| DATA-01 | `data/rfq.json` exists and deserializes to a valid `RFQ` instance with 8 line items | fixture | `uv run pytest tests/test_sample_fixtures.py::test_rfq_fixture_valid -x` | ❌ Wave 0 |
| DATA-02 | `data/vendor_*.json` files (×3) exist and deserialize to valid `VendorResponse` instances | fixture | `uv run pytest tests/test_sample_fixtures.py::test_vendor_fixtures_exist_and_valid -x` | ❌ Wave 0 |
| DATA-03 — persona messiness | Each persona fixture contains its declared issue types: thorough-but-pricey has bundled/over-scoped pricing; cheap-but-incomplete has missing line items and vague timelines; polished-fluff has internal conflicts | fixture + string | `uv run pytest tests/test_sample_fixtures.py::test_vendor_fixture_messiness -x` | ❌ Wave 0 |
| DATA-03 — missing price | Cheap-but-incomplete fixture has at least one line item with no price mention | fixture | `uv run pytest tests/test_sample_fixtures.py::test_cheap_incomplete_has_missing_price -x` | ❌ Wave 0 |
| DATA-03 — conflicting statement | Polished-fluff fixture contains two contradictory timeline/scope statements | fixture | `uv run pytest tests/test_sample_fixtures.py::test_polished_fluff_has_conflict -x` | ❌ Wave 0 |
| DATA-04 — codegen drift | After schema changes, pydantic2ts output matches committed TS types | codegen | `uv run pytest tests/test_codegen_drift.py -x` | ✅ (existing) |
| PROMPT-04 | rfq-gen, vendor-gen, messy-data-gen prompts load from registry without error | unit | `uv run pytest tests/test_prompt_registry.py -x` | ✅ (existing, covers load) |

### The Falsifiability Tests (Critical for Phase Goal)

Two tests MUST be written before any implementation:

**Test A — Fabricated span IS downgraded (success criterion 1):**
```python
def test_fabricated_span_is_downgraded():
    source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
    fabricated_evidence = Evidence(
        snippet="Vendor A proposes $99 for everything",  # not in source
        char_start=0, char_end=10, source_id="v1"
    )
    field = Field(
        status=FlagStatus.present,
        value="$99 for everything",
        evidence=[fabricated_evidence],
    )
    grounded, report = ground_field(field, {"v1": source})
    assert grounded.status == FlagStatus.unsupported
    assert grounded.value is None
    assert grounded.evidence == []
    assert len(report) == 1
```

**Test B — Genuine span survives (success criterion 2):**
```python
def test_genuine_span_passes_grounding():
    source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
    genuine_evidence = Evidence(
        snippet="$15,000 for strategy and creative",  # genuinely in source
        char_start=0, char_end=10,  # intentionally wrong — gate recomputes
        source_id="v1"
    )
    field = Field(
        status=FlagStatus.present,
        value=Decimal("15000"),
        evidence=[genuine_evidence],
    )
    grounded, report = ground_field(field, {"v1": source})
    assert grounded.status == FlagStatus.present
    assert grounded.value == Decimal("15000")
    assert len(grounded.evidence) == 1
    assert len(report) == 0
    ev = grounded.evidence[0]
    # Verify recomputed offsets actually point to the snippet
    assert source[ev.char_start:ev.char_end] == "$15,000 for strategy and creative"
```

### Sampling Rate
- **Per task commit:** `cd services/ai && uv run pytest tests/test_grounding_gate.py -x -q`
- **Per wave merge:** `cd services/ai && uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work 2`

### Wave 0 Gaps
- [ ] `tests/test_grounding_gate.py` — covers EXTRACT-04 (all gate unit tests above)
- [ ] `tests/test_sample_fixtures.py` — covers DATA-01, DATA-02, DATA-03 (fixture existence + messiness assertions)
- [ ] `grounding/__init__.py`, `grounding/gate.py`, `grounding/report.py` — module stubs for imports to resolve

*(Existing test infrastructure covers `tests/test_codegen_drift.py` and `tests/test_prompt_registry.py`)*

---

## Security Domain

> `security_enforcement` not explicitly set in config.json — treating as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in P2 (single-user prototype) |
| V3 Session Management | No | No sessions in P2 |
| V4 Access Control | No | No RBAC in P2 |
| V5 Input Validation | Yes | Source text inputs to grounding gate are validated as `str`; pydantic v2 enforces schema at model construction |
| V6 Cryptography | No | No crypto in P2 |
| V10 Malicious Code | Partial | OpenAI API key is in `.env` (gitignored); `llm/factory.py` never logs the key (T-03-01 from P1 carries forward) |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via vendor response text | Tampering | The grounding gate is LLM-free and operates on raw text — no prompt injection surface. Vendor text is never re-injected into a new LLM call during grounding. |
| Model-supplied `verified` flag bypasses grounding | Spoofing | D-01 / D-02: gate ignores model-supplied offsets entirely; all offsets are recomputed in code. This is the core CLAUDE.md §8 control. |
| Fabricated evidence snippet passes fuzzy threshold | Spoofing | Threshold at ~90 + minimum snippet length guard (Pitfall 3) + falsifiability tests ensure fabricated spans are caught. |
| Path traversal via `source_id` key | Tampering | `sources` is a `dict[str, str]` passed by the caller — not a filesystem path. `source_id` is a lookup key only. |

---

## Sources

### Primary (HIGH confidence)
- `/websites/rapidfuzz_github_io_rapidfuzz` (Context7) — `partial_ratio_alignment`, `partial_ratio`, `Indel.editops`, changelog
- `github.com/rapidfuzz/RapidFuzz/blob/main/src/rapidfuzz/distance/_initialize.pyi` (official type stub) — `ScoreAlignment` fields confirmed: `score`, `src_start`, `src_end`, `dest_start`, `dest_end`
- `/pydantic/pydantic` (Context7 HIGH) — `model_fields`, nested model iteration, `model_copy(update=...)`
- `/websites/langchain_oss` (Context7 HIGH) — `with_structured_output`, `method="json_schema"`, `ChatOpenAI.invoke()`
- Python stdlib `unicodedata` docs (official) — NFKC normalization behavior
- Live Python 3.12 probe (2026-06-27) — NFKC ligature expansion confirmed (`ﬁ` → "fi", 1→2), two-stage offset map tested end-to-end

### Secondary (MEDIUM confidence)
- `pypistats.org/packages/rapidfuzz` — ~25M weekly downloads (verified via WebSearch)
- `rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html` — current stable version 3.14.5 (docs); PyPI latest 3.13.0 (pip index)
- `discuss.python.org/t/get-changed-offsets-of-unicode-normalization/14085` — confirmed that Python stdlib has no built-in offset-tracking normalization; char-by-char incremental approach is the community recommendation

### Tertiary (LOW confidence)
- A2 (gpt-5.4 structured output subset constraints): extrapolated from gpt-4o behavior documented by OpenAI; not tested with actual gpt-5.4 API call.

---

## Metadata

**Confidence breakdown:**
- Offset remapping (D-04): HIGH — live-tested with Python 3.12, NFKC expansion confirmed, two-stage map algorithm verified
- rapidfuzz API (D-03): HIGH — type stub inspected, `ScoreAlignment` fields confirmed, Context7 HIGH source
- pydantic v2 walker (D-05): HIGH — Context7 HIGH source, `model_fields` pattern confirmed
- LangChain structured output (D-11): HIGH — Context7 HIGH source, `with_structured_output` documented
- RFQ schema design (D-11): MEDIUM — no incompatibility found, but gpt-5.4 JSON schema subset not live-tested
- Fuzzy threshold tuning (D-03): LOW (A1) — starting point from D-03, must be calibrated in tests
- Messiness assertion patterns: HIGH — deterministic committed fixtures + string search are simple and reliable

**Research date:** 2026-06-27
**Valid until:** 2026-07-27 (stable ecosystem; rapidfuzz, pydantic v2, and LangChain APIs are stable)
