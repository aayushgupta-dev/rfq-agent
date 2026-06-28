"""
test_health.py — hermetic test for GET /health (docker-compose healthcheck target).

TestClient instantiated WITHOUT a context manager so the lifespan startup gate
(verify_access() — needs a live OpenAI key) never runs. Same pattern as
test_sse_demo.py / test_input_wrap.py. This proves /health is reachable with no key.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app, raise_server_exceptions=True)


def test_health_returns_ok() -> None:
    """GET /health → 200 with body exactly {"status": "ok"}, no model call, no key."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
