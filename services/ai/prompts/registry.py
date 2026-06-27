"""Prompt Pack registry — loads versioned .md prompt files by id.

Design decisions realised here:
  D-11: each prompt is a .md file with YAML frontmatter (id, version, intent, model_tier,
        failure_handling) + markdown body, loaded by id.
  D-12: versioning via filename suffix (extraction.v1.md); _find_latest resolves the
        highest-version file.  # ponytail: latest-by-suffix exists for D-12; do not add caching.
  D-13: all 7 stubs created in Phase 1 and loadable from this registry.

Usage:
    from prompts.registry import load
    post = load("extraction")
    print(post.metadata["intent"])
    print(post.content)
"""

import pathlib
import re

import frontmatter

_DIR = pathlib.Path(__file__).resolve().parent

# Matches e.g. "extraction.v1.md" → groups id="extraction", n="1"
_VER_RE = re.compile(r"^(?P<id>.+)\.v(?P<n>\d+)\.md$")

# Prompt ids must be lowercase alphanumeric + hyphens only (guards against path traversal).
_ID_RE = re.compile(r"^[a-z0-9-]+$")


def _find_latest(prompt_id: str, base_dir: pathlib.Path) -> pathlib.Path:
    """Return the highest-version .md file for prompt_id in base_dir.

    # ponytail: latest-by-suffix exists for D-12 versioning; do not add caching.

    Raises:
        KeyError: if no matching file is found.
    """
    candidates: list[tuple[int, pathlib.Path]] = []
    for p in base_dir.glob(f"{prompt_id}.v*.md"):
        m = _VER_RE.match(p.name)
        if m and m["id"] == prompt_id:
            candidates.append((int(m["n"]), p))
    if not candidates:
        raise KeyError(f"no prompt '{prompt_id}'")
    _, path = max(candidates)
    return path


def load(prompt_id: str, base_dir: pathlib.Path = _DIR) -> frontmatter.Post:
    """Load a prompt by id, resolving to the latest version in base_dir.

    Args:
        prompt_id: lowercase-alphanumeric-hyphen id (e.g. "extraction").
        base_dir:  directory to search; defaults to the real prompts directory.
                   Pass a tmp_path in tests to avoid writing to the real dir.

    Returns:
        A ``frontmatter.Post`` with .metadata (dict) and .content (str).

    Raises:
        ValueError: if prompt_id does not match ``^[a-z0-9-]+$``.
        KeyError:   if no file matching ``{prompt_id}.v*.md`` exists in base_dir.
    """
    if not _ID_RE.fullmatch(prompt_id):
        raise ValueError(f"invalid prompt_id '{prompt_id}': must match ^[a-z0-9-]+$")
    file_path = _find_latest(prompt_id, base_dir)
    return frontmatter.load(file_path)
