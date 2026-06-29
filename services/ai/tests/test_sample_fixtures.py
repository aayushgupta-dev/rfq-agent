"""
test_sample_fixtures.py — Existence and messiness assertions on committed sample data (DATA-01/02/03).

Tests run against COMMITTED files under data/ — no LLM calls (D-13).
Live regen is a separate smoke path, not tested here.

Tests fail in RED state: data/rfq.json and data/vendor_*.json do not exist yet.
Each test asserts file existence FIRST (assert path.exists()) so failures surface as
AssertionError on the existence check, not AttributeError on a missing schema field.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.codegen import repo_root
from schemas.domain import RFQ, VendorResponse

_DATA_DIR = repo_root() / "data"

# D-09/D-13: explicit persona->filename map; filenames are authoritative.
# generate_samples.py must write exactly these names.
# Do not derive from persona.replace("-", "_") — explicit mapping prevents silent drift.
FIXTURE_FILENAMES: dict[str, str] = {
    "thorough-but-pricey": "vendor_thorough.json",
    "cheap-but-incomplete": "vendor_cheap.json",
    "polished-fluff": "vendor_fluff.json",
}


def test_rfq_fixture_valid() -> None:
    """data/rfq.json must exist and deserialize to a valid RFQ with exactly 8 line items."""
    fixture_path = _DATA_DIR / "rfq.json"
    # Assert existence FIRST — ensures pre-02-03 run fails with clear AssertionError,
    # not AttributeError on a missing schema field.
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"
    rfq = RFQ.model_validate_json(fixture_path.read_text())
    assert isinstance(rfq, RFQ)
    # 8 is the test-enforced contract (test-only, no model_validator needed for the
    # prototype); the rfq-gen prompt specifies 8 named line items.
    assert len(rfq.line_items) == 8


def test_vendor_fixtures_exist_and_valid() -> None:
    """Each vendor_*.json must exist and deserialize to a valid VendorResponse with raw_text."""
    for persona, filename in FIXTURE_FILENAMES.items():
        fixture_path = _DATA_DIR / filename
        # Assert existence FIRST — clear failure message before any schema access
        assert fixture_path.exists(), f"Missing fixture for persona '{persona}': {fixture_path}"
        vendor = VendorResponse.model_validate_json(fixture_path.read_text())
        assert isinstance(vendor, VendorResponse)
        # raw_text is the primary content — must be non-trivially long
        assert vendor.raw_text is not None and len(vendor.raw_text) > 200, (
            f"vendor '{persona}' raw_text is absent or suspiciously short "
            f"(got {len(vendor.raw_text) if vendor.raw_text else 0} chars)"
        )


def test_vendor_fixture_messiness() -> None:
    """Each persona fixture must contain its declared messiness markers.

    D-09/D-13: messiness assertions are deterministic keyword-based checks on committed
    raw_text — not LLM calls. If the model generates unexpected phrasing (e.g. 'price to
    be confirmed' vs 'TBD'), the fix is in the vendor-gen prompt, not the test assertion.
    """
    # thorough-but-pricey: must have bundled/all-inclusive/package pricing language
    thorough_path = _DATA_DIR / FIXTURE_FILENAMES["thorough-but-pricey"]
    assert thorough_path.exists(), f"Missing fixture: {thorough_path}"
    thorough = VendorResponse.model_validate_json(thorough_path.read_text())
    raw_thorough = thorough.raw_text.lower()
    assert any(
        marker in raw_thorough for marker in ("bundle", "all-inclusive", "package", "comprehensive")
    ), (
        "thorough-but-pricey vendor must have bundled/all-inclusive/package pricing language "
        "(D-09 mess spec: bundled_scope)"
    )

    # cheap-but-incomplete: must have a missing price marker
    cheap_path = _DATA_DIR / FIXTURE_FILENAMES["cheap-but-incomplete"]
    assert cheap_path.exists(), f"Missing fixture: {cheap_path}"
    cheap = VendorResponse.model_validate_json(cheap_path.read_text())
    raw_cheap = cheap.raw_text.lower()
    # D-09: cheap persona should not provide prices for at least one line item
    assert any(
        marker in raw_cheap for marker in ("tbd", "to be determined", "price not provided", "no price", "not included", "upon request")
    ), (
        "cheap-but-incomplete vendor must have at least one missing-price marker "
        "(D-09 mess spec: missing_price)"
    )

    # polished-fluff: must have contradictory/conflicting timeline statements
    fluff_path = _DATA_DIR / FIXTURE_FILENAMES["polished-fluff"]
    assert fluff_path.exists(), f"Missing fixture: {fluff_path}"
    fluff = VendorResponse.model_validate_json(fluff_path.read_text())
    raw_fluff = fluff.raw_text.lower()
    # D-09: fluff persona should have internal contradictions (two different week counts
    # or contradictory scope statements)
    week_counts = re.findall(r"(\d+)\s*weeks?", raw_fluff)
    scope_conflicts = any(
        marker in raw_fluff for marker in ("will not", "won't", "cannot", "excluded", "not included")
    )
    assert len(set(week_counts)) >= 2 or scope_conflicts, (
        "polished-fluff vendor must contain at least two contradictory timeline or "
        "scope statements (D-09 mess spec: internal_conflict)"
    )


def test_cheap_incomplete_has_missing_price() -> None:
    """cheap-but-incomplete fixture must have at least one line item with no price mention."""
    vendor_path = _DATA_DIR / FIXTURE_FILENAMES["cheap-but-incomplete"]
    # Assert existence FIRST
    assert vendor_path.exists(), f"Missing fixture: {vendor_path}"
    vendor = VendorResponse.model_validate_json(vendor_path.read_text())
    raw = vendor.raw_text.lower()
    # D-13: string search only, no LLM call
    has_missing_price_marker = any(
        marker in raw for marker in ("tbd", "to be determined", "price not provided", "no price", "not included", "upon request")
    )
    # Alternative: check that at least one line item section has no dollar amount
    import re
    dollar_amounts = re.findall(r"\$[\d,]+", raw)
    # If there are fewer dollar amounts than line items (8), at least one is missing
    has_fewer_prices_than_items = len(dollar_amounts) < 8
    assert has_missing_price_marker or has_fewer_prices_than_items, (
        "cheap-but-incomplete vendor must have at least one line item with no visible price"
    )


def test_polished_fluff_has_conflict() -> None:
    """polished-fluff fixture must contain at least two contradictory timeline or scope statements."""
    vendor_path = _DATA_DIR / FIXTURE_FILENAMES["polished-fluff"]
    # Assert existence FIRST
    assert vendor_path.exists(), f"Missing fixture: {vendor_path}"
    vendor = VendorResponse.model_validate_json(vendor_path.read_text())
    raw = vendor.raw_text.lower()
    # D-13: simple string pattern search, no LLM call
    # Look for two different week counts (e.g. "6 weeks" and "12 weeks")
    week_counts = re.findall(r"(\d+)\s*weeks?", raw)
    different_week_counts = len(set(week_counts)) >= 2
    # Or: look for contradictory will/won't statements near the same line item
    has_contradictory_terms = any(
        marker in raw for marker in ("will not", "won't", "cannot", "excluded", "not included")
    ) and any(
        marker in raw for marker in ("will ", "we offer", "we provide", "included")
    )
    assert different_week_counts or has_contradictory_terms, (
        "polished-fluff vendor must contain at least two contradictory timeline or "
        "scope statements (D-09 mess spec: internal_conflict)"
    )


def test_polished_fluff_has_total_price_conflict() -> None:
    """vendor_fluff must state two contradictory all-in grand totals (UAT test-8 regression guard)."""
    vendor_path = _DATA_DIR / FIXTURE_FILENAMES["polished-fluff"]
    # Assert existence FIRST
    assert vendor_path.exists(), f"Missing fixture: {vendor_path}"
    vendor = VendorResponse.model_validate_json(vendor_path.read_text())
    raw = vendor.raw_text
    # D-13: string search only, no LLM call. Pins the exact injected totals.
    assert "USD 1.2M" in raw and "$950,000" in raw, (
        "vendor_fluff must contain two contradictory all-in grand totals (USD 1.2M vs $950,000) "
        "so the total_price=conflicting path is exercisable (UAT test-8)"
    )
