"""Phase 2 API contract smoke (DATA-04) — validation paths only, no happy-path OpenAI calls.

Confirms the live-regen endpoints are wired and enforce their input contract:
  - routes registered
  - unknown persona -> 400 (allowlist guard, runs before any LLM call)
  - over-length rfq_text -> 422 (pydantic bound, runs before the handler)
Run from services/ai via `uv run python <this>`.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app

paths = {(r.path, tuple(sorted(getattr(r, "methods", []) or []))) for r in app.routes}
have_rfq = any(p == "/data/rfq" for p, _ in paths)
have_vendor = any(p == "/data/vendor-gen" for p, _ in paths)
print(f"[{'PASS' if have_rfq else 'FAIL'}] GET /data/rfq route registered")
print(f"[{'PASS' if have_vendor else 'FAIL'}] POST /data/vendor-gen route registered")

ok = have_rfq and have_vendor
with TestClient(app) as client:  # lifespan runs verify_access() once (proves D-16 boot gate)
    # unknown persona -> 400 from the allowlist guard (no OpenAI call reached)
    r = client.post("/data/vendor-gen", json={"persona": "not-a-real-persona"})
    bad_persona_ok = r.status_code == 400
    print(f"[{'PASS' if bad_persona_ok else 'FAIL'}] unknown persona -> 400 (got {r.status_code})")

    # over-length rfq_text -> 422 from pydantic max_length bound (before handler)
    r2 = client.post(
        "/data/vendor-gen",
        json={"persona": "polished-fluff", "rfq_text": "x" * 200_001},
    )
    bound_ok = r2.status_code == 422
    print(f"[{'PASS' if bound_ok else 'FAIL'}] over-length rfq_text -> 422 (got {r2.status_code})")
    ok = ok and bad_persona_ok and bound_ok

print(f"\n{'API CONTRACT SMOKE PASSED' if ok else 'API CONTRACT SMOKE FAILED'}")
raise SystemExit(0 if ok else 1)
