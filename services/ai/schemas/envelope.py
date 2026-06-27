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

    Offsets are computed/validated in code, never trusted from the model (CLAUDE.md §8).
    """

    model_config = ConfigDict(extra="forbid")

    snippet: str
    char_start: int
    char_end: int
    source_id: str


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

        # status == unclear: no constraint — partial/tentative info allowed

        return self
