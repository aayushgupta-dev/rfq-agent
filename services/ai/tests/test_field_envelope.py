"""
Semantic validation tests for the Field[T] absence envelope.

Each invalid Field[T] combination must raise ValidationError (PLAT-01).
Each valid combination must pass. Evidence and EventEnvelope closed-enum
checks are also covered.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.envelope import (
    ConflictingValue,
    Evidence,
    Field,
    FlagStatus,
)
from schemas.events import ErrorPayload, EventEnvelope

# ---------------------------------------------------------------------------
# FlagStatus
# ---------------------------------------------------------------------------


def test_flag_status_has_five_members() -> None:
    members = {m.value for m in FlagStatus}
    assert members == {"present", "missing", "unclear", "conflicting", "unsupported"}


# ---------------------------------------------------------------------------
# Evidence — extra="forbid"
# ---------------------------------------------------------------------------


def test_evidence_valid() -> None:
    ev = Evidence(snippet="x", char_start=0, char_end=1, source_id="doc-1")
    assert ev.snippet == "x"
    assert ev.char_start == 0
    assert ev.char_end == 1
    assert ev.source_id == "doc-1"


def test_evidence_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        Evidence(snippet="x", char_start=0, char_end=1, source_id="s", bogus=1)


# ---------------------------------------------------------------------------
# Field[str] — valid cases
# ---------------------------------------------------------------------------


def test_field_present_with_value() -> None:
    ev = Evidence(snippet="hello", char_start=0, char_end=5, source_id="doc-1")
    f: Field[str] = Field[str](status=FlagStatus.present, value="hello", evidence=[ev])
    assert f.value == "hello"
    assert f.status == FlagStatus.present


def test_field_missing_with_none_value() -> None:
    f: Field[str] = Field[str](status=FlagStatus.missing)
    assert f.value is None
    assert f.status == FlagStatus.missing


def test_field_unclear_with_none_value() -> None:
    f: Field[str] = Field[str](status=FlagStatus.unclear)
    assert f.value is None


def test_field_unclear_with_value() -> None:
    """unclear with an asserted value requires evidence."""
    ev = Evidence(snippet="maybe", char_start=0, char_end=5, source_id="doc-1")
    f: Field[str] = Field[str](status=FlagStatus.unclear, value="maybe", evidence=[ev])
    assert f.value == "maybe"


def test_field_unsupported_with_none_value() -> None:
    f: Field[str] = Field[str](status=FlagStatus.unsupported)
    assert f.value is None


# ---------------------------------------------------------------------------
# Field[str] — invalid cases (semantic model_validator rules)
# ---------------------------------------------------------------------------


def test_field_missing_with_value_raises() -> None:
    with pytest.raises(ValidationError):
        Field[str](status=FlagStatus.missing, value="something")


def test_field_unsupported_with_value_raises() -> None:
    with pytest.raises(ValidationError):
        Field[str](status=FlagStatus.unsupported, value="something")


def test_field_present_with_none_value_raises() -> None:
    with pytest.raises(ValidationError):
        Field[str](status=FlagStatus.present, value=None)


# ---------------------------------------------------------------------------
# Field[int] — conflicting status
# ---------------------------------------------------------------------------


def test_field_conflicting_empty_values_raises() -> None:
    with pytest.raises(ValidationError):
        Field[int](status=FlagStatus.conflicting, values=[])


def test_field_conflicting_non_empty_values_valid() -> None:
    ev = Evidence(snippet="p1", char_start=0, char_end=2, source_id="src-1")
    cv = ConflictingValue[int](value=42, evidence=[ev])
    f: Field[int] = Field[int](status=FlagStatus.conflicting, values=[cv])
    assert len(f.values) == 1
    assert f.values[0].value == 42


def test_field_conflicting_none_values_raises() -> None:
    """values=None on conflicting status is also invalid."""
    with pytest.raises(ValidationError):
        Field[int](status=FlagStatus.conflicting, values=None)


# ---------------------------------------------------------------------------
# Field[Decimal] — round-trips correctly
# ---------------------------------------------------------------------------


def test_field_decimal_present() -> None:
    ev = Evidence(snippet="9.99", char_start=0, char_end=4, source_id="doc-1")
    f: Field[Decimal] = Field[Decimal](status=FlagStatus.present, value=Decimal("9.99"), evidence=[ev])
    assert f.value == Decimal("9.99")


# ---------------------------------------------------------------------------
# EventEnvelope — closed Literal type
# ---------------------------------------------------------------------------


def test_event_envelope_valid_types() -> None:
    for event_type in ("status", "partial", "result", "error", "done"):
        env = EventEnvelope(type=event_type, payload={})
        assert env.type == event_type


def test_event_envelope_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        EventEnvelope(type="frobnicate", payload={})


# ---------------------------------------------------------------------------
# ErrorPayload
# ---------------------------------------------------------------------------


def test_error_payload_valid() -> None:
    ep = ErrorPayload(code="E001", message="Something went wrong", recoverable=True)
    assert ep.code == "E001"
    assert ep.recoverable is True


def test_error_payload_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        ErrorPayload(code="E001")  # missing message and recoverable


# ---------------------------------------------------------------------------
# Field evidence default_factory
# ---------------------------------------------------------------------------


def test_field_evidence_defaults_to_empty_list() -> None:
    f: Field[str] = Field[str](status=FlagStatus.missing)
    assert f.evidence == []
    # Confirm it's not the same object across instances (mutable default guard)
    f2: Field[str] = Field[str](status=FlagStatus.missing)
    assert f.evidence is not f2.evidence


# ---------------------------------------------------------------------------
# CR-01: Field[present] requires non-empty evidence (grounding invariant)
# ---------------------------------------------------------------------------


def test_field_present_empty_evidence_raises() -> None:
    """present status with no evidence violates the grounding invariant (CR-01)."""
    with pytest.raises(ValidationError):
        Field[str](status=FlagStatus.present, value="1200000", evidence=[])


def test_field_present_with_evidence_passes() -> None:
    """present status with at least one Evidence item is valid."""
    ev = Evidence(snippet="vendor said so", char_start=0, char_end=14, source_id="doc-1")
    f: Field[str] = Field[str](status=FlagStatus.present, value="1200000", evidence=[ev])
    assert f.value == "1200000"
    assert len(f.evidence) == 1


# ---------------------------------------------------------------------------
# CR-01 variant: Field[unclear] with a value requires evidence
# ---------------------------------------------------------------------------


def test_field_unclear_with_value_empty_evidence_raises() -> None:
    """unclear + value with no evidence violates the grounding invariant (CR-01)."""
    with pytest.raises(ValidationError):
        Field[str](status=FlagStatus.unclear, value="maybe 500k", evidence=[])


def test_field_unclear_with_value_and_evidence_passes() -> None:
    """unclear + value + evidence is valid."""
    ev = Evidence(snippet="approx", char_start=0, char_end=6, source_id="doc-1")
    f: Field[str] = Field[str](status=FlagStatus.unclear, value="maybe 500k", evidence=[ev])
    assert f.value == "maybe 500k"


def test_field_unclear_with_none_value_empty_evidence_passes() -> None:
    """unclear + value=None (pure tentative/absent) with no evidence is valid."""
    f: Field[str] = Field[str](status=FlagStatus.unclear, value=None, evidence=[])
    assert f.value is None


# ---------------------------------------------------------------------------
# CR-03: Field[conflicting] — each ConflictingValue requires evidence
# ---------------------------------------------------------------------------


def test_field_conflicting_cv_empty_evidence_raises() -> None:
    """A ConflictingValue with empty evidence fails (CR-03)."""
    with pytest.raises(ValidationError):
        Field[str](
            status=FlagStatus.conflicting,
            values=[
                ConflictingValue[str](value="500k", evidence=[]),
                ConflictingValue[str](value="600k", evidence=[]),
            ],
        )


def test_field_conflicting_all_cvs_have_evidence_passes() -> None:
    """Conflicting where every ConflictingValue has evidence is valid."""
    ev1 = Evidence(snippet="section A says 500k", char_start=0, char_end=19, source_id="doc-1")
    ev2 = Evidence(snippet="section B says 600k", char_start=20, char_end=39, source_id="doc-1")
    f: Field[str] = Field[str](
        status=FlagStatus.conflicting,
        values=[
            ConflictingValue[str](value="500k", evidence=[ev1]),
            ConflictingValue[str](value="600k", evidence=[ev2]),
        ],
    )
    assert len(f.values) == 2


# ---------------------------------------------------------------------------
# CR-02: Evidence offset sanity validation
# ---------------------------------------------------------------------------


def test_evidence_char_end_before_char_start_raises() -> None:
    """char_end <= char_start is semantically impossible (CR-02)."""
    with pytest.raises(ValidationError):
        Evidence(snippet="x", char_start=500, char_end=0, source_id="doc-1")


def test_evidence_negative_char_start_raises() -> None:
    """Negative char_start is invalid (CR-02)."""
    with pytest.raises(ValidationError):
        Evidence(snippet="x", char_start=-5, char_end=0, source_id="doc-1")


def test_evidence_valid_offsets_pass() -> None:
    """Positive char_start with char_end > char_start is valid."""
    ev = Evidence(snippet="hello", char_start=0, char_end=5, source_id="doc-1")
    assert ev.char_start == 0
    assert ev.char_end == 5
