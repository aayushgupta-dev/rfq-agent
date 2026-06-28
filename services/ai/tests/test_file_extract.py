"""
test_file_extract.py — RED stubs for POST /extract/file-text (Wave 1, Plan 05-02).

All five tests are strict-xfail: they MUST fail while the route is unimplemented.
Plan 05-02 removes all xfail markers after the route lands (GREEN phase).

Uses TestClient without a context manager to skip the lifespan startup gate
(verify_access() would require a live OpenAI key). Same pattern as test_sse_demo.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app, raise_server_exceptions=True)


class TestFileExtractRoute:
    """POST /extract/file-text — file-to-text dispatcher (PDF/DOCX/XLSX/PPTX)."""

    @pytest.mark.xfail(strict=True, reason="Wave 1 — route not yet implemented")
    def test_pdf_returns_text_and_chars(self) -> None:
        """POST /extract/file-text with minimal PDF bytes → 200, {text: str, chars: int}."""
        r = client.post(
            "/extract/file-text",
            files={"file": ("test.pdf", b"%PDF-1.4 minimal", "application/pdf")},
        )
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body.get("text"), str)
        assert isinstance(body.get("chars"), int)
        assert "filename" in body

    @pytest.mark.xfail(strict=True, reason="Wave 1 — route not yet implemented")
    def test_docx_returns_text(self) -> None:
        """POST /extract/file-text with DOCX bytes → 200, response has 'text' key."""
        # Minimal DOCX magic bytes (ZIP header) — best-effort extraction
        r = client.post(
            "/extract/file-text",
            files={"file": ("test.docx", b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "text" in body

    @pytest.mark.xfail(strict=True, reason="Wave 1 — route not yet implemented")
    def test_xlsx_returns_text(self) -> None:
        """POST /extract/file-text with XLSX bytes → 200, response has 'text' key."""
        r = client.post(
            "/extract/file-text",
            files={"file": ("test.xlsx", b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "text" in body

    @pytest.mark.xfail(strict=True, reason="Wave 1 — route not yet implemented")
    def test_pptx_returns_text(self) -> None:
        """POST /extract/file-text with PPTX bytes → 200, response has 'text' key."""
        r = client.post(
            "/extract/file-text",
            files={"file": ("test.pptx", b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "text" in body

    @pytest.mark.xfail(strict=True, reason="Wave 1 — route not yet implemented")
    def test_weak_extraction_not_an_error(self) -> None:
        """Tiny file with poor content → 200, not 422/500. chars < 200 is allowed.

        The server reports what it extracted; the caller decides whether to show an alert.
        Low yield is not a server error — it is a quality signal the UI can surface.
        """
        r = client.post(
            "/extract/file-text",
            files={"file": ("tiny.pdf", b"%PDF-1.4 x", "application/pdf")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "chars" in body
        # chars may be < 200 — that is acceptable; caller decides
        assert isinstance(body["chars"], int)
