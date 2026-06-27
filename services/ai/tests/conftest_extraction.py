"""
conftest_extraction.py — Shared fixture builders for extraction agent tests.

Plain functions (not pytest fixtures) so they work both as top-level setup
and inside test bodies without the pytest fixture injection machinery.

# ponytail: builder functions exist to avoid brittle inline Field construction
# across 9 test stubs; centralised here so a schema change breaks one place.
"""
from __future__ import annotations

from schemas.envelope import Evidence, Field, FlagStatus


def missing_field(type_=str) -> Field:  # type: ignore[type-arg]
    """Return a Field with status=missing (no value, no evidence)."""
    # ponytail: type_ param reserved for documentation; Field is generic but
    # pydantic runtime doesn't enforce the inner type at construction — the
    # schema model_validator enforces field-level constraints.
    return Field(status=FlagStatus.missing)


def present_field(value: object, snippet: str, source_id: str = "src") -> Field:  # type: ignore[type-arg]
    """Return a Field[T] with status=present, one Evidence item."""
    return Field(
        status=FlagStatus.present,
        value=value,
        evidence=[Evidence(snippet=snippet, source_id=source_id, char_start=0, char_end=1)],
    )


def fabricated_field(value: str = "XYZNOTFOUND_VALUE") -> Field:  # type: ignore[type-arg]
    """Return a present Field whose snippet is guaranteed not locatable in any real source.

    ground_model() on this field ALWAYS produces a DowngradeEntry.
    Used by test_walker_covers_all_fields to verify the walker visits every Field[T].

    # ponytail: the sentinel snippet 'XYZNOTFOUND_FABRICATED_SNIPPET_123' is long enough
    # to clear MIN_SNIPPET_LEN (15 chars) and bizarre enough to never fuzzy-match real text.
    """
    return Field(
        status=FlagStatus.present,
        value=value,
        evidence=[
            Evidence(
                snippet="XYZNOTFOUND_FABRICATED_SNIPPET_123",
                source_id="src",
                char_start=0,
                char_end=1,
            )
        ],
    )
