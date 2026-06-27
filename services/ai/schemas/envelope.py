"""
envelope.py — Generic Field[T] absence envelope with semantic model_validator rules.

The core contract primitive for every extracted domain fact. Absence is a first-class
5-state enum — there is no nullable that silently collapses to blank (D-05, D-07).

Semantic rules (enforced in code, not by convention — HIGH review requirement):
  - status=present   → value must not be None
  - status=missing   → value must be None
  - status=unsupported → value must be None
  - status=conflicting → values[] must be non-empty (len >= 1)
  - status=unclear   → no constraint on value (partial/tentative info allowed)

# ponytail: class named Field shadows pydantic.Field — alias import avoids collision
# without renaming the contract class (the pydantic.Field function is imported as
# pydantic_Field).
"""
from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as pydantic_Field


class FlagStatus(StrEnum):
    """5-state absence/confidence flag for every extracted field (D-07).

    Never collapses to blank — absence is first-class.
    """

    present = "present"
    missing = "missing"
    unclear = "unclear"
    conflicting = "conflicting"
    unsupported = "unsupported"


T = TypeVar("T")


class Evidence(BaseModel):
    """Source grounding for a single extracted fact (D-04).

    Offsets are validated in code, never trusted from the model (CLAUDE.md §8).
    Enforced: char_start >= 0 and char_end > char_start. Snippet-vs-source-text
    matching (that the span actually exists in the vendor document) is a Phase 3
    agent-level concern requiring the source text — not enforced here.
    """

    model_config = ConfigDict(extra="forbid")

    snippet: str
    char_start: int
    char_end: int
    source_id: str

    @model_validator(mode="after")
    def _validate_offsets(self) -> Evidence:
        if self.char_start < 0:
            raise ValueError(
                f"char_start must be >= 0, got {self.char_start}"
            )
        if self.char_end <= self.char_start:
            raise ValueError(
                f"char_end ({self.char_end}) must be > char_start ({self.char_start})"
            )
        return self


class ConflictingValue(BaseModel, Generic[T]):  # noqa: UP046
    """One entry in a conflicting field's values[] list (D-06).

    When a vendor response says one thing in section A and another in section B,
    each contradictory claim becomes a ConflictingValue with its own evidence —
    so the UI can show "Vendor says X here, Y there" with both sources.
    """

    model_config = ConfigDict(extra="forbid")

    value: T | None = None
    evidence: list[Evidence] = pydantic_Field(default_factory=list)


class Field(BaseModel, Generic[T]):  # noqa: UP046
    """Per-field absence envelope — the contract core (D-05).

    Every domain fact that may be missing, ambiguous, or contradictory uses this
    envelope instead of a bare nullable. The model_validator enforces that invalid
    combinations (e.g. status=missing + populated value) fail at validation time,
    not silently pass through to the UI.
    """

    model_config = ConfigDict(extra="forbid")

    status: FlagStatus
    value: T | None = None
    # ponytail: default_factory=list is safer than a mutable default literal; pydantic
    # supports it, and it is clearer intent (each instance gets its own list object).
    evidence: list[Evidence] = pydantic_Field(default_factory=list)
    # populated only when status == conflicting (D-06)
    values: list[ConflictingValue[T]] | None = None

    @model_validator(mode="after")
    def _validate_absence_semantics(self) -> Field[T]:
        """Enforce semantic rules for the 5-state absence enum.

        These constraints make the absence-enum contract code-enforced, not just
        advisory. A caller — or an LLM output — that puts a value in a missing
        field, or leaves a conflicting field without evidence, gets a hard
        ValidationError (PLAT-01).
        """
        status = self.status

        if status == FlagStatus.conflicting:
            if not self.values:
                raise ValueError(
                    "conflicting status requires non-empty values[] "
                    "(each contradictory claim must carry its own evidence)"
                )
            for i, cv in enumerate(self.values):
                if not cv.evidence:
                    raise ValueError(
                        f"conflicting values[{i}] has no evidence — "
                        "every contradictory claim must link to a source snippet"
                    )

        elif status in (FlagStatus.missing, FlagStatus.unsupported):
            if self.value is not None:
                raise ValueError(
                    f"{status.value!r} status must not carry a value "
                    "(absence is a first-class state, not a suppressed nullable)"
                )

        elif status == FlagStatus.present:
            if self.value is None:
                raise ValueError(
                    "present status requires a value "
                    "(use missing/unclear if the information is not available)"
                )
            if not self.evidence:
                raise ValueError(
                    "present status requires at least one Evidence item "
                    "(every asserted fact must be traceable to a source snippet)"
                )

        # status == unclear: partial/tentative info allowed; if a value is asserted,
        # evidence is still required so the partial claim traces to a source.
        if status == FlagStatus.unclear and self.value is not None and not self.evidence:
            raise ValueError(
                "unclear status with a value requires at least one Evidence item "
                "(partial facts still need a source)"
            )

        return self
