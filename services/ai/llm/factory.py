"""
factory.py — LLM tier factory for the Bid Desk AI service (D-15, D-16).

Provides:
  get_llm(tier) — returns a configured LangChain chat model for the given tier.
                  Tiers: "reasoning" -> MODEL_REASONING env var (gpt-5.4)
                          "cheap"     -> MODEL_CHEAP env var (gpt-5.4-mini)
  verify_access() — live-pings both models; raises RuntimeError naming the
                    failing tier + model id on access failure (PLAT-03).

Model IDs are always read from env, enforcing the gpt-5.4/mini-never-5.5
discipline in one place (D-15). Callers pass a tier string — never a model id.

Security: no code path in this module interpolates the API key into any
message, log, or exception string (T-03-01 mitigation).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load the repo-root .env at module import time.
# factory.py lives at: services/ai/llm/factory.py
# repo root is three levels up.
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

# Tier -> env var name mapping (D-15).
_TIER_ENV: dict[str, str] = {
    "reasoning": "MODEL_REASONING",
    "cheap": "MODEL_CHEAP",
}

# HTTP status substrings and keywords that indicate a true access-denied /
# unknown-model error vs. a request-parameter rejection (Pitfall 5 / A2).
# gpt-5.4 reasoning models may reject params like temperature or max_tokens.
# A param rejection (HTTP 400 / InvalidRequestError) must NOT be reported as
# "No access" — that would be a false-negative for the PLAT-03 access check.
_PARAM_REJECTION_MARKERS = (
    "400",
    "bad request",
    "invalid request",
    "unknown parameter",
    "unsupported parameter",
    "unrecognized parameter",
    "extra inputs",
)


def get_llm(tier: Literal["reasoning", "cheap"]):  # noqa: ANN201
    """Return a configured LangChain chat model for the requested tier.

    Args:
        tier: "reasoning" (gpt-5.4) or "cheap" (gpt-5.4-mini).

    Returns:
        A LangChain chat model instance returned by init_chat_model(model_id).

    Raises:
        ValueError: tier is not "reasoning" or "cheap".
        RuntimeError: the tier's env var is unset.
    """
    if tier not in _TIER_ENV:
        raise ValueError(f"Unknown tier {tier!r}. Must be 'reasoning' or 'cheap'.")

    env_var = _TIER_ENV[tier]
    model_id = os.environ.get(env_var)
    if not model_id:
        raise RuntimeError(
            f"Env var {env_var!r} is not set. "
            f"Set it to the model id for the '{tier}' tier (e.g. gpt-5.4)."
        )

    return init_chat_model(model_id)


def _is_param_rejection(exc: Exception) -> bool:
    """Return True if exc looks like a request-parameter rejection (HTTP 400).

    Used by verify_access to distinguish access-denied from param errors so
    PLAT-03 does not produce false-negatives (Pitfall 5 / A2).
    """
    msg = str(exc).lower()
    return any(marker in msg for marker in _PARAM_REJECTION_MARKERS)


def verify_access() -> None:
    """Live-ping both model tiers and raise on access failure.

    Calls get_llm(tier).invoke(<minimal ping>) for each tier.

    Error categorization (PLAT-03 / Pitfall 5 / A2):
      - A true access-denied / unknown-model error (401, 403, "model not found",
        etc.) raises RuntimeError("No access to {tier} model ({model_id}): ...")
      - A request-parameter rejection (HTTP 400 / "unknown parameter") is a
        different failure class and raises RuntimeError("Param error ...") so
        callers can distinguish it from a missing-access finding.

    Security: the OPENAI_API_KEY value is never included in any message or log.

    Raises:
        RuntimeError: access is denied / model unknown, OR a param error occurred.
                      The message names the tier and model id but never the key.
    """
    # ponytail: verify_access is deliberately kept as a single function despite
    # two tiers — the ping loop is trivial and splitting it adds no clarity.
    for tier in ("reasoning", "cheap"):
        env_var = _TIER_ENV[tier]
        model_id = os.environ.get(env_var, "<unset>")
        logger.info("Pinging %s model (tier=%s) ...", model_id, tier)
        try:
            model = get_llm(tier)  # type: ignore[arg-type]
            # Minimal ping: a single human message — no extra params that
            # reasoning models may reject (Pitfall 5: avoid temperature / max_tokens).
            model.invoke("ping")
        except RuntimeError:
            # Re-raise env-var errors from get_llm directly.
            raise
        except Exception as exc:
            if _is_param_rejection(exc):
                raise RuntimeError(
                    f"Param error pinging {tier} model ({model_id}): {exc}. "
                    "Check that the minimal-ping request uses no unsupported parameters."
                ) from exc
            raise RuntimeError(f"No access to {tier} model ({model_id}): {exc}") from exc
        logger.info("OK: %s model accessible (tier=%s)", model_id, tier)
