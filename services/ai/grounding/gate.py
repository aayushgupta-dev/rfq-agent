"""
gate.py — Grounding gate: verify and recompute evidence spans (EXTRACT-04).

Pure, LLM-free. Ignores model-supplied char_start/char_end (D-01); searches
source text for the snippet, recomputes REAL offsets on a hit, and downgrades
unlocatable facts to unsupported (D-06). Sources are dict[str, str] keyed by
Evidence.source_id (D-07).

This module is a STUB — function signatures are defined so imports resolve and
tests can be written against real identifiers before implementation lands in
plan 02-02. All functions raise NotImplementedError.
"""
from __future__ import annotations

from pydantic import BaseModel

# ponytail: class named Field shadows pydantic.Field — alias import avoids collision
# without renaming the contract class (the pydantic.Field function is imported as
# pydantic_Field in models that need it).
from schemas.envelope import Field as EnvelopeField

from grounding.report import DowngradeEntry, DowngradeReport

# ponytail: 90.0 is the starting fuzzy threshold from D-03; calibrated against
# real committed sample fixtures in plan 02-02. Not a magic number — see
# RESEARCH.md Pattern 3 and Pitfall 3 for rationale.
FUZZY_THRESHOLD: float = 90.0

# ponytail: 15-char minimum guards against trivially-short snippets scoring high
# via partial_ratio (RESEARCH.md Pitfall 3). Revisit in P3 once extraction agent
# output is known — real evidence snippets may require adjustment.
MIN_SNIPPET_LEN: int = 15


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Return (normalized, orig_indices) where orig_indices[i] = original char index.

    Two-stage normalization (RESEARCH.md Pattern 2):
      Stage 1: NFKC + smart-quote/dash normalization + casefold (may expand chars)
      Stage 2: whitespace collapse (removes chars, shifts indices)
    Compose both maps so orig_indices[i] always points into the original `text`.

    Not yet implemented — plan 02-02 lands the logic.
    """
    raise NotImplementedError("_normalize_with_map not implemented")


def _match_exact(
    norm_snippet: str,
    norm_source: str,
    orig_indices: list[int],
) -> tuple[int, int] | None:
    """Search for norm_snippet in norm_source via exact string find.

    Returns (char_start, char_end) in original source text on hit, or None on miss.
    Uses orig_indices to remap normalized positions back to original offsets.

    Not yet implemented — plan 02-02 lands the logic.
    """
    raise NotImplementedError("_match_exact not implemented")


def _match_fuzzy(
    norm_snippet: str,
    norm_source: str,
    threshold: float,
    orig_indices: list[int],
) -> tuple[int, int] | None:
    """Fuzzy fallback via rapidfuzz.fuzz.partial_ratio_alignment (RESEARCH.md Pattern 3).

    Returns (char_start, char_end) in original source text if score >= threshold,
    or None if score is below threshold. Uses orig_indices to remap dest offsets.

    Not yet implemented — plan 02-02 lands the logic (rapidfuzz added then).
    """
    raise NotImplementedError("_match_fuzzy not implemented")


def ground_field(
    field: EnvelopeField,
    sources: dict[str, str],
    field_path: str = "",
) -> tuple[EnvelopeField, list[DowngradeEntry]]:
    """Ground one Field[T] against its source text.

    Returns a (possibly downgraded) new Field[T] and a list of DowngradeEntry items.
    The original field is never mutated — always returns a new object (D-06).

    If any evidence snippet cannot be located in its source text, the entire field
    is downgraded to FlagStatus.unsupported with value=None and evidence=[].

    Not yet implemented — plan 02-02 lands the logic.
    """
    raise NotImplementedError("ground_field not implemented")


def ground_model(
    obj: BaseModel,
    sources: dict[str, str],
) -> tuple[BaseModel, DowngradeReport]:
    """Schema-agnostic recursive walker: ground every Field[T] in a pydantic model.

    Returns a (re-grounded copy of obj, DowngradeReport). The original obj is
    never mutated (D-06). Uses pydantic v2 model_fields + model_copy (RESEARCH.md
    Pattern 4).

    Not yet implemented — plan 02-02 lands the logic.
    """
    raise NotImplementedError("ground_model not implemented")
