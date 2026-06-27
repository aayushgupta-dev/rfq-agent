"""
test_llm_factory.py — Unit tests for the LLM tier factory.

Tests cover:
  - get_llm("reasoning") and get_llm("cheap") return configured chat models
  - get_llm with an unknown tier raises ValueError
  - get_llm with an unset env var raises a clear RuntimeError
  - verify_access() logic (mocked invoke — no live key required for the unit suite)
  - The API key is never present in any error message or log output

The LIVE proof (verify_access exits 0 with a real key) runs in the verification
step of Task 1, not in this unit suite.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


class TestGetLlm:
    """get_llm tier factory — import-and-call behavior (no live model required)."""

    def test_reasoning_tier_returns_chat_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm('reasoning') must return a configured chat model object."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        with patch("langchain.chat_models.init_chat_model") as mock_init:
            mock_model = MagicMock()
            mock_init.return_value = mock_model

            from llm.factory import get_llm  # noqa: PLC0415

            result = get_llm("reasoning")

        mock_init.assert_called_once_with("gpt-5.4")
        assert result is mock_model

    def test_cheap_tier_returns_chat_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm('cheap') must return a configured chat model object."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        with patch("langchain.chat_models.init_chat_model") as mock_init:
            mock_model = MagicMock()
            mock_init.return_value = mock_model

            from llm.factory import get_llm  # noqa: PLC0415

            result = get_llm("cheap")

        mock_init.assert_called_once_with("gpt-5.4-mini")
        assert result is mock_model

    def test_unknown_tier_raises_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm with an unrecognised tier must raise ValueError immediately."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        from llm.factory import get_llm  # noqa: PLC0415

        with pytest.raises(ValueError, match="Unknown tier"):
            get_llm("bogus")  # type: ignore[arg-type]

    def test_unset_reasoning_env_var_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm('reasoning') with MODEL_REASONING unset must raise a clear RuntimeError."""
        monkeypatch.delenv("MODEL_REASONING", raising=False)
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        from llm.factory import get_llm  # noqa: PLC0415

        with pytest.raises(RuntimeError, match="MODEL_REASONING"):
            get_llm("reasoning")

    def test_unset_cheap_env_var_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm('cheap') with MODEL_CHEAP unset must raise a clear RuntimeError."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.delenv("MODEL_CHEAP", raising=False)

        from llm.factory import get_llm  # noqa: PLC0415

        with pytest.raises(RuntimeError, match="MODEL_CHEAP"):
            get_llm("cheap")

    def test_api_key_not_in_error_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Error messages from get_llm must never contain the OPENAI_API_KEY value."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-key-value-that-must-not-leak")
        monkeypatch.delenv("MODEL_REASONING", raising=False)

        from llm.factory import get_llm  # noqa: PLC0415

        with pytest.raises(RuntimeError) as exc_info:
            get_llm("reasoning")

        assert "sk-secret-key-value-that-must-not-leak" not in str(exc_info.value)


class TestVerifyAccess:
    """verify_access() — behavior tests (mocked model.invoke; no live key)."""

    def test_verify_access_succeeds_when_both_models_reachable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """verify_access() must return None (no raise) when both tiers respond."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(content="ok")

        with patch("llm.factory.get_llm", return_value=mock_model):
            from llm.factory import verify_access  # noqa: PLC0415

            verify_access()  # must not raise

        assert mock_model.invoke.call_count == 2  # one call per tier

    def test_verify_access_raises_on_access_denied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """verify_access() must raise RuntimeError naming the tier + model id on access failure."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        # Simulate an access/auth error (not a param rejection)
        access_error = Exception("401 Unauthorized: model not found or no access")
        mock_model = MagicMock()
        mock_model.invoke.side_effect = access_error

        with patch("llm.factory.get_llm", return_value=mock_model):
            from llm.factory import verify_access  # noqa: PLC0415

            with pytest.raises(RuntimeError, match="No access to reasoning model"):
                verify_access()

    def test_verify_access_error_names_model_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The RuntimeError from verify_access must include the model id (not just tier)."""
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        access_error = Exception("401 Unauthorized")
        mock_model = MagicMock()
        mock_model.invoke.side_effect = access_error

        with patch("llm.factory.get_llm", return_value=mock_model):
            from llm.factory import verify_access  # noqa: PLC0415

            with pytest.raises(RuntimeError, match="gpt-5.4") as exc_info:
                verify_access()

        assert "sk-" not in str(exc_info.value)  # key must not appear

    def test_verify_access_never_leaks_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """verify_access RuntimeError must never contain the OPENAI_API_KEY value."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-super-secret-key-must-not-appear")
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("some error")

        with patch("llm.factory.get_llm", return_value=mock_model):
            from llm.factory import verify_access  # noqa: PLC0415

            with pytest.raises(RuntimeError) as exc_info:
                verify_access()

        assert "sk-super-secret-key-must-not-appear" not in str(exc_info.value)

    def test_param_rejection_not_reported_as_no_access(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A param-rejection error (e.g. unknown param) must NOT produce 'No access' message.

        PLAT-03 risk: gpt-5.4 may reject request params (Pitfall 5/A2). If verify_access
        catches a param error and reports 'No access', PLAT-03 yields a false negative.
        This test ensures param-rejection errors surface as RuntimeError but with a
        distinct message that names the param error, not 'No access to {tier} model'.
        """
        monkeypatch.setenv("MODEL_REASONING", "gpt-5.4")
        monkeypatch.setenv("MODEL_CHEAP", "gpt-5.4-mini")

        # Simulate a param rejection (HTTP 400 / InvalidRequestError pattern)
        param_error = Exception("400 Bad Request: Unknown parameter: temperature")
        mock_model = MagicMock()
        mock_model.invoke.side_effect = param_error

        with patch("llm.factory.get_llm", return_value=mock_model):
            from llm.factory import verify_access  # noqa: PLC0415

            with pytest.raises(RuntimeError) as exc_info:
                verify_access()

        # The error must NOT be the false-negative 'No access to ...' message
        assert "No access to" not in str(exc_info.value), (
            "A param-rejection error was incorrectly reported as an access-denied error. "
            "This is a false-negative for PLAT-03."
        )
        # It must still raise (something is wrong), but with a different message
        assert "400" in str(exc_info.value) or "parameter" in str(exc_info.value).lower()
