"""
test_prompts_api.py — GET /prompts/{id} (Prompt Pack read endpoint).

Hermetic: reads the versioned prompt files via prompts.registry; no live model call.
TestClient(app) is instantiated without a context manager so the lifespan startup
access check (verify_access) never fires (mirrors test_sse_demo.py).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_get_prompt_returns_metadata_and_body():
    r = client.get("/prompts/extraction")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "extraction"
    assert body["content"].strip()  # non-empty markdown body
    assert isinstance(body["metadata"], dict)


def test_unknown_prompt_returns_404():
    # Valid id shape, but no such prompt file → KeyError → 404 (not a 500).
    r = client.get("/prompts/does-not-exist")
    assert r.status_code == 404


def test_invalid_prompt_id_returns_400():
    # Uppercase + underscore violate ^[a-z0-9-]+$ → ValueError → 400 (path-traversal guard).
    r = client.get("/prompts/Bad_Id")
    assert r.status_code == 400
