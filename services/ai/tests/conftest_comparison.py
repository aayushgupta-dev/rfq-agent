"""
conftest_comparison.py — Shared fixture builders for comparison agent tests.

Plain functions (not pytest fixtures) — same rationale as conftest_extraction.py:
they work both as top-level setup and inside test bodies without pytest fixture
injection machinery, and a single schema change breaks only this module.

# ponytail: builder functions not fixtures for the same reason as
# conftest_extraction.py — no fixture injection needed, direct call is cleaner.
"""
from __future__ import annotations

from conftest_extraction import missing_field, present_field
from schemas.domain import ExtractionResult, LineItemExtraction
from schemas.envelope import FlagStatus


# ---------------------------------------------------------------------------
# LineItemExtraction builders
# ---------------------------------------------------------------------------


def missing_line_item(line_item_id: str, line_item_name: str) -> LineItemExtraction:
    """Both pricing and scope_coverage are missing."""
    return LineItemExtraction(
        line_item_id=line_item_id,
        line_item_name=line_item_name,
        pricing=missing_field(),
        scope_coverage=missing_field(),
    )


def present_line_item(
    line_item_id: str,
    line_item_name: str,
    pricing_snippet: str,
    scope_snippet: str,
    source_id: str = "src",
) -> LineItemExtraction:
    """Both pricing and scope_coverage are present with Evidence."""
    return LineItemExtraction(
        line_item_id=line_item_id,
        line_item_name=line_item_name,
        pricing=present_field(pricing_snippet, pricing_snippet, source_id),
        scope_coverage=present_field(scope_snippet, scope_snippet, source_id),
    )


# ---------------------------------------------------------------------------
# ExtractionResult builders
# ---------------------------------------------------------------------------


def missing_extraction(vendor_name: str) -> ExtractionResult:
    """All Field[T] attributes set to missing; list fields default to []."""
    return ExtractionResult(
        vendor_name=vendor_name,
        scope_summary=missing_field(),
        line_items=[],
        pricing_structure=missing_field(),
        total_price=missing_field(),
        commercial_terms=missing_field(),
        timeline=missing_field(),
        compliance_points=[],
        assumptions=[],
        exclusions=[],
        risks=[],
    )


def present_extraction(vendor_name: str) -> ExtractionResult:
    """All required Field[T] attributes set to present with sentinel snippets."""
    return ExtractionResult(
        vendor_name=vendor_name,
        scope_summary=present_field("Full scope offered", "Full scope offered"),
        line_items=[
            present_line_item(
                "strategy-creative",
                "Strategy & Creative Development",
                "USD 120,000",
                "Full creative strategy and brand campaign development",
            )
        ],
        pricing_structure=present_field("Fixed fee per deliverable", "Fixed fee per deliverable"),
        total_price=present_field("USD 850,000", "USD 850,000"),
        commercial_terms=present_field("Net 30, milestone-based", "Net 30, milestone-based"),
        timeline=present_field("12 months from kick-off", "12 months from kick-off"),
        compliance_points=[present_field("COPPA compliant", "COPPA compliant")],
        assumptions=[present_field("Client provides brand guidelines", "Client provides brand guidelines")],
        exclusions=[present_field("Media buying excluded", "Media buying excluded")],
        risks=[present_field("Timeline risk if approvals delayed", "Timeline risk if approvals delayed")],
    )


def partial_extraction(vendor_name: str) -> ExtractionResult:
    """scope_summary and timeline present; pricing_structure/total_price/commercial_terms missing.

    line_items contains one missing_line_item — pricing missing triggers commercial
    ceiling to not_comparable. This fixture is the primary subject of clamp tests
    (mirrors cheap-but-incomplete persona).
    """
    return ExtractionResult(
        vendor_name=vendor_name,
        scope_summary=present_field("Partial scope — some items omitted", "Partial scope — some items omitted"),
        line_items=[
            missing_line_item("strategy-creative", "Strategy & Creative Development")
        ],
        pricing_structure=missing_field(),
        total_price=missing_field(),
        commercial_terms=missing_field(),
        timeline=present_field("6-8 weeks per phase", "6-8 weeks per phase"),
        compliance_points=[],
        assumptions=[],
        exclusions=[],
        risks=[],
    )
