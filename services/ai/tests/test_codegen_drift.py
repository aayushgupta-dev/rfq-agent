"""
Drift-check test for the pydantic → TypeScript contract (D-14, PLAT-02).

Regenerates packages/shared-types/index.d.ts into a temp directory and asserts
byte-equality with the committed file. A stale or hand-edited contract turns this
test red — the "never hand-mirrored" rule is code-enforced, not advisory.

Uses repo_root() imported from scripts.codegen so path resolution is centralized.
Running this test against a freshly generated committed file must pass.
Running it after adding a pydantic field without re-running codegen must fail.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from scripts.codegen import generate, repo_root


def test_ts_contract_not_stale() -> None:
    """Generated TS must be byte-identical to the committed file.

    If this test fails:
      1. Run: cd services/ai && uv run python scripts/codegen.py
      2. Commit: packages/shared-types/index.d.ts
      3. Re-run this test — it should pass.
    """
    committed = repo_root() / "packages" / "shared-types" / "index.d.ts"
    assert committed.exists(), f"Committed TS contract not found at {committed}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_out = Path(tmp_dir) / "index.d.ts"
        generate(out_path=tmp_out)

        generated_text = tmp_out.read_text()
        committed_text = committed.read_text()

        assert generated_text == committed_text, (
            "TS contract is stale — run scripts/codegen.py and commit "
            "packages/shared-types/index.d.ts\n\n"
            f"Committed file: {committed}\n"
            f"Regenerated to: {tmp_out}"
        )
