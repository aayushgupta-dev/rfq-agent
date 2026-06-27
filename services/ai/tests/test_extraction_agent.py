"""
test_extraction_agent.py — RED test stubs for Phase 3 extraction agent (Wave 0).

All 9 tests are marked @pytest.mark.xfail(strict=True) — they must FAIL until
the corresponding implementation plan executes. pytest reports them as XFAIL
(expected failure), not ERROR.

test_truncation_live_guard is additionally marked @pytest.mark.live so it is
skipped in normal CI (needs a real OpenAI key + langchain-openai installed).
Run with `uv run pytest -m live` to validate the RESEARCH.md MEDIUM-confidence
assumption that the installed langchain-openai raises LengthFinishReasonError on
finish_reason=length truncation.

One-to-one mapping with 03-VALIDATION.md Per-Task Verification Map:
  test_schema_shape               → EXTRACT-01
  test_walker_covers_all_fields   → walker / IN-04
  test_evidence_required          → EXTRACT-02
  test_truncation_raises_error_event → EXTRACT-05 (truncation path)
  test_refusal_raises_error_event    → EXTRACT-05 (refusal path)
  test_missing_line_items_surface_as_missing → EXTRACT-01/03
  test_sse_event_taxonomy         → SSE taxonomy
  test_traces_committed           → PROMPT-03 / D-13..D-15
  test_truncation_live_guard      → EXTRACT-05 live guard
"""
from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from conftest_extraction import fabricated_field, missing_field, present_field
from grounding.gate import ground_model
from grounding.report import DowngradeReport
from openai import LengthFinishReasonError
from schemas.domain import ExtractionResult
from schemas.envelope import Evidence, Field, FlagStatus
from schemas.events import EVENT_TYPES


# ---------------------------------------------------------------------------
# 1. Schema shape
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-02 not yet executed — ExtractionResult is still a stub", strict=True)
def test_schema_shape() -> None:
    """ExtractionResult must cover all 8 extraction categories; vendor_name is plain str (D-05).

    The current stub has vendor_name: Field[str] — Phase 3 corrects it to plain str.
    """
    fields = ExtractionResult.model_fields

    # vendor_name must be plain str, NOT a Field wrapper (D-05)
    assert "vendor_name" in fields
    annotation = fields["vendor_name"].annotation
    # Field[str] would have __origin__ == Field; plain str is just str
    assert annotation is str, (
        f"vendor_name must be plain str, not {annotation!r} — "
        "it is known provenance metadata, not an extracted fact (D-05)"
    )

    # All 8 extraction categories must be present
    required_fields = {
        "scope_summary",
        "line_items",
        "pricing_structure",
        "total_price",
        "commercial_terms",
        "timeline",
        "compliance_points",
        "assumptions",
        "exclusions",
        "risks",
    }
    missing = required_fields - set(fields.keys())
    assert not missing, f"ExtractionResult is missing fields: {missing}"


