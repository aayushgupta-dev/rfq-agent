"""
generate_samples.py — Developer CLI to generate and commit sample data fixtures.

Usage (from services/ai/):
    uv run python scripts/generate_samples.py

Requires OPENAI_API_KEY in .env (loaded automatically via llm.factory).

This script makes live OpenAI API calls to generate:
  - data/rfq.json    — the marketing-services RFQ (via rfq-gen prompt)
  - data/rfq.md      — the same RFQ rendered as Markdown (for vendor context)
  - data/vendor_thorough.json  — thorough-but-pricey persona fixture
  - data/vendor_cheap.json     — cheap-but-incomplete persona fixture
  - data/vendor_fluff.json     — polished-fluff persona fixture

CI validates committed fixtures only (D-13); this script is a developer tool
for regenerating them when the prompts or schemas change.

Filenames come from agents.vendor_gen.FIXTURE_FILENAMES — never derived via
persona.replace("-", "_") so the short names (vendor_thorough.json etc.) stay
authoritative and in sync with test_sample_fixtures.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agents.rfq_gen import generate_rfq, render_rfq_md
from agents.vendor_gen import FIXTURE_FILENAMES, MESS_SPECS, generate_vendor_response
from llm.factory import get_llm
from scripts.codegen import repo_root


def _check_api_access() -> None:
    """Verify OpenAI API is reachable before running expensive generation.

    Calls get_llm("reasoning").invoke("ping") with a minimal prompt.
    Fails fast with a clear message if the key is missing or invalid.
    The API key value is NEVER included in any error message (T-02-12).
    """
    try:
        get_llm("reasoning").invoke("ping")
    except Exception as e:
        # Do not include the API key value in the error message (T-02-12 mitigation).
        print(
            f"ERROR: Cannot reach OpenAI API. Check OPENAI_API_KEY in .env. Details: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Generate all sample data fixtures and write them to data/."""
    print("Checking API access...")
    _check_api_access()
    print("API access OK.")

    print("Generating RFQ...")
    rfq = generate_rfq()
    print(f"  RFQ generated: {rfq.title!r} ({len(rfq.line_items)} line items)")

    data_dir: Path = repo_root() / "data"
    data_dir.mkdir(exist_ok=True)

    rfq_json_path = data_dir / "rfq.json"
    rfq_json_path.write_text(rfq.model_dump_json(indent=2))
    print(f"  wrote rfq.json")

    rfq_md = render_rfq_md(rfq)
    rfq_md_path = data_dir / "rfq.md"
    rfq_md_path.write_text(rfq_md)
    print(f"  wrote rfq.md")

    print("Generating vendor responses...")
    for persona in list(FIXTURE_FILENAMES.keys()):
        print(f"  generating {persona}...")
        vendor = generate_vendor_response(rfq_md, persona, MESS_SPECS[persona])
        filename = FIXTURE_FILENAMES[persona]
        (data_dir / filename).write_text(vendor.model_dump_json(indent=2))
        print(f"  wrote {filename} ({len(vendor.raw_text)} chars)")

    print("Done — fixtures written to data/")


if __name__ == "__main__":
    main()
