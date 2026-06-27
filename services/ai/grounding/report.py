"""
report.py — Downgrade report types for the grounding gate (EXTRACT-04).

DowngradeEntry: one failed grounding attempt (field path, evidence, reason).
DowngradeReport: the full collection returned alongside the re-grounded object.

Consumed by tests now; passed to the SSE trace in P3.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic import Field as pydantic_Field

from schemas.envelope import Evidence


class DowngradeEntry(BaseModel):
    """One failed evidence grounding attempt.

    Records the field path, the evidence that failed to ground, and the reason
    for downgrade. Collected per-field and aggregated into DowngradeReport by
    the gate walker.
    """

    model_config = ConfigDict(extra="forbid")

    field_path: str
    original_status: str  # FlagStatus.value — str avoids circular import
    failed_evidence: Evidence
    reason: str


class DowngradeReport(BaseModel):
    """Full collection of downgrade entries for one ground_model() call.

    Returned alongside the re-grounded object so callers can surface downgrade
    details in the SSE trace (P3) or log them for debugging.
    """

    model_config = ConfigDict(extra="forbid")

    entries: list[DowngradeEntry] = pydantic_Field(default_factory=list)

    @property
    def has_downgrades(self) -> bool:
        return len(self.entries) > 0
