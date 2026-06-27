---
phase: 03
slug: extraction-agent
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-28
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Mitigations verified against implementation code. Accept dispositions documented in Accepted Risks Log.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| POST /extract/vendor | HTTP request body from any caller | VendorResponse.raw_text (untrusted vendor prose), RFQ fields |
| SSE response stream | Agent-to-client event stream | Structured extraction facts, grounding report, error payloads |
| LLM API | FastAPI service → OpenAI | Prompt (system + human), model output |
| Trace capture | scripts/capture_traces.py → docs/traces/ | Vendor raw_text previews, ungrounded + grounded extraction output |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-W0-01 | Tampering | test import block | accept | Wave 0 test-only; no trust boundary crossed; no user input | CLOSED |
| T-03-W0-SC | Tampering | pip installs (wave 0) | accept | No new packages introduced | CLOSED |
| T-03-02-01 | Information Disclosure | ExtractionResult.vendor_name | mitigate | vendor_name declared `str` at domain.py:147; gate.py has no reference to vendor_name (grep confirmed) | CLOSED |
| T-03-02-02 | Tampering | dict[str,Field] shapes | mitigate | No `dict[str, Field]` annotation in domain.py (grep: only comment reference at line 142); all multi-claim fields are list[Field[T]] or list[BaseModel] | CLOSED |
| T-03-02-SC | Tampering | pip installs (schema) | accept | No new packages introduced | CLOSED |
| T-03-03-01 | Tampering/Spoofing | Prompt injection via vendor raw_text | mitigate | System prompt wrapped in `SystemMessage(content=...)` (extraction.py:54) — LangChain f-string parsing suppressed. `vendor_text` injected only in human turn (extraction.py:57). raw_text never appears in SystemMessage content | CLOSED |
| T-03-03-02 | Information Disclosure | Model fabricating grounded claims | mitigate | `ground_model()` called at extraction.py:213, BEFORE `emit(result_event)` at extraction.py:232; result event only carries grounded output | CLOSED |
| T-03-03-03 | DoS | Oversized vendor raw_text | mitigate | `ExtractionRequest._check_payload_size` validator (app.py:124–136): raw_text capped at 200,000 chars; aggregate request capped at 500,000 chars | CLOSED |
| T-03-03-04 | Information Disclosure | Sensitive data in error SSE events | mitigate | `ErrorPayload` carries only `code`, `message`, `recoverable` (events.py:33–35); `extra="forbid"` (events.py:31). factory.py logs only model_id, never OPENAI_API_KEY (factory.py:122,138) | CLOSED |
| T-03-03-05 | Tampering | Truncated output parsed as valid | mitigate | `LengthFinishReasonError` caught at extraction.py:130 before any parse attempt; emits `extraction_truncated` error event (extraction.py:135) and returns early | CLOSED |
| T-03-03-06 | Tampering | Refusal mistaken for ValidationError | mitigate | Refusal detected via `raw_msg.additional_kwargs.get("refusal")` (extraction.py:148); explicit comment at extraction.py:145 confirms NOT keyed off `str(ValidationError)` | CLOSED |
| T-03-03-07 | Tampering | Half-parsed/None object reaching result path | mitigate | CR-01 verified: `model_copy` (line 202), `ground_model` (line 213), `emit(result_event)` (line 232) are all inside the outer `try` block (lines 117–249); bare `except Exception` at line 236 maps every success-path failure to a safe error event | CLOSED |
| T-03-03-SC | Tampering | pip installs (agent + route) | accept | No new packages introduced | CLOSED |
| T-03-04-01 | Tampering | Staged/fabricated traces | mitigate | capture_traces.py imports and calls `generate_extraction_with_trace` exclusively (capture_traces.py:30,51); `raw_ungrounded` recorded at capture_traces.py:83 under `raw_model_output` key before grounding step | CLOSED |
| T-03-04-02 | Information Disclosure | Vendor raw_text in committed traces | accept | Generated sample data, no real PII; committed as submission artifact per plan decision | CLOSED |
| T-03-04-03 | Repudiation | Prompt version drift | mitigate | `resolved_prompt` block captures `id` (capture_traces.py:78), `version` (capture_traces.py:79), `system_message` (capture_traces.py:80) at trace time via `load("extraction")` (capture_traces.py:56); extraction.py uses `load("extraction")` (extraction.py:48) | CLOSED |
| T-03-04-04 | Information Disclosure | API key in trace/script output | mitigate | factory.py logs only model_id, never API key value (factory.py:122,138; confirmed no `OPENAI_API_KEY` reference in capture_traces.py); grep of capture_traces.py print/log statements shows no key/api/secret/token | CLOSED |
| T-03-04-05 | Tampering | FUZZY_THRESHOLD lowered to manufacture downgrade | mitigate | `FUZZY_THRESHOLD: float = 90.0` in gate.py:32 (unchanged from Phase 2); capture_traces.py explicitly forbids threshold lowering at lines 11–15 and 258 | CLOSED |
| T-03-04-SC | Tampering | pip installs (prompt + traces) | accept | No new packages introduced | CLOSED |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-W0-01 | Wave 0 is test-only code; no user input is processed, no trust boundary is crossed. Risk is build-time only. | gsd-security-auditor (plan-time register) | 2026-06-28 |
| AR-03-02 | T-03-W0-SC | No packages were added in Wave 0. Supply-chain risk surface is unchanged from Phase 2 baseline. | gsd-security-auditor (plan-time register) | 2026-06-28 |
| AR-03-03 | T-03-02-SC | No packages were added in the schema wave. Supply-chain risk surface is unchanged from Phase 2 baseline. | gsd-security-auditor (plan-time register) | 2026-06-28 |
| AR-03-04 | T-03-03-SC | No packages were added in the agent/route wave. Supply-chain risk surface is unchanged from Phase 2 baseline. | gsd-security-auditor (plan-time register) | 2026-06-28 |
| AR-03-05 | T-03-04-02 | All vendor text in docs/traces/ is generated sample data created by the vendor-gen agent. No real vendor PII or commercially sensitive data is present. Committed as a graded submission artifact (docs/ is the submission package per CLAUDE.md §14). | gsd-security-auditor (plan-time register) | 2026-06-28 |
| AR-03-06 | T-03-04-SC | No packages were added in the prompt/traces wave. Supply-chain risk surface is unchanged from Phase 2 baseline. | gsd-security-auditor (plan-time register) | 2026-06-28 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

None. All `## Threat Flags` sections in the four SUMMARY files either declare "None" (03-01) or map explicitly to registered threat IDs (03-02 maps to T-03-02-01/T-03-02-02; 03-03 maps to T-03-03-01 through T-03-03-07). No unregistered attack surface appeared during implementation.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-28 | 20 | 20 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-28
