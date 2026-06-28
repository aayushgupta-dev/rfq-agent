"""
test_input_wrap.py — RED stub for POST /input/raw-text (Wave 1, Plan 05-02).

Strict-xfail: MUST fail while the route is unimplemented.
Plan 05-02 removes the xfail marker after the route lands (GREEN phase).

Uses TestClient without a context manager to skip the lifespan startup gate
(verify_access() would require a live OpenAI key). Same pattern as test_sse_demo.py.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app
from schemas.domain import VendorResponse

client = TestClient(app, raise_server_exceptions=True)


def test_raw_text_wrap_returns_valid_vendor_response() -> None:
    """POST /input/raw-text → 200, body validates as VendorResponse.

    Proves the output feeds the /extract/vendor contract without schema drift.
    VendorResponse.model_validate() will raise ValidationError if any required
    field is missing or mis-typed — surfacing contract breakage immediately.
    """
    r = client.post(
        "/input/raw-text",
        json={"vendor_name": "Test Vendor", "raw_text": "We offer full-service marketing."},
    )
    assert r.status_code == 200

    # Round-trip: output must be a valid VendorResponse (the extraction agent contract)
    vendor = VendorResponse.model_validate(r.json())
    assert vendor.vendor_name == "Test Vendor"
    assert vendor.raw_text is not None
