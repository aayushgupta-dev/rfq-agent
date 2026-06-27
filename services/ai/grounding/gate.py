"""
gate.py — Grounding gate: verify and recompute evidence spans (EXTRACT-04).

Pure, LLM-free. Ignores model-supplied char_start/char_end (D-01); searches
source text for the snippet, recomputes REAL offsets on a hit, and downgrades
unlocatable facts to unsupported (D-06). Sources are dict[str, str] keyed by
Evidence.source_id (D-07).

# ponytail: class named Field shadows pydantic.Field — alias import avoids collision
# without renaming the contract class (the pydantic.Field function is imported as
# pydantic_Field in models that need it).
"""
from __future__ import annotations

import unicodedata

from pydantic import BaseModel
from rapidfuzz.fuzz import partial_ratio_alignment

# ponytail: class named Field shadows pydantic.Field — alias import avoids collision
# without renaming the contract class (the pydantic.Field function is imported as
# pydantic_Field in models that need it).
from schemas.envelope import Evidence, Field as EnvelopeField, FlagStatus

from grounding.report import DowngradeEntry, DowngradeReport

# ponytail: 90.0 is the starting fuzzy threshold from D-03; calibrated against
# real committed sample fixtures in plan 02-02. Not a magic number — see
# RESEARCH.md Pattern 3 and Pitfall 3 for rationale.
# FUZZY_THRESHOLD calibrated against test fixtures — genuine minor-whitespace diffs score
# ~95+; set to 90.0 to accept genuine fuzzy matches while rejecting fabricated spans.
FUZZY_THRESHOLD: float = 90.0

