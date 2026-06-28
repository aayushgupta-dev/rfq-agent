---
phase: 05-buyer-ui-trace-submission
plan: "02"
subsystem: services/ai
tags: [fastapi, cors, file-upload, sse, tdd]
dependency_graph:
  requires: ["05-01"]
  provides: ["INPUT-01", "INPUT-02", "INPUT-04", "CORS", "SSE-buffering-fix"]
  affects: ["services/ai/api/app.py"]
tech_stack:
  added: ["pypdf", "python-docx", "openpyxl", "python-pptx", "python-multipart"]
  patterns: ["CORSMiddleware with allow_origin_regex", "best-effort file dispatch", "X-Accel-Buffering in code"]
key_files:
  modified:
    - services/ai/api/app.py
    - services/ai/pyproject.toml
    - services/ai/tests/test_file_extract.py
    - services/ai/tests/test_input_wrap.py
  created: []
decisions:
  - "allow_origin_regex used (not allow_origins glob) for Vercel subdomain matching — Starlette exact-matches allow_origins by string equality"
  - "X-Accel-Buffering set in code on both SSE endpoints — authoritative vs. platform env var"
  - "_extract_text wraps each parser in try/except returning '' — best-effort keeps route always-200"
  - "20 MB file size cap checked after await file.read() — app-layer best-effort; server-level limit deferred to SHIP-01"
metrics:
  duration: "~10 min"
  completed: "2026-06-28"
  tasks_completed: 2
  files_changed: 4
---

# Phase 5 Plan 02: Backend Input Endpoints + CORS + X-Accel-Buffering Summary

FastAPI gains CORS middleware, two new input endpoints (/extract/file-text and /input/raw-text), and X-Accel-Buffering response headers on both SSE endpoints. Five file-parsing packages added and installed. All 6 xfail test stubs promoted to PASSED.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add 5 Python file-parsing dependencies | b7aaaf1 | services/ai/pyproject.toml, services/ai/uv.lock |
| 2 | CORS + /extract/file-text + /input/raw-text + X-Accel-Buffering | a319cf4 | services/ai/api/app.py, tests/test_file_extract.py, tests/test_input_wrap.py |

## What Was Built

**Task 1 — Dependencies:** `pypdf>=6.14.2`, `python-docx>=1.2.0`, `openpyxl>=3.1.5`, `python-pptx>=1.0.2`, `python-multipart>=0.0.32` added to `[project].dependencies` in pyproject.toml and synced via `uv sync`. All 5 importable: `import pypdf; import docx; import openpyxl; import pptx; import multipart` prints "all ok".

**Task 2 — App changes (TDD GREEN):**

1. `CORSMiddleware` added immediately after `app = FastAPI(...)`:
   - `allow_origins=["http://localhost:3000"]` (exact)
   - `allow_origin_regex=r"https://.*\.vercel\.app"` (handles all Vercel preview + prod URLs)
   - `allow_methods=["GET", "POST"]`, `allow_headers=["Content-Type"]`

2. `_extract_text(content: bytes, suffix: str) -> str` — private dispatcher:
   - PDF: pypdf PdfReader, page text joined with newlines
   - DOCX: python-docx Document, paragraph text joined
   - XLSX: openpyxl read_only workbook, all non-None cell values
   - PPTX: python-pptx Presentation, shape text_frame paragraphs
   - Unknown extension: returns `""`
   - All branches wrapped in `try/except Exception` — returns `""` on any parse error (best-effort)

3. `POST /extract/file-text` — multipart upload:
   - 20 MB app-layer cap (413 before parsing)
   - Suffix derived from `file.filename.rsplit(".", 1)[-1].lower()` — filename never passed to `_extract_text`
   - Returns `{"text": str, "filename": str, "chars": int}` always (never 422/500 on weak extraction)

4. `POST /input/raw-text` — raw text wrap:
   - `RawTextInput(vendor_name: str max_length=200, raw_text: str max_length=200_000)`
   - Returns `VendorResponse.model_dump(mode="json")` — valid extraction agent input, no schema drift

5. `X-Accel-Buffering: no` set on `EventSourceResponse` in both `/extract/vendor` and `/compare/vendors` — set in Python code (authoritative over platform env var).

## Test Results

```
tests/test_file_extract.py::TestFileExtractRoute::test_pdf_returns_text_and_chars PASSED
tests/test_file_extract.py::TestFileExtractRoute::test_docx_returns_text PASSED
tests/test_file_extract.py::TestFileExtractRoute::test_xlsx_returns_text PASSED
tests/test_file_extract.py::TestFileExtractRoute::test_pptx_returns_text PASSED
tests/test_file_extract.py::TestFileExtractRoute::test_weak_extraction_not_an_error PASSED
tests/test_input_wrap.py::test_raw_text_wrap_returns_valid_vendor_response PASSED
Full suite: 144 passed, 1 xfailed, 0 failures
```

## Deviations from Plan

**1. [Rule 3 - Blocking] Worktree .env absent — factory.py loads .env 3 levels up from services/ai/llm/factory.py**
- **Found during:** Task 1 verification (existing test suite failed to collect with `RuntimeError: Env var 'MODEL_REASONING' is not set`)
- **Issue:** The worktree root is `/…/worktrees/agent-a5212d248a365e7a9`; `factory.py` resolves `parents[3]` to that path, not the main repo root where `.env` lives
- **Fix:** Copied `.env` from repo root into the worktree root (test environment only; `.env` is gitignored)
- **Files modified:** `.env` (worktree local, not committed — gitignored)

All other changes executed exactly as planned.

## Known Stubs

None — both endpoints are fully wired and return real data.

## Threat Surface Scan

No new threat surface beyond what is documented in the plan's threat model (T-05-02-A through T-05-02-D). All mitigations implemented as specified:
- T-05-02-A: filename used only for extension; bytes path only in `_extract_text`
- T-05-02-B: 20 MB `len(content)` guard before parse, 413 on violation
- T-05-02-C: `pydantic_Field(max_length=200_000)` on `raw_text`
- T-05-02-D: no wildcard `*` origin; `allow_origin_regex` for Vercel subdomain matching

## Self-Check: PASSED

- [x] `services/ai/api/app.py` exists and modified
- [x] `services/ai/pyproject.toml` contains pypdf, python-docx, openpyxl, python-pptx, python-multipart
- [x] Commits b7aaaf1 and a319cf4 present in git log
- [x] 6/6 target tests PASSED (0 xfail, 0 skip)
- [x] Full suite: 144 passed, 1 xfailed
- [x] `grep -c "CORSMiddleware" app.py` = 2 (import + add_middleware — 1 add_middleware call)
- [x] `grep -c "allow_origin_regex" app.py` = 3 (comment + kwarg + acceptance check comment)
- [x] `grep -c "X-Accel-Buffering" app.py` = 3 (comment + 2 header assignments on SSE endpoints)
- [x] xfail markers removed from both test files (only docstring references remain)
