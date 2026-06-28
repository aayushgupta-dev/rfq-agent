---
phase: 05
slug: buyer-ui-trace-submission
status: verified
threats_open: 0
asvs_level: prototype
created: 2026-06-28
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (all 9 PLAN files carry a `<threat_model>` block) — COMPLETE.
> Audit mode: verify each `mitigate` mitigation EXISTS in implementation. block_on: high.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| browser → `/extract/file-text` | Untrusted binary file upload (Plan 05-02/04) | Vendor proposal files (PDF/DOCX/XLSX/PPTX) |
| browser → `/input/raw-text` | Untrusted free-text paste (Plan 05-02/04) | Vendor proposal text |
| FastAPI CORS → browser | Origin gating for SSE + API (Plan 05-02/08) | Allowed origins only |
| browser → `NEXT_PUBLIC_AI_BASE_URL` | All AI calls go to env-configured URL (Plan 05-03) | Service URL (public, not the key) |
| Trace route → filesystem | `/api/traces/[name]` reads `public/traces/` (Plan 05-04/07) | Sanitized filename |
| SSE stream → React state | ExtractionResult/ComparisonResult to client (Plan 05-06) | Grounded results |
| sessionStorage | Tab-scoped client cache; no server session (Plan 05-03/06) | No PII |
| Vercel → Render | Public internet, HTTPS, CORS-gated (Plan 05-08) | API traffic |
| Render env → OpenAI | API key server-only, never to browser (Plan 05-05/08) | OPENAI_API_KEY |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|------------------------|--------|
| T-05-02-A | Tampering | `/extract/file-text` filename | mitigate | `app.py:156` — only lowercased ext + raw bytes reach `_extract_text`; filename never a path; parsers read `io.BytesIO` only | closed |
| T-05-02-B | DoS | `/extract/file-text` | mitigate | `app.py:154-155` — `len(content) > 20_000_000` → HTTP 413 before parse | closed |
| T-05-02-C | DoS | `/input/raw-text` raw_text | mitigate | `app.py:102` — `pydantic_Field(max_length=200_000)` on `RawTextInput` | closed |
| T-05-02-D | Info Disclosure | CORS origin control | mitigate | `app.py:82-88` — exact `allow_origins` + Vercel regex, no `"*"`; OpenAI key server-only | closed |
| T-05-04-A | Tampering | `/api/traces/[name]` filename | mitigate | `route.ts:11-12` — `name.replace(/[^a-zA-Z0-9_.-]/g,"")` before `path.join`; `public/traces/` only | closed |
| T-05-05-B | Spoofing | ui-ux-gen artifact | mitigate | `docs/traces/ui-ux-gen-run.md:3-5` — model/prompt/date header; ~490-line artifact, not silent failure | closed |
| T-05-06-C | DoS | SSE stream never closes | mitigate | `extraction/page.tsx:246-247,288` + `comparison/page.tsx:352-354,361,461` — AbortController abort on cleanup in BOTH | closed |
| T-05-08-A | Info Disclosure | OPENAI_API_KEY on Render | mitigate | `render.yaml:19-20` `sync:false`; `.gitignore:9-11` ignores `.env*`; absent from code | closed |
| T-05-08-B | Spoofing | CORS misconfig | mitigate | `app.py:84` — `allow_origins` exact-string only; dead glob `https://*.vercel.app` absent (regex-only `:85`) | closed |
| T-05-08-C | DoS | Render cold start at demo | mitigate | `docs/demo/demo-script.md:18-19` — `curl .../data/rfq` warm step in Pre-Demo Checklist | closed |
| T-05-09-A | Spoofing | Playwright test | mitigate | `docs/qa/phase5-playwright.spec.ts` — asserts data-testid presence + no-rank framing, not exact model values | closed |
| T-05-01-SC | Tampering | No new package installs (Wave 0) | accept | Test files only; no new PyPI/npm packages | closed |
| T-05-02-SC | Tampering | pypdf/python-docx/openpyxl/python-pptx/python-multipart | accept | 05-RESEARCH Package Legitimacy Audit — all 5 canonical via PyPI API | closed |
| T-05-03-A | Info Disclosure | `NEXT_PUBLIC_AI_BASE_URL` | accept | Intentionally public (service URL, not the key); key stays server-side (D-24) | closed |
| T-05-03-B | Tampering | sessionStorage read/write | accept | Tab-scoped, single-buyer prototype, no PII, cleared on tab close | closed |
| T-05-03-C | Spoofing | LLM facts rendered as fact | accept | Grounding gate server-side (Phase 3); UI renders grounded result as-is | closed |
| T-05-04-B | DoS | File upload UI (client) | accept | Server enforces 20 MB (T-05-02-B); client guard redundant | closed |
| T-05-04-C | Spoofing | LLM fabrication on Vendor Input | accept | Raw text passed to extraction agent which enforces grounding | closed |
| T-05-05-A | Info Disclosure | OPENAI_API_KEY during live run | accept | Key in gitignored `.env`; artifact in `docs/traces/` carries no key material | closed |
| T-05-06-A | Spoofing | LLM facts rendered as fact | accept | Grounding gate server-side (Phase 3); `unsupported` badged, never `present` | closed |
| T-05-06-B | Tampering | Comparability verdict manipulation | accept | Comparability clamp code-enforced server-side (Phase 4); UI renders clamped result | closed |
| T-05-07-A | Info Disclosure | README content | accept | Only env var names, no values; `.env` gitignored + documented | closed |
| T-05-07-B | Tampering | Trace file path | accept | Sanitization handled in route handler (T-05-04-A) — no new risk | closed |
| T-05-08-D | Spoofing | LLM facts in deployed result | accept | Grounding gate server-side (Phase 3); not changeable at deploy time | closed |
| T-05-09-B | Info Disclosure | Demo video content | accept | Recording shows buyer UI only; verified no keys/env/terminals before commit | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-05-01-SC | Wave 0 test files only — no new packages | Aayush Gupta | 2026-06-28 |
| AR-02 | T-05-02-SC | 5 parser packages canonical (PyPI legitimacy audit) | Aayush Gupta | 2026-06-28 |
| AR-03 | T-05-03-A | `NEXT_PUBLIC_AI_BASE_URL` is the service URL, not the key | Aayush Gupta | 2026-06-28 |
| AR-04 | T-05-03-B | sessionStorage tab-scoped, no PII, single-buyer prototype | Aayush Gupta | 2026-06-28 |
| AR-05 | T-05-03-C, T-05-04-C, T-05-06-A, T-05-08-D | LLM fabrication mitigated by code-enforced grounding (Phase 3) | Aayush Gupta | 2026-06-28 |
| AR-06 | T-05-04-B | Server-side 20 MB cap makes client guard redundant | Aayush Gupta | 2026-06-28 |
| AR-07 | T-05-05-A | OpenAI key in gitignored `.env`; artifacts carry no key material | Aayush Gupta | 2026-06-28 |
| AR-08 | T-05-06-B | Comparability clamp code-enforced server-side (Phase 4) | Aayush Gupta | 2026-06-28 |
| AR-09 | T-05-07-A, T-05-07-B | README has no secret values; trace path sanitized (T-05-04-A) | Aayush Gupta | 2026-06-28 |
| AR-10 | T-05-09-B | Demo video shows buyer UI only; verified before commit | Aayush Gupta | 2026-06-28 |

*Accepted risks do not resurface in future audit runs.*

**Deferred (prototype scope, not a gap):** App-layer 20 MB / 200k-char caps are best-effort (body already deserialized when checked). The authoritative request-body limit (uvicorn `--limit-*` / reverse proxy) is explicitly deferred per 05-02-PLAN.md:282, consistent with prototype ASVS — not a declared mitigation for any verified threat.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-28 | 25 | 25 | 0 | gsd-security-auditor (verify-mitigations mode) |

11 `mitigate` threats verified present in implementation (file:line evidence above); 14 `accept` threats documented in Accepted Risks Log. No unregistered flags — SUMMARY.md Threat Flags (05-02/04/06/07) all map to existing threat IDs.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-28
