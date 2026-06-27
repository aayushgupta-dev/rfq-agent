"""
verify_access.py — Standalone CLI for the PLAT-03 access proof (D-16).

Run this script once during project setup to confirm the org/key has live
access to both gpt-5.4 (reasoning) and gpt-5.4-mini (cheap) before any agent
is built on them. This is the first half of D-16; the second half is the
FastAPI lifespan startup check in api/app.py.

Usage:
    cd services/ai && uv run python scripts/verify_access.py

Exit codes:
    0 — both models accessible; prints the model IDs that were checked.
    1 — access failed; prints the error message (never the API key value).

Security: model IDs are logged; OPENAI_API_KEY is never printed or logged.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the services/ai package root is on the import path when run as a script.
_pkg_root = Path(__file__).resolve().parents[1]
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from llm.factory import _TIER_ENV, verify_access  # noqa: E402


def main() -> None:
    reasoning_id = os.environ.get(_TIER_ENV["reasoning"], "<unset>")
    cheap_id = os.environ.get(_TIER_ENV["cheap"], "<unset>")

    print("Bid Desk — OpenAI model access check (PLAT-03)")
    print(f"  reasoning model : {reasoning_id}")
    print(f"  cheap model     : {cheap_id}")
    print()

    try:
        verify_access()
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)

    print("PASS: both models are accessible.")


if __name__ == "__main__":
    main()