# ponytail: 15-char minimum guards against trivially-short snippets scoring high
# via partial_ratio (Pitfall 3). Revisit in P3 once extraction agent output is
# known — real evidence snippets may require adjustment.
MIN_SNIPPET_LEN: int = 15


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Return (normalized, orig_indices) where orig_indices[i] = original char index.

    Two-stage normalization (RESEARCH.md Pattern 2):
      Stage 1: NFKC + smart-quote/dash normalization + casefold (may expand chars)
      Stage 2: whitespace collapse (removes chars, shifts indices)
    Compose both maps so orig_indices[i] always points into the original `text`.

    # ponytail: two-stage normalization map exists because NFKC expansion and
    # whitespace collapse both change string length; single-pass assumption breaks
    # offset recovery (D-04).

    # NFD decomposed source (e.g. 'e' + combining acute) is composed to 'e-acute'
    # by NFKC. The resulting offset points to the base character position in the
    # original string — this is intentionally conservative and acceptable for
    # grounding (snippet highlights the composed character region).
    """
    # Stage 1: NFKC + smart-quote/dash normalization + casefold per char.
    # Builds stage1_to_orig: stage1_index -> original index.
    # NFKC can expand one char to many (e.g. ﬁ → fi, 1→2); extend the map for
    # each expanded character so the mapping stays 1:1 with the stage1 string.
    stage1_chars: list[str] = []
    stage1_to_orig: list[int] = []
    for orig_i, ch in enumerate(text):
        n = unicodedata.normalize("NFKC", ch)
        # D-02: moderate normalization — smart quotes → straight, en/em dash → hyphen
        n = (
            n.replace("‘", "'").replace("’", "'")   # ' '
             .replace("“", '"').replace("”", '"')   # " "
             .replace("–", "-").replace("—", "-")   # – —
        )
        n = n.casefold()
        stage1_chars.append(n)
        # Each char in the expanded stage1 string maps back to orig_i
        stage1_to_orig.extend([orig_i] * len(n))

    stage1 = "".join(stage1_chars)

    # Stage 2: whitespace collapse — keep positions of surviving chars.
    # Records the stage1 index of each character that survives into the final string.
    surviving_positions: list[int] = []
    final_chars: list[str] = []
    prev_was_space = False
    for s1_i, ch in enumerate(stage1):
        if ch in (" ", "\t", "\n", "\r", "\x0b", "\x0c"):
            if not prev_was_space:
                final_chars.append(" ")
                surviving_positions.append(s1_i)
            prev_was_space = True
        else:
            final_chars.append(ch)
            surviving_positions.append(s1_i)
            prev_was_space = False

    normalized_str = "".join(final_chars)

    # Trim leading/trailing whitespace together with the surviving_positions so that
    # the index map stays aligned with the trimmed string (OFFSET-MAP CORRECTNESS).
    # Stripping the normalized string alone after building orig_indices would shift the
    # mapping — trim both together to avoid the index skew.
    leading_spaces = len(normalized_str) - len(normalized_str.lstrip())
    trailing_spaces = len(normalized_str) - len(normalized_str.rstrip())
    normalized = normalized_str[leading_spaces: len(normalized_str) - trailing_spaces or None]
    trimmed_positions = surviving_positions[
        leading_spaces: len(surviving_positions) - trailing_spaces or None
    ]

    # Compose: final_i -> stage1_i -> orig_i
    orig_indices = [stage1_to_orig[s1_i] for s1_i in trimmed_positions[: len(normalized)]]
    return normalized, orig_indices


def _match_exact(
    norm_snippet: str,
    norm_source: str,
    orig_indices: list[int],
) -> tuple[int, int] | None:
    """Search for norm_snippet in norm_source via exact string find.

    Returns (char_start, char_end) in original source text on hit, or None on miss.
    Uses orig_indices to remap normalized positions back to original offsets.
    """
    if not norm_snippet or not norm_source:
        return None
    found = norm_source.find(norm_snippet)
    if found == -1:
        return None
    norm_start = found
    norm_end_excl = norm_start + len(norm_snippet)
    char_start = orig_indices[norm_start]
    char_end = orig_indices[norm_end_excl - 1] + 1
    return char_start, char_end


def _match_fuzzy(
    norm_snippet: str,
    norm_source: str,
    threshold: float,
    orig_indices: list[int],
) -> tuple[int, int] | None:
    """Fuzzy fallback via rapidfuzz.fuzz.partial_ratio_alignment (RESEARCH.md Pattern 3).

    Returns (char_start, char_end) in original source text if score >= threshold,
    or None if score is below threshold. Uses orig_indices to remap dest offsets.

    Pitfall 2: dest_end is exclusive — use dest_end - 1 for the last char index.
    """
    if not norm_snippet or not norm_source:
        return None
    result = partial_ratio_alignment(
        norm_snippet,   # s1 = needle (shorter)
        norm_source,    # s2 = haystack (normalized source text)
        score_cutoff=threshold,
    )
    if result is None:
        return None
    # dest_start/dest_end are indices into norm_source (the haystack).
    # dest_end is exclusive; last matched char is at dest_end - 1.
    char_start = orig_indices[result.dest_start]
    char_end = orig_indices[result.dest_end - 1] + 1
    return char_start, char_end


def _ground_evidence_item(
    ev: Evidence,
    source_text: str,
    field_path: str,
    field_status: str,
) -> tuple[Evidence | None, DowngradeEntry | None]:
    """Attempt to locate ev.snippet in source_text; recompute offsets on hit.

    Returns (new_Evidence, None) on success or (None, DowngradeEntry) on failure.
    field_status carries the enclosing Field's real status value — passed in from
    ground_field so DowngradeEntry.original_status is accurate (not hardcoded).
    """
    if not ev.snippet:
        return None, DowngradeEntry(
            field_path=field_path,
            original_status=field_status,
            failed_evidence=ev,
            reason="empty snippet",
        )
    if not source_text:
        return None, DowngradeEntry(
            field_path=field_path,
            original_status=field_status,
            failed_evidence=ev,
            reason="empty source text",
        )
    if len(ev.snippet) < MIN_SNIPPET_LEN:
        return None, DowngradeEntry(
            field_path=field_path,
            original_status=field_status,
            failed_evidence=ev,
            reason=f"snippet too short ({len(ev.snippet)} < {MIN_SNIPPET_LEN})",
        )

    norm_source, orig_src_indices = _normalize_with_map(source_text)
    norm_snippet, _ = _normalize_with_map(ev.snippet)

    # Stage 1: exact match in normalized space
    hit = _match_exact(norm_snippet, norm_source, orig_src_indices)
    if hit is not None:
        char_start, char_end = hit
        return (
            Evidence(
                snippet=ev.snippet,
                char_start=char_start,
                char_end=char_end,
                source_id=ev.source_id,
            ),
            None,
        )

    # Stage 2: fuzzy fallback (D-03)
    hit = _match_fuzzy(norm_snippet, norm_source, FUZZY_THRESHOLD, orig_src_indices)
    if hit is not None:
        char_start, char_end = hit
        return (
            Evidence(
                snippet=ev.snippet,
                char_start=char_start,
                char_end=char_end,
                source_id=ev.source_id,
            ),
            None,
        )

    return None, DowngradeEntry(
        field_path=field_path,
        original_status=field_status,
        failed_evidence=ev,
        reason="snippet not locatable in source text",
    )


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

    Per D-07, sources is dict[str, str] keyed by Evidence.source_id.
    """
    # Absent states need no grounding — they carry no asserted facts
    if field.status in (FlagStatus.missing, FlagStatus.unsupported):
        return field, []

    # Conflicting field branch (Pitfall 5 from RESEARCH.md):
    # evidence lives inside each ConflictingValue, not at the top-level evidence list.
    if field.status == FlagStatus.conflicting:
        downgrade_entries: list[DowngradeEntry] = []
        new_values = []
        for cv in field.values or []:
            cv_new_evidence: list[Evidence] = []
            for ev in cv.evidence:
                source_text = sources.get(ev.source_id)
                if source_text is None:
                    downgrade_entries.append(
                        DowngradeEntry(
                            field_path=field_path,
                            original_status=field.status.value,
                            failed_evidence=ev,
                            reason="source_id not in sources",
                        )
                    )
                    continue
                new_ev, entry = _ground_evidence_item(
                    ev, source_text, field_path, field.status.value
                )
                if entry is not None:
                    downgrade_entries.append(entry)
                else:
                    assert new_ev is not None
                    cv_new_evidence.append(new_ev)
            new_values.append(cv.model_copy(update={"evidence": cv_new_evidence}))

        if downgrade_entries:
            # ponytail: any failed evidence across all ConflictingValues downgrades the
            # WHOLE Field to unsupported — intentional conservative tradeoff (D-05).
            # Partial preservation of conflicting values would create ambiguous grounding
            # state; the gate prefers to surface the conflict as unsupported and let the
            # buyer see a flag rather than partial facts.
            return EnvelopeField(status=FlagStatus.unsupported), downgrade_entries
        return field.model_copy(update={"values": new_values}), []

    # present / unclear: ground top-level evidence list
    all_entries: list[DowngradeEntry] = []
    new_evidence: list[Evidence] = []
    for ev in field.evidence:
        source_text = sources.get(ev.source_id)
        if source_text is None:
            all_entries.append(
                DowngradeEntry(
                    field_path=field_path,
                    original_status=field.status.value,
                    failed_evidence=ev,
                    reason="source_id not in sources",
                )
            )
            continue
        new_ev, entry = _ground_evidence_item(ev, source_text, field_path, field.status.value)
        if entry is not None:
            all_entries.append(entry)
        else:
            assert new_ev is not None
            new_evidence.append(new_ev)

    if all_entries:
        return EnvelopeField(status=FlagStatus.unsupported), all_entries
    return field.model_copy(update={"evidence": new_evidence}), []