# ---------------------------------------------------------------------------
# 2. Walker coverage (IN-04 / B-R1)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-02 not yet executed — ExtractionResult is still a stub", strict=True)
def test_walker_covers_all_fields() -> None:
    """Every Field[T] in ExtractionResult must be visited by _walk_and_ground.

    Approach (B-R1 redesign — model_fields enumeration):
      1. Build an ExtractionResult where every Field[T] attribute is fabricated_field()
         (a present field with a snippet guaranteed unlocatable in the source).
      2. Call ground_model(..., {"src": "harmless source text that contains nothing"}).
      3. Enumerate expected_paths by recursively walking model_fields.
      4. Assert the set of field_path values in report.entries == expected_paths.

    This proves the walker visited every Field[T] regardless of grounding outcome.
    NOTE: all-missing ExtractionResult CANNOT be used — ground_field early-returns on
    missing with 0 entries, so the assertion would be trivially vacuous (0 == 0).
    """
    # Import here to avoid collection errors if ExtractionResult is still the stub
    from schemas.domain import ExtractionResult, LineItemExtraction  # type: ignore[attr-defined]

    def _collect_field_paths(model_cls: type, prefix: str = "") -> set[str]:
        """Recursively enumerate dotted paths for every Field[T]-typed attribute."""
        paths: set[str] = set()
        import typing
        for name, field_info in model_cls.model_fields.items():
            path = f"{prefix}.{name}" if prefix else name
            ann = field_info.annotation
            origin = getattr(ann, "__origin__", None)

            # Direct Field[T]
            if origin is Field or (isinstance(ann, type) and issubclass(ann, Field)):
                paths.add(path)
            # list[Field[T]] or list[SomeModel]
            elif origin is list:
                args = getattr(ann, "__args__", ())
                if args:
                    inner = args[0]
                    inner_origin = getattr(inner, "__origin__", None)
                    if inner_origin is Field or (isinstance(inner, type) and issubclass(inner, Field)):
                        # list[Field[T]] — we'll add a [0] path placeholder
                        paths.add(f"{path}[0]")
                    elif isinstance(inner, type) and hasattr(inner, "model_fields"):
                        # list[SomeModel] — recurse into the element model
                        sub = _collect_field_paths(inner, f"{path}[0]")
                        paths.update(sub)
            # Nested BaseModel
            elif isinstance(ann, type) and hasattr(ann, "model_fields"):
                sub = _collect_field_paths(ann, path)
                paths.update(sub)
        return paths

    expected_paths = _collect_field_paths(ExtractionResult)
    assert expected_paths, "expected_paths must not be empty — ExtractionResult has no Field[T]?"

    # Build a minimal ExtractionResult with one fabricated LineItemExtraction so list
    # paths are covered; all fields set to fabricated_field() so every visit downgrades.
    li = LineItemExtraction(
        line_item_id="li-01",
        line_item_name="Test",
        pricing=fabricated_field("XYZNOTFOUND_VALUE"),
        scope_coverage=fabricated_field("XYZNOTFOUND_VALUE"),
    )
    result = ExtractionResult(
        vendor_name="test",
        scope_summary=fabricated_field("XYZNOTFOUND_VALUE"),
        line_items=[li],
        pricing_structure=fabricated_field("XYZNOTFOUND_VALUE"),
        total_price=fabricated_field("XYZNOTFOUND_VALUE"),
        commercial_terms=fabricated_field("XYZNOTFOUND_VALUE"),
        timeline=fabricated_field("XYZNOTFOUND_VALUE"),
        compliance_points=[fabricated_field("XYZNOTFOUND_VALUE")],
        assumptions=[fabricated_field("XYZNOTFOUND_VALUE")],
        exclusions=[fabricated_field("XYZNOTFOUND_VALUE")],
        risks=[fabricated_field("XYZNOTFOUND_VALUE")],
    )

    _, report = ground_model(result, {"src": "harmless source text containing nothing relevant"})
    visited_paths = {e.field_path for e in report.entries}
    assert visited_paths == expected_paths, (
        f"Walker missed fields.\n"
        f"  Expected : {sorted(expected_paths)}\n"
        f"  Visited  : {sorted(visited_paths)}\n"
        f"  Missing  : {sorted(expected_paths - visited_paths)}\n"
        f"  Extra    : {sorted(visited_paths - expected_paths)}"
    )


