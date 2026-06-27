# SECURITY.md — Phase 02: Grounding Gate & Messy Data

**Audit date:** 2026-06-27
**Phase:** 02 — grounding-gate-messy-data
**Plans audited:** 02-01, 02-02, 02-03, 02-04
**ASVS level:** 1 (prototype; no ASVS level declared in config — defaulting to 1 per scope)
**Auditor stance:** FORCE — every mitigation assumed absent until grep-confirmed in implementation.

---

## Threat Register — Verdict Summary

| Threat ID | Plan | Category | Disposition | Verdict | Evidence |
|-----------|------|----------|-------------|---------|----------|
| T-02-01 | 02-01 | Spoofing | accept | CLOSED | Accepted: stubs raise NotImplementedError; no code path trusts model output. Real mitigation landed in 02-02 (T-02-03/04). |
| T-02-02 | 02-01 | Tampering | mitigate | CLOSED | `services/ai/tests/test_sample_fixtures.py:18` — `_DATA_DIR = repo_root() / "data"` (hardcoded, never user-supplied) |
| T-02-SC (01) | 02-01 | Tampering | accept | CLOSED | No new installs in 02-01 — accepted. |
| T-02-03 | 02-02 | Spoofing | mitigate | CLOSED | `gate.py:4` docstring: "Ignores model-supplied char_start/char_end (D-01)". `_ground_evidence_item` never reads `ev.char_start`/`ev.char_end` — offsets are computed exclusively via `orig_indices` from `_normalize_with_map` + `_match_exact`/`_match_fuzzy`. Grep confirms zero occurrences of `ev.char_start` or `ev.char_end` in gate.py. |
| T-02-04 | 02-02 | Spoofing | mitigate | CLOSED | `schemas/envelope.py` contains no `grounded`, `verified`, or `is_verified` field. Gate operates only on `ev.snippet` vs source text — no model-asserted authorization flag exists in the schema or is consulted anywhere in gate.py. |
| T-02-05 | 02-02 | Spoofing | mitigate | CLOSED | `gate.py:37`: `MIN_SNIPPET_LEN: int = 15`. `_ground_evidence_item:189`: `if len(ev.snippet) < MIN_SNIPPET_LEN: return None, DowngradeEntry(...)`. Combined with `FUZZY_THRESHOLD = 90.0` at line 32. Both guards are in the only code path that processes evidence. |
| T-02-06 | 02-02 | Tampering | accept | CLOSED | Accepted: gate is LLM-free; vendor text processed by `unicodedata` + string comparison only. No exec/eval/subprocess surface confirmed (grep returned empty). |
| T-02-07 | 02-02 | Tampering | accept | CLOSED | Accepted: `sources` is a `dict[str, str]`; `source_id` is used only as a dict key (`sources.get(ev.source_id)`), never as a filesystem path. |
| T-02-SC (02) | 02-02 | Tampering | mitigate | CLOSED | `services/ai/pyproject.toml:16`: `"rapidfuzz>=3.14.5"` — package is PyPI-verified, MIT-licensed. |
| T-02-08 | 02-03 | Info Disclosure | accept | CLOSED | Accepted: prompt files contain no secrets or API keys. Confirmed by grep against `services/ai/prompts/`. |
| T-02-09 | 02-03 | Tampering | mitigate | CLOSED | `services/ai/tests/test_codegen_drift.py:28-39` — regenerates `index.d.ts` in a temp dir and diffs against committed output. Test fails if schema changes without re-running codegen. |
| T-02-10 | 02-03 | Spoofing | mitigate | CLOSED | (1) `vendor-gen.v1.md:119`: "Do not reference real living persons, named award shows..." anti-hallucination clause present. (2) `vendor_gen.py:41-179`: `MESS_SPECS` typed as `dict[str, list[MessSpecItem]]` — no `list[dict]` injection surface. (3) Mess specs are hand-authored constants in code, not runtime user input. |
| T-02-SC (03) | 02-03 | Tampering | accept | CLOSED | No new installs in 02-03 — accepted. |
| T-02-11 | 02-04 | Tampering | mitigate | CLOSED | `api/app.py:86-90`: `if req.persona not in MESS_SPECS: raise HTTPException(status_code=400, ...)` executes before any LLM call. `VendorGenRequest.persona` also has `max_length=64` (line 60) enforced by pydantic at request parse time. Persona is used only as a dict key (`MESS_SPECS[req.persona]`), never as a path or shell fragment. |
| T-02-12 | 02-04 | Info Disclosure | mitigate | CLOSED | (1) `.gitignore`: `.env` / `.env.*` patterns present; confirmed not tracked by `git ls-files`. (2) `factory.py:74-79`: `RuntimeError` message references only `env_var` name and `tier`, never the key value. `model_id` (not the key) appears in error strings. (3) `generate_samples.py:48`: error message prints `{e}` from the exception, not the key. API key is never passed as an explicit string argument to LangChain — it is read from environment internally by the OpenAI SDK, which does not embed the key in exception `str()`. (4) `factory.py:14-16` docstring: "no code path in this module interpolates the API key into any message, log, or exception string." |
| T-02-13 | 02-04 | Spoofing | accept | CLOSED | Accepted: vendor text is test data for the grounding gate; fabricated claims are intentional and gate validates them before display. |
| T-02-14 | 02-04 | Denial of Service | accept | CLOSED | Accepted: synchronous LLM calls for prototype scope; no production SLA. |
| T-02-15 | 02-04 | Tampering | accept | CLOSED | Accepted: `rfq_text` is caller-supplied context to an LLM; no external untrusted party has access in this prototype. |
| T-02-SC (04) | 02-04 | Tampering | accept | CLOSED | No new installs in 02-04 — accepted. |