def _walk_and_ground(
    obj: BaseModel,
    sources: dict[str, str],
    path: str = "",
) -> tuple[BaseModel, list[DowngradeEntry]]:
    """Recursively find every Field[T] in obj, ground each, return new obj + entries.

    Works without knowing obj's concrete type — only uses model_fields (Pattern 4).
    """
    updates: dict[str, object] = {}
    report: list[DowngradeEntry] = []

    for field_name in type(obj).model_fields:
        value = getattr(obj, field_name)
        field_path = f"{path}.{field_name}" if path else field_name

        if isinstance(value, EnvelopeField):
            grounded, entries = ground_field(value, sources, field_path)
            updates[field_name] = grounded
            report.extend(entries)

        elif isinstance(value, BaseModel):
            grounded_sub, sub_entries = _walk_and_ground(value, sources, field_path)
            updates[field_name] = grounded_sub
            report.extend(sub_entries)

        elif isinstance(value, list):
            new_list: list[object] = []
            for i, item in enumerate(value):
                item_path = f"{field_path}[{i}]"
                if isinstance(item, EnvelopeField):
                    grounded_item, item_entries = ground_field(item, sources, item_path)
                    new_list.append(grounded_item)
                    report.extend(item_entries)
                elif isinstance(item, BaseModel):
                    grounded_item, item_entries = _walk_and_ground(item, sources, item_path)
                    new_list.append(grounded_item)
                    report.extend(item_entries)
                else:
                    new_list.append(item)
            updates[field_name] = new_list

    return obj.model_copy(update=updates), report


def ground_model(
    obj: BaseModel,
    sources: dict[str, str],
) -> tuple[BaseModel, DowngradeReport]:
    """Schema-agnostic recursive walker: ground every Field[T] in a pydantic model.

    Returns a (re-grounded copy of obj, DowngradeReport). The original obj is
    never mutated (D-06). Uses pydantic v2 model_fields + model_copy (RESEARCH.md
    Pattern 4).
    """
    new_obj, entries = _walk_and_ground(obj, sources)
    return new_obj, DowngradeReport(entries=entries)