# ---------------------------------------------------------------------------
# 3. Evidence required (EXTRACT-02)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-02 not yet executed — ExtractionResult is still a stub", strict=True)
def test_evidence_required() -> None:
    """A present field with a genuine verbatim snippet must survive grounding with status=present."""
    from schemas.domain import ExtractionResult

    source_text = "some text verbatim quote from source more text"
    scope = present_field("X", "verbatim quote from source", source_id="src")

    result = ExtractionResult(
        vendor_name="test",
        scope_summary=scope,
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
    grounded, report = ground_model(result, {"src": source_text})
    assert grounded.scope_summary.status == FlagStatus.present, (  # type: ignore[attr-defined]
        f"Genuine verbatim snippet should survive grounding; got {grounded.scope_summary.status}"  # type: ignore[attr-defined]
    )


# ---------------------------------------------------------------------------
# 4. Truncation → error event (EXTRACT-05)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-03 not yet executed — extraction agent not yet built", strict=True)
def test_truncation_raises_error_event() -> None:
    """LengthFinishReasonError from the LLM chain must produce error event with recoverable=True.

    The extraction graph must catch truncation, emit error SSE event with
    {code, message, recoverable: true}, and NOT parse any partial output.
    """
    # Import inside body — agents.extraction does not exist until Plan 03-03
    from agents.extraction import run_extraction  # type: ignore[import-not-found]

    with patch("agents.extraction._chain") as mock_chain:
        mock_chain.invoke.side_effect = LengthFinishReasonError(
            message="finish_reason=length — output truncated",
            response=MagicMock(),
        )
        state = run_extraction(
            vendor_response=MagicMock(),
            rfq=MagicMock(),
        )

    assert state.get("error") == "truncated", (
        f"State must have error='truncated' on truncation, got {state.get('error')!r}"
    )
    assert state.get("result") is None, "No parsed ExtractionResult should exist on truncation"

    # Last SSE chunk must be an error event with recoverable=True
    last_event = state.get("last_sse_event")
    assert last_event is not None
    assert last_event["type"] == "error"
    assert last_event["payload"]["recoverable"] is True


# ---------------------------------------------------------------------------
# 5. Refusal → error event (EXTRACT-05)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-03 not yet executed — extraction agent not yet built", strict=True)
def test_refusal_raises_error_event() -> None:
    """A model refusal must produce error event with recoverable=False; no ExtractionResult parsed.

    Detection path (RESEARCH.md): include_raw=True → raw AIMessage →
    additional_kwargs["refusal"] is non-None and parsed is None.
    """
    from agents.extraction import run_extraction  # type: ignore[import-not-found]

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {"refusal": "I cannot process this request."}

    with patch("agents.extraction._chain") as mock_chain:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": None}
        state = run_extraction(
            vendor_response=MagicMock(),
            rfq=MagicMock(),
        )

    assert state.get("error") == "refusal", (
        f"State must have error='refusal' on model refusal, got {state.get('error')!r}"
    )
    assert state.get("result") is None, "No parsed ExtractionResult should exist on refusal"

    last_event = state.get("last_sse_event")
    assert last_event is not None
    assert last_event["type"] == "error"
    assert last_event["payload"]["recoverable"] is False


# ---------------------------------------------------------------------------
# 6. Missing line items surface as missing (EXTRACT-01/03)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-03 not yet executed — extraction agent not yet built", strict=True)
def test_missing_line_items_surface_as_missing() -> None:
    """A LineItemExtraction with missing pricing/scope_coverage must propagate through SSE result.

    The SSE 'result' event payload must carry line items with missing status
    intact — they must never be collapsed to None or omitted.
    """
    from agents.extraction import run_extraction  # type: ignore[import-not-found]
    from schemas.domain import ExtractionResult, LineItemExtraction  # type: ignore[attr-defined]

    li = LineItemExtraction(
        line_item_id="li-01",
        line_item_name="Strategy & Creative",
        pricing=missing_field(),
        scope_coverage=missing_field(),
    )
    canned_result = ExtractionResult(
        vendor_name="test",
        scope_summary=missing_field(),
        line_items=[li],
        pricing_structure=missing_field(),
        total_price=missing_field(),
        commercial_terms=missing_field(),
        timeline=missing_field(),
        compliance_points=[],
        assumptions=[],
        exclusions=[],
        risks=[],
    )

    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    with patch("agents.extraction._chain") as mock_chain:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_result}
        state = run_extraction(
            vendor_response=MagicMock(),
            rfq=MagicMock(),
        )

    result_event = state.get("result_sse_event")
    assert result_event is not None, "A 'result' SSE event must be emitted"
    assert result_event["type"] == "result"

    # The payload must carry the extraction result with missing line item fields intact
    payload = result_event["payload"]
    line_items = payload.get("line_items", [])
    assert len(line_items) >= 1, "At least one line item must appear in result payload"
    li_payload = line_items[0]
    assert li_payload.get("pricing", {}).get("status") == "missing", (
        "Missing pricing must propagate through SSE result as status='missing'"
    )
    assert li_payload.get("scope_coverage", {}).get("status") == "missing", (
        "Missing scope_coverage must propagate through SSE result as status='missing'"
    )


