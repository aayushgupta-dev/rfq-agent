---
phase: 1
slug: foundation
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-27
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Verify-only pass — register authored at plan time across plans 01-01..01-04; each declared
> mitigation verified present in implemented code. No new-threat scan, no implementation edits.

**Result: SECURED.** All 14 registered threats resolve (9 MITIGATE verified CLOSED in code,
5 ACCEPT rationales confirmed against current code and logged). `threats_open: 0`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| install-time → repo | npm + PyPI dependency resolution introduces third-party code (supply-chain surface) | package code / lockfiles |
| pydantic schema → generated TS | codegen shells out to json2ts; the generated `index.d.ts` is a committed build artifact consumed by apps/web | structural type definitions (no secrets) |
| process env / `.env` → AI service | `OPENAI_API_KEY` (a secret) enters the service; the access ping crosses out to the OpenAI API | API key (secret), model IDs |
| HTTP client → `GET /stream/demo` | unauthenticated local request triggers a streamed graph run (Phase 1 local-only; no auth by design) | hardcoded taxonomy events (no model call) |
| prompt `.md` files → registry | first-party authored source files parsed as data (no external/untrusted input in Phase 1) | prompt intent/TODO stubs (no secrets) |
| `prompt_id` argument → `_find_latest` glob | `prompt_id` validated against `^[a-z0-9-]+$` before use in a filename glob (path-traversal guard) | caller-supplied identifier |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Tampering | npm/PyPI dependency installs | mitigate | `pnpm-lock.yaml` + `services/ai/uv.lock` present and git-tracked (`git ls-files` confirms); pinned resolved versions enforce reproducible installs. | closed |
| T-01-02 | Information Disclosure | `.gitignore` coverage of dep/env dirs | accept | `.gitignore:32,59,77` cover `node_modules/`, `__pycache__/`, `.venv/`; no secrets handled in plan-01 scaffold. | closed |
| T-01-SC | Tampering | npm/pip/uv installs (slopcheck unavailable in research env) | mitigate | Same committed lockfiles as T-01-01; RESEARCH-"Approved" version-pinned stack; no new installs introduced post-plan-01 — reproducibility enforced by the committed lockfiles. | closed |
| T-02-01 | Tampering | stale/hand-edited `packages/shared-types/index.d.ts` (contract drift) | mitigate | `services/ai/tests/test_codegen_drift.py:31-43` regenerates into a `tempfile.TemporaryDirectory` and asserts byte-equality (`assert generated_text == committed_text`) against the committed `index.d.ts`. Live re-run of `scripts/codegen.py` + `git diff --exit-code` = CLEAN. | closed |
| T-02-02 | Tampering | json2ts binary invocation path | accept | `node_modules/.bin/json2ts` present/executable; `scripts/codegen.py:82` resolves it by explicit path via `repo_root()`; first-party schemas only; pinned json-schema-to-typescript@15 (lockfile). | closed |
| T-02-03 | Information Disclosure | schema content in generated TS | accept | `schemas/domain.py` stubs are structural placeholders; generated `index.d.ts` contains only type shapes, no secrets/PII. | closed |
| T-02-04 | Tampering | `Field[T]` model_validator bypass | mitigate | `schemas/envelope.py:105-156` — `@model_validator(mode="after") _validate_absence_semantics`; mode="after" runs on every instantiation incl. `model_validate` (dict-construction path); cannot be bypassed. `tests/test_field_envelope.py` exercises invalid combos via `pytest.raises(ValidationError)` — 66 schema tests pass. | closed |
| T-03-01 | Information Disclosure | `OPENAI_API_KEY` in `.env`, ping errors, startup logs | mitigate | Grep across `llm/factory.py`, `scripts/verify_access.py`, `api/app.py`: only `OPENAI_API_KEY` references are security-comment lines (`factory.py:107`, `verify_access.py:16`); no code path interpolates the key into any message/log — logs reference model IDs + pass/fail only (`factory.py:118,134`). `.env` gitignored (`.gitignore:9-12`), only `.env.example` committed (empty `OPENAI_API_KEY=`); no `.env` tracked. | closed |
| T-03-02 | Denial of Service | unauthenticated `GET /stream/demo` | accept | `api/app.py:46-66` has no auth dependency (no `Depends`/`Security`/`Authorization`); stream emits hardcoded taxonomy via `demo_graph.astream(...)` with NO model call. Local-only single-buyer prototype; auth out of scope (REQUIREMENTS). **Revisit at Phase 5 / SHIP-01 when CORS + public deploy land.** | closed |
| T-03-03 | Spoofing | wrong/over-tier model silently used (e.g. gpt-5.5) | mitigate | `llm/factory.py:37-40` `_TIER_ENV` maps tier→env var; `factory.py:82` `init_chat_model(model_id)` is the sole call site (grep confirms `MODEL_REASONING`/`MODEL_CHEAP`/`init_chat_model` in no non-test file). `get_llm` rejects unknown tier (`ValueError`:72) and unset env (`RuntimeError`:77); callers pass a tier literal, never a model string. Only `5.5` occurrence is the never-5.5 enforcement comment (`factory.py:11`). | closed |
| T-03-SC | Tampering | langchain/langgraph/sse-starlette installs | mitigate | Installed in plan 01 from the version-pinned, RESEARCH-"Approved" stack; reproducibility via committed `services/ai/uv.lock` (same lockfile evidence as T-01-SC). No new installs in plan 03. | closed |
| T-04-01 | Tampering | YAML frontmatter parsing of `.md` prompts | mitigate | `prompts/registry.py:20,68` uses `python-frontmatter` (`frontmatter.load`) — safe YAML loading. No `yaml.load`/`Loader`/`UnsafeLoader`/`FullLoader` anywhere under `prompts/`. Files parsed are first-party committed `.md` source. | closed |
| T-04-02 | Information Disclosure | prompt bodies/frontmatter | accept | 7 prompt stubs (`prompts/*.v1.md`) are intent/TODO placeholders intended for the public Prompt Pack; no secrets/PII. | closed |
| T-04-03 | Elevation of Privilege | path traversal via `prompt_id` in glob | mitigate | `prompts/registry.py:65-66` — `load()` runs `re.fullmatch(r"^[a-z0-9-]+$", prompt_id)` and raises `ValueError` BEFORE `_find_latest` (the glob/filesystem use at line 67). `"../etc/passwd"`/`"foo bar"` rejected; covered by `test_prompt_registry.py` invalid-id cases. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-02 | `.gitignore` covers dep/env dirs; no secrets in plan-01 scaffold. | Aayush Gupta | 2026-06-27 |
| AR-02 | T-02-02 | json2ts invoked by explicit path; first-party schemas only; pinned binary. | Aayush Gupta | 2026-06-27 |
| AR-03 | T-02-03 | Generated TS is structural stubs — no secrets/PII. | Aayush Gupta | 2026-06-27 |
| AR-04 | T-03-02 | Unauthenticated `GET /stream/demo`; local-only, no model call on stream path; auth deferred to Phase 5 (CORS + deploy). | Aayush Gupta | 2026-06-27 |
| AR-05 | T-04-02 | Prompt bodies/frontmatter are public-Prompt-Pack stubs — no secrets/PII. | Aayush Gupta | 2026-06-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

