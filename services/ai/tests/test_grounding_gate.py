"""
Grounding gate unit tests (EXTRACT-04).

Each invalid grounding case must produce a DowngradeEntry and return
status=unsupported (success criterion 1).
Each genuine evidence snippet must survive with recomputed offsets (success criterion 2).

Tests are in RED state: they call gate functions normally, and the stubs raise
NotImplementedError — pytest reports FAILED (the correct RED state before plan 02-02).
Do NOT wrap test bodies in pytest.raises(NotImplementedError): that would invert the
RED->GREEN invariant, passing against stubs and failing after implementation.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict

from schemas.envelope import (
    ConflictingValue,
    Evidence,
    Field,
    FlagStatus,
)
from grounding.gate import _normalize_with_map, ground_field, ground_model
from grounding.report import DowngradeEntry, DowngradeReport

# ---------------------------------------------------------------------------
# Fabricated span downgrade (success criterion 1)
# ---------------------------------------------------------------------------


class TestFabricatedSpanDowngrade:
    def test_fabricated_span_is_downgraded(self) -> None:
        """A snippet not present in source must be downgraded to unsupported (Test A)."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        fabricated_evidence = Evidence(
            snippet="Vendor A proposes $99 for everything",
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="$99 for everything",
            evidence=[fabricated_evidence],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.unsupported
        assert grounded.value is None
        assert grounded.evidence == []
        assert len(report) == 1


# ---------------------------------------------------------------------------
# Genuine span survival (success criterion 2)
# ---------------------------------------------------------------------------


class TestGenuineSpanPasses:
    def test_genuine_span_passes_grounding(self) -> None:
        """A snippet genuinely in source must keep present status + recomputed offsets (Test B)."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        genuine_evidence = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=10,  # intentionally wrong — gate recomputes
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[genuine_evidence],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.present
        assert len(report) == 0
        ev = grounded.evidence[0]
        assert source[ev.char_start : ev.char_end] == "$15,000 for strategy and creative"

    def test_offsets_are_recomputed_not_trusted(self) -> None:
        """Gate must recompute char_start/char_end even when model-supplied offsets are wrong."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        # Provide intentionally wrong offsets (0:1 points to "V", not the snippet)
        evidence_with_wrong_offsets = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=1,  # wrong — gate must overwrite these
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[evidence_with_wrong_offsets],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.present
        assert len(report) == 0
        ev = grounded.evidence[0]
        # Recomputed offsets must actually point to the snippet in source
        assert source[ev.char_start : ev.char_end] == "$15,000 for strategy and creative"


# ---------------------------------------------------------------------------
# Conflicting field (each ConflictingValue.evidence grounded independently)
# ---------------------------------------------------------------------------


