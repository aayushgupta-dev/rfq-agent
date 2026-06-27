"""
codegen.py — Mechanically regenerate packages/shared-types/index.d.ts from pydantic schemas.

Usage (from services/ai/):
    uv run python scripts/codegen.py

This script resolves the repo root by walking up from __file__ until it finds
pnpm-workspace.yaml — avoiding the fragile parents[N] index that would resolve
services/ai/scripts/ -> services/ instead of the repo root.

The repo_root() helper is exported so test_codegen_drift.py imports it directly
rather than recomputing the path independently (D-14, MEDIUM review fix).

Output: <repo_root>/packages/shared-types/index.d.ts
The committed file is the generated contract — never hand-edit it (PLAT-02).
"""
from __future__ import annotations

import re
from pathlib import Path

from pydantic2ts import generate_typescript_defs


def repo_root() -> Path:
    """Walk up from this file until pnpm-workspace.yaml is found.

    This is more robust than a hard-coded parents[N] index, which breaks if the
    script is moved or the directory depth changes.

    Raises RuntimeError if the marker file is not found (would indicate an
    unexpected repo layout).
    """
    current = Path(__file__).resolve().parent
    while True:
        if (current / "pnpm-workspace.yaml").exists():
            return current
        parent = current.parent
        if parent == current:
            raise RuntimeError(
                "Could not locate repo root (pnpm-workspace.yaml not found). "
                "Run this script from within the aerchain monorepo."
            )
        current = parent


def _strip_empty_interfaces(ts_text: str) -> str:
    """Remove empty exported interfaces that pydantic2ts occasionally emits.

    When a shared extra='forbid' base leaks as an empty interface, strip it.
    This is a defensive post-gen pass — per-model model_config should prevent it,
    but belt-and-suspenders given the Pitfall 3 warning in RESEARCH.md.
    """
    # Match: export interface Name {} (with optional leading whitespace/newline)
    return re.sub(r"\nexport interface \w+ \{\}\n", "\n", ts_text)


def schemas_path() -> Path:
    """Return the absolute path to services/ai/schemas/__init__.py.

    pydantic2ts's _import_module checks os.path.exists(path) first — if the
    path is a directory name like "schemas" and that directory exists in cwd,
    it tries spec_from_file_location which fails for packages. Passing the
    absolute __init__.py path reliably triggers the file-loading branch.
    """
    return Path(__file__).resolve().parent.parent / "schemas" / "__init__.py"


def generate(out_path: Path | None = None) -> Path:
    """Regenerate the TypeScript contract from the pydantic schemas.

    Args:
        out_path: destination .d.ts file. Defaults to the canonical location
                  <repo_root>/packages/shared-types/index.d.ts.

    Returns:
        The resolved output path.
    """
    root = repo_root()
    dest = out_path or (root / "packages" / "shared-types" / "index.d.ts")
    json2ts_bin = root / "node_modules" / ".bin" / "json2ts"

    generate_typescript_defs(
        str(schemas_path()),
        str(dest),
        json2ts_cmd=str(json2ts_bin),
    )

    # Post-process: strip any empty interfaces that leaked through
    text = dest.read_text()
    cleaned = _strip_empty_interfaces(text)
    if cleaned != text:
        dest.write_text(cleaned)

    return dest


if __name__ == "__main__":
    out = generate()
    print(f"Generated: {out}")