None. Every `## Threat Flags` section in the four SUMMARY files (01-01..01-04) explicitly states
"no new threat surface" and maps observed surface back to registered threat IDs. No new attack
surface appeared during implementation without a threat mapping.

Note: SUMMARY 01-02 documents a post-plan gap-closure (CR-01/CR-02/CR-03) that *strengthened*
T-02-04 / PLAT-01 grounding enforcement (evidence-non-empty checks, Evidence offset validation) —
verified present at `envelope.py:59-69` and `:142-154`. This hardens an already-CLOSED threat;
not a new flag.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-27 | 14 | 14 | 0 | gsd-security-auditor (verify-only; orchestrated by /gsd:secure-phase 1) |

---

## Implementation files reviewed (READ-ONLY — not modified)

- `pnpm-lock.yaml`, `services/ai/uv.lock`, `.gitignore`, `.env.example`
- `services/ai/scripts/codegen.py`, `services/ai/tests/test_codegen_drift.py`, `packages/shared-types/index.d.ts`
- `services/ai/schemas/envelope.py`, `services/ai/tests/test_field_envelope.py`
- `services/ai/llm/factory.py`, `services/ai/scripts/verify_access.py`, `services/ai/api/app.py`
- `services/ai/prompts/registry.py`, `services/ai/tests/test_prompt_registry.py`

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-27