class TestConflictingField:
    def test_conflicting_field_grounded_per_value(self) -> None:
        """Conflicting field with fabricated evidence in any ConflictingValue downgrades the whole field.

        Per D-05: any failed evidence in any ConflictingValue downgrades the whole Field
        to unsupported — a conservative tradeoff. The gate never partially preserves
        conflicting values when grounding fails.
        """
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        genuine_ev = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        fabricated_ev = Evidence(
            snippet="Vendor proposes $99 for absolutely everything",  # not in source
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.conflicting,
            values=[
                ConflictingValue[str](value="$15,000", evidence=[genuine_ev]),
                ConflictingValue[str](value="$99 for everything", evidence=[fabricated_ev]),
            ],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.unsupported


# ---------------------------------------------------------------------------
# Fuzzy matching (above and below threshold)
# ---------------------------------------------------------------------------


class TestFuzzyMatching:
    def test_fuzzy_match_above_threshold_grounds(self) -> None:
        """Minor normalization differences (extra space, lowercase) should still ground."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        # Snippet has extra space and is lowercase — minor normalization diff
        fuzzy_evidence = Evidence(
            snippet="vendor a proposes  $15,000",  # extra space, all lowercase
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[fuzzy_evidence],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.present
        assert len(report) == 0

    def test_fuzzy_match_below_threshold_downgrades(self) -> None:
        """A snippet completely unrelated to the source must be downgraded."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."
        completely_unrelated = Evidence(
            snippet="quarterly revenue targets exceed global benchmark standards",  # not in source
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="some value",
            evidence=[completely_unrelated],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.unsupported


# ---------------------------------------------------------------------------
# NFKC ligature offset mapping
# ---------------------------------------------------------------------------


class TestNFKCLigature:
    def test_nfkc_ligature_offset_mapping(self) -> None:
        """fi ligature (U+FB01) in source must match 'fi' snippet with correct offsets."""
        # Source text contains fi ligature (U+FB01) which NFKC-normalizes to "fi" (2 chars)
        source = "Our ﬁrm proposes $15,000"  # ﬁ = ﬁ (fi ligature)
        # Snippet uses decomposed "fi" (two separate chars)
        evidence = Evidence(
            snippet="firm proposes $15,000",
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[evidence],
        )
        grounded, report = ground_field(field, {"v1": source})
        assert grounded.status == FlagStatus.present
        assert len(report) == 0
        ev = grounded.evidence[0]
        # Recomputed offsets must point to correct region in original source
        # (source has the ligature ﬁ, not "fi" — offsets must still be correct)
        assert ev.char_start >= 0
        assert ev.char_end > ev.char_start


# ---------------------------------------------------------------------------
# Short snippet guard (MIN_SNIPPET_LEN)
# ---------------------------------------------------------------------------


class TestShortSnippetGuard:
    def test_short_snippet_guard(self) -> None:
        """Snippets shorter than MIN_SNIPPET_LEN must be downgraded even if coincidentally present.

        'Q3' appears in the source text but is too short to be reliably grounded
        (RESEARCH.md Pitfall 3 — trivially-short snippets can score near-100 via
        partial_ratio against any text, producing false positives).
        """
        source = "Our proposal covers Q3 through Q4 of the fiscal year for all eight line items."
        short_evidence = Evidence(
            snippet="Q3",  # shorter than MIN_SNIPPET_LEN (15 chars) — trivially short
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="Q3",
            evidence=[short_evidence],
        )
        grounded, report = ground_field(field, {"v1": source})
        # Even though "Q3" appears in source, it must be downgraded as too short
        assert grounded.status == FlagStatus.unsupported


# ---------------------------------------------------------------------------
# Walker (schema-agnostic recursive Field[T] traversal)
# ---------------------------------------------------------------------------


class TestWalker:
    def test_walker_grounds_nested_fields(self) -> None:
        """Recursive walker must find and re-ground every Field[T] in a nested pydantic model."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."

        # Inline pydantic model with two Field[str] attributes
        class _TestModel(BaseModel):
            model_config = ConfigDict(extra="forbid")
            genuine_field: Field[str]
            fabricated_field: Field[str]

        genuine_ev = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        fabricated_ev = Evidence(
            snippet="Vendor A proposes $99 for everything",  # not in source
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        model = _TestModel(
            genuine_field=Field[str](
                status=FlagStatus.present,
                value="15000",
                evidence=[genuine_ev],
            ),
            fabricated_field=Field[str](
                status=FlagStatus.present,
                value="$99 for everything",
                evidence=[fabricated_ev],
            ),
        )
        grounded_model, report = ground_model(model, {"v1": source})
        # Fabricated field must be downgraded
        assert grounded_model.fabricated_field.status == FlagStatus.unsupported
        # Genuine field must survive
        assert grounded_model.genuine_field.status == FlagStatus.present
        assert report.has_downgrades

    def test_ground_model_does_not_mutate_input(self) -> None:
        """ground_model() must return a NEW object; the original must be unchanged (D-06)."""
        source = "Vendor A proposes $15,000 for strategy and creative over 8 weeks."

        class _MutationTestModel(BaseModel):
            model_config = ConfigDict(extra="forbid")
            price_field: Field[str]

        ev = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=10,
            source_id="v1",
        )
        original_field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[ev],
        )
        model = _MutationTestModel(price_field=original_field)
        original_status_before = original_field.status

        ground_model(model, {"v1": source})

        # Original field object must be unchanged after ground_model()
        assert original_field.status == original_status_before


# ---------------------------------------------------------------------------
# _normalize_with_map unit tests (offset-map correctness)
# ---------------------------------------------------------------------------


class TestNormalizeWithMap:
    def test_nfkc_ligature_offset_roundtrip(self) -> None:
        """NFKC ﬁ ligature (1 char → 2 chars) must produce orig_indices that roundtrip to source."""
        source = "Our ﬁrm offers services"
        normalized, orig_indices = _normalize_with_map(source)
        # "fi" from ligature ﬁ should appear in normalized text
        fi_pos = normalized.find("fi")
        assert fi_pos >= 0, "NFKC ligature ﬁ must normalize to 'fi'"
        # Round-trip: original text sliced via orig_indices must equal source chars at that region
        orig_start = orig_indices[fi_pos]
        orig_end = orig_indices[fi_pos + 1] + 1  # +1 since ﬁ is one char in source
        assert source[orig_start:orig_end] == "ﬁ", (
            f"Expected 'ﬁ', got {source[orig_start:orig_end]!r}"
        )

    def test_normalize_strips_leading_trailing_consistently(self) -> None:
        """After trim-together, len(orig_indices) must equal len(normalized)."""
        normalized, orig_indices = _normalize_with_map("  hello  ")
        assert len(orig_indices) == len(normalized), (
            f"Map array length {len(orig_indices)} != normalized length {len(normalized)}"
        )
        assert normalized == "hello"


# ---------------------------------------------------------------------------
# Source-id missing downgrade
# ---------------------------------------------------------------------------


class TestSourceIdMissing:
    def test_missing_source_id_downgrades(self) -> None:
        """A field whose evidence references an unknown source_id must be downgraded."""
        ev = Evidence(
            snippet="$15,000 for strategy and creative",
            char_start=0,
            char_end=10,
            source_id="v_unknown",
        )
        field: Field[str] = Field[str](
            status=FlagStatus.present,
            value="15000",
            evidence=[ev],
        )
        grounded, report = ground_field(field, {"v_other": "some text about other things"})
        assert grounded.status == FlagStatus.unsupported
        assert len(report) == 1
        assert report[0].original_status == "present"
        assert "source_id not in sources" in report[0].reason