**Totals: 18/18 CLOSED — 0 OPEN**

---

## Grounding Integrity — Keystone Verification

The headline security property of this phase is that the grounding gate recomputes evidence offsets from source text and never trusts model-supplied values. Verification by code path:

1. **Model-supplied offsets discarded at entry:** `_ground_evidence_item` receives an `Evidence` object but never reads `ev.char_start` or `ev.char_end`. Grep over gate.py returns zero matches for those field accesses. The only offset reads are `orig_indices[...]` computed by `_normalize_with_map`.

2. **Recomputed offsets only:** `_match_exact` and `_match_fuzzy` both return `(char_start, char_end)` computed from `orig_indices` derived from the actual source text. These replace the incoming evidence offsets unconditionally on a match.

3. **Downgrade on miss:** If neither exact nor fuzzy match finds the snippet, `_ground_evidence_item` returns a `DowngradeEntry` and `ground_field` returns `EnvelopeField(status=FlagStatus.unsupported)` — suppressing `value` and `evidence` entirely (enforced by the envelope schema's `model_validator`).

4. **No "verified" bypass:** The `Evidence`, `Field`, and `FlagStatus` schemas contain no `grounded`, `verified`, or `is_verified` field. There is no flag the model could set to bypass the gate.

---

## Secret Handling — Verification

- `.env` is gitignored (`.gitignore` line: `.env` / `.env.*`) and confirmed absent from `git ls-files`.
- `factory.py` reads `OPENAI_API_KEY` via `os.environ.get(env_var)` — the key value is assigned to a local variable that is never interpolated into any error string, log call, or exception message.
- Error messages in `factory.py` reference `model_id` (e.g. `"gpt-5.4"`) and `tier` (e.g. `"reasoning"`), not the key value.
- `generate_samples.py` exception handler prints `{e}` from the LangChain/OpenAI SDK exception. The OpenAI SDK's `AuthenticationError` says "Incorrect API key provided" — it does not embed the key value in the exception string. The key is never passed as an explicit string argument to any LangChain call.
- No `sk-` or `OPENAI_API_KEY=` values found in `data/`, `services/ai/prompts/`, or any tracked file.

---

## API Endpoint Safety — Verification

**POST /data/vendor-gen (T-02-11):**
- Pydantic enforces `max_length=64` on `persona` and `max_length=200_000` on `rfq_text` at request parse time, before the handler runs.
- `if req.persona not in MESS_SPECS` check fires before any LLM call or dict access.
- `persona` is used only as a dict key; it is never passed to shell, eval, exec, or filesystem path construction.
- No `eval`, `exec`, `subprocess`, or `os.system` calls in `app.py`, `rfq_gen.py`, or `vendor_gen.py` (grep confirmed empty).

**Prompt-injection surface (rfq_text → vendor-gen LLM):**
- `rfq_text` is forwarded into an LLM prompt via LangChain template substitution. This is an accepted risk (T-02-15) because: the endpoint generates sample data with no privileged decisions or downstream code execution; the caller in normal use is the app's own `/data/rfq` endpoint; and no external untrusted party has access to the prototype service.
- This risk is correctly scoped — it would require reassessment if the service were exposed publicly or if LLM output were used in a privileged context.

**CORS / rate-limiting:**
- Not implemented in Phase 2. Deferred to Phase 5 (SHIP-01) as declared in the `app.py` docstring. Not a blocker for this phase audit.

---

## Unregistered Threat Flags

No `## Threat Flags` section was present in the SUMMARY.md files for 02-01 through 02-04.

One surface warrants noting as an informational flag (not a blocker — no threat mapping exists):

**UNREGISTERED — UF-02-01 — LangChain exception string in generate_samples.py error output:**
`generate_samples.py:48` prints `{e}` from a caught `Exception`. This is safe for the API key (SDK does not embed the key), but could expose internal model IDs, endpoint URLs, or other diagnostic detail to the terminal. For a developer CLI tool this is acceptable; for a production service it would warrant sanitisation. No action required for this prototype scope.

---

## Accepted Risks Log

| Threat ID | Risk | Rationale |
|-----------|------|-----------|
| T-02-01 | Stubs raise NotImplementedError | Wave 0 test harness only; real mitigation in T-02-03/04 |
| T-02-06 | Vendor text via unicodedata/string comparison | Gate is LLM-free; no code execution surface |
| T-02-07 | source_id as dict key | Never used as filesystem path |
| T-02-08 | Prompts in source control | No secrets in prompt files |
| T-02-13 | Fabricated vendor claims in test data | Intentional — gate validates before display |
| T-02-14 | Slow synchronous LLM calls | Prototype scope; no production SLA |
| T-02-15 | rfq_text injection into vendor-gen LLM | Generation-only endpoint; no external untrusted access; no privileged decisions |
| T-02-SC (01,03,04) | No new package installs | All deps already in pyproject.toml |
