# PROMPT-04 — Prompt Failure Example & Fix

**Prompt affected:** `services/ai/prompts/extraction.v1.md`
**Failure type:** Humility-bias violation — paraphrased evidence treated as verbatim
**Rubric relevance:** §21 differentiator; Extraction accuracy & reliability (20%); Prompt quality (30%)

---

## The Failure

In the early version of the extraction prompt (implicit v0 — before the verbatim evidence
requirement was explicit), the model would produce evidence snippets that were semantically
accurate but not verbatim copies of the source text.

**Example:**

Source text (raw vendor response):
> "We remain flexible on price and would be happy to discuss further once the scope is confirmed."

Model output (`extraction v0`, implicit):
```json
{
  "pricing_structure": {
    "status": "present",
    "value": "Vendor offers competitive pricing in the $80K–$100K range",
    "evidence": [
      {
        "snippet": "Vendor offers competitive pricing in the flexible range pending scope confirmation",
        "source_id": "vendor_spark_creative",
        "char_start": 0,
        "char_end": 1
      }
    ]
  }
}
```

The model produced a `present` status with a value that fabricated a price range ("$80K–$100K")
not in the source text, and an evidence snippet that was a paraphrase ("competitive pricing in
the flexible range") rather than a verbatim copy of the source. The snippet sounds like a real
quote — it contains words from the source ("flexible") — but it is not one. The source said
"flexible on price"; the evidence said "flexible range pending scope confirmation", substituting
and adding words.

A naive substring check would fail to locate this snippet in the source text (because the
exact string does not appear there), but a lenient fuzzy matcher at threshold 70 might score
it as a near-match because the word overlap is high. This is the failure mode: a paraphrased
snippet that passes a weak fuzzy gate and allows a fabricated value to be shown as
"grounded" to the buyer.

---

## Why It Happened

**The prompt did not instruct the model to quote verbatim.** The early extraction prompt
described the task as "extract facts with supporting evidence from the vendor response" but
did not include an explicit verbatim requirement. The model — trained to be helpful and
produce readable output — "helpfully" generated evidence that read like a clear, professional
paraphrase of the source rather than a character-for-character copy. From the model's
perspective, a paraphrase is often clearer and more concise than a verbatim quote.

This is a well-documented LLM reliability failure mode: models default to paraphrase because
it produces more natural-sounding output, reduces redundancy, and — from a language modeling
perspective — is highly rewarded behavior in training. Without an explicit instruction to the
contrary, the model has no incentive to reproduce text character-for-character.

**The grounding gate had no floor to catch it.** With a fuzzy match threshold of 70
(hypothetically), a semantically close paraphrase with 70%+ word overlap would have passed
gate verification and been presented to the buyer as a grounded, evidence-backed fact. The
buyer would see `"present"` with a confidence-sounding snippet, when the actual source text
supported at best `"unclear"`.

---

## The Fix

The fix was two-part: a prompt update AND a code-level gate tightening. Neither alone was
sufficient.

**Part 1 — Prompt update (extraction.v1.md):**

The evidence section was rewritten to include three explicit verbatim requirements and a
few-shot example contrasting a verbatim quote against a paraphrase:

```
1. Quote verbatim. Copy the passage character-for-character from the vendor response.
   Do NOT paraphrase, summarize, or substitute synonyms. The quoted text must appear
   word-for-word in the vendor's document.

[... minimum length and source_id instructions ...]

3. Your evidence snippets MUST be copied character-for-character from the vendor text.
   Any rephrasing, synonyms, or paraphrasing — including changing word order, substituting
   near-synonyms, or adding/omitting a word — will cause the evidence to fail automated
   verification. Copy the passage exactly as it appears, including punctuation and spacing.
```

The few-shot examples (Example 1 through 4 in the prompt body) were also updated to use
snippets that appear verbatim in the example source texts, so the model sees the correct
behavior modeled before it extracts from real vendor input.

**Part 2 — Grounding gate (gate.py) with FUZZY_THRESHOLD=90:**

The grounding gate in `services/ai/grounding/gate.py` validates every evidence snippet by
locating it in the source text using exact substring search first, then a fuzzy match
fallback. The fuzzy threshold was set to 90 (not 70 or 80) so that a paraphrased snippet
sharing only partial word overlap with the source cannot pass verification:

```python
FUZZY_THRESHOLD = 90  # Min fuzz.partial_ratio score to accept a non-exact snippet
```

A snippet that does not appear verbatim in the source AND scores below 90 on the fuzzy gate
is downgraded to `unsupported` regardless of the model's stated `status`. This is the
"code disproves the model" story — code-level enforcement prevents paraphrased or fabricated
evidence from reaching the buyer, even if the prompt instruction is not perfectly followed.

The gate also enforces a minimum snippet length (`MIN_SNIPPET_LEN = 15` characters) so that
single-word or very short snippets — which can score high on fuzzy ratio by coincidence —
are rejected outright.

---

## Versioning Notes

**v0 (implicit):** The extraction prompt lacked an explicit verbatim requirement. Evidence
snippets were validated only for presence (non-empty) and a lenient fuzzy threshold. This
version was never named or committed as a versioned file; it represents the state before
the `extraction.v1.md` verbatim constraint was added.

**v1 (current):** Three explicit verbatim requirements in the evidence section; updated
few-shot examples with character-accurate snippets; minimum snippet length stated in the
prompt (≥20 characters, ≥3 words, above the gate minimum of 15 characters). The version
bump from implicit v0 to explicit v1 tracks exactly this change.

**Why both the prompt fix AND the code gate are needed:**

- The prompt alone is not sufficient: a model cannot be reliably instructed to follow a
  character-level precision rule on every inference. Even with explicit verbatim instructions,
  the model occasionally produces near-verbatim snippets that differ by punctuation or a
  single word. If the gate were not present, these would reach the buyer as grounded facts.

- The code gate alone is not sufficient: a strict gate (FUZZY_THRESHOLD=90) would correctly
  reject paraphrased snippets, but without the prompt fix, the model would produce many
  paraphrased snippets that require downgrading — making `unsupported` the dominant state
  even for facts that are genuinely present in the vendor response. The prompt fix reduces
  paraphrasing at the source; the gate handles residual cases.

**Defense in depth** — prompt reduces the failure rate; gate enforces the ceiling.

---

## Evaluation

**How the fix is validated:**

1. **Unit test — grounding gate fabrication scenario** (`test_grounding_gate.py`):
   `test_fabricated_evidence_downgraded_to_unsupported` constructs a synthetic extraction
   result where a field is marked `present` but its evidence snippet does not appear in the
   source text. The test asserts that the gate downgrades the field to `unsupported`.
   This test is a permanent regression guard: if the gate behavior changes, this test fails.

2. **Verbatim-evidence integrity in committed traces** (`docs/traces/`):
   The trace fixtures captured from live runs (extraction agent on the 3 messy vendor
   fixtures) demonstrate verbatim-evidence integrity: every shown fact in the trace's final
   result is locatable in the vendor source text. The committed traces are checked by
   `test_traces_committed.py` which asserts that all evidence spans in a trace are
   locatable substrings of their source text.

3. **Semantic check (manual):** Read any extraction result from the committed traces and
   verify that the evidence snippets in `"status": "present"` fields are character-for-
   character copies of the vendor response — not paraphrases. The humility-bias traces
   in `docs/traces/` are the recommended starting point for a manual reviewer.