# ---------------------------------------------------------------------------
# 7. SSE event taxonomy (B-R4)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-03 not yet executed — /extract/vendor route not yet built", strict=True)
def test_sse_event_taxonomy() -> None:
    """All emitted SSE event types from /extract/vendor must be in EVENT_TYPES.

    Patches agents.extraction._chain so no live API call is made.
    Uses TestClient without lifespan (no startup access check).
    """
    # Import inside body — api.app route and agents.extraction don't exist yet
    from api.app import app  # type: ignore[import-not-found]
    from agents.extraction import _chain  # type: ignore[import-not-found,attr-defined] # noqa: F401
    from schemas.domain import ExtractionResult, VendorResponse, RFQ

    from fastapi.testclient import TestClient

    # Build a minimal canned ExtractionResult (all fields missing)
    canned_result = ExtractionResult(
        vendor_name="test",
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
    raw_msg = MagicMock()
    raw_msg.additional_kwargs = {}

    with patch("agents.extraction._chain") as mock_chain:
        mock_chain.invoke.return_value = {"raw": raw_msg, "parsed": canned_result}

        client = TestClient(app, raise_server_exceptions=True)
        # Minimal valid request body — exact schema determined by Plan 03-03
        body = {
            "vendor_response": {
                "vendor_name": "Test Vendor",
                "persona": "test",
                "mess_spec": [],
                "source_id": "src",
                "format_label": "text",
                "raw_text": "Test vendor response text.",
            },
            "rfq": {
                "title": "Test RFQ",
                "client_name": "Test Client",
                "issue_date": "2026-01-01",
                "response_deadline": "2026-02-01",
                "scope_summary": "Test scope",
                "line_items": [],
                "commercial_expectations": "Best value",
            },
        }
        response = client.post("/extract/vendor", json=body)

    assert response.status_code == 200

    # Parse SSE events from response body
    events: list[dict] = []
    for line in response.text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            payload_str = line[len("data: "):]
            if payload_str:
                events.append(json.loads(payload_str))

    assert events, "At least one SSE event must be emitted"
    for i, event in enumerate(events):
        assert event["type"] in EVENT_TYPES, (
            f"Event {i} type {event['type']!r} not in EVENT_TYPES {EVENT_TYPES}"
        )


# ---------------------------------------------------------------------------
# 8. Traces committed (PROMPT-03 / D-13..D-15)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-04 not yet executed — trace capture not yet run", strict=True)
def test_traces_committed() -> None:
    """docs/traces/ must contain >=3 JSON trace files with the required structure (D-13..D-15).

    Each trace must have keys: input, resolved_prompt, raw_model_output,
    grounding_step, final_result.

    At least one trace must have a non-empty grounding_step.downgrade_report.entries
    to prove a genuine code-enforced downgrade occurred (D-15 machine-verifiable).
    """
    traces_dir = pathlib.Path(__file__).parents[3] / "docs" / "traces"
    assert traces_dir.exists(), f"docs/traces/ directory must exist at {traces_dir}"

    json_traces = sorted(traces_dir.glob("*.json"))
    assert len(json_traces) >= 3, (
        f"Expected >=3 trace JSON files in {traces_dir}, found {len(json_traces)}"
    )

    required_keys = {"input", "resolved_prompt", "raw_model_output", "grounding_step", "final_result"}
    for trace_path in json_traces:
        with trace_path.open() as f:
            trace = json.load(f)
        missing_keys = required_keys - set(trace.keys())
        assert not missing_keys, (
            f"{trace_path.name} is missing keys: {missing_keys}"
        )

    # D-15: at least one trace must show a genuine downgrade (non-empty entries)
    has_genuine_downgrade = any(
        len(
            json.loads(p.read_text()).get("grounding_step", {})
            .get("downgrade_report", {})
            .get("entries", [])
        ) > 0
        for p in json_traces
    )
    assert has_genuine_downgrade, (
        "At least one trace must have a non-empty grounding_step.downgrade_report.entries "
        "(D-15: code-enforced downgrade must be demonstrated on real model runs)"
    )


# ---------------------------------------------------------------------------
# 9. Live truncation guard (B-R2 — RESEARCH.md MEDIUM-confidence assumption)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Plan 03-03 not yet executed — agents.extraction._chain not yet built", strict=True)
@pytest.mark.live
def test_truncation_live_guard() -> None:
    """Live guard: confirms installed langchain-openai raises LengthFinishReasonError on truncation.

    Validates the RESEARCH.md MEDIUM-confidence assumption (open bugs #29700/#25510).
    Skipped in normal CI. Run with `uv run pytest -m live` against a real OpenAI key.

    # ponytail: live guard for RESEARCH.md Pattern 2 MEDIUM-confidence open-bug assumption
    # (#29700/#25510). Skipped in CI. Run with `uv run pytest -m live` to validate against
    # the installed langchain-openai before shipping EXTRACT-05.
    """
    from agents.extraction import _chain  # type: ignore[import-not-found,attr-defined]

    with pytest.raises(LengthFinishReasonError):
        _chain.invoke(
            {"vendor_text": "x" * 50000, "rfq_line_items": ""},
            config={"max_tokens": 1},
        )
