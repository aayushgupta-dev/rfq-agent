"""Tests for the prompt registry (Plan 01-04, PROMPT-01).

Covers:
- All 7 prompt stubs load by id with valid model_tier + non-empty intent.
- Each stub's frontmatter id matches its filename stem.
- Latest-version resolution uses injectable base_dir (tmp_path, not real prompts dir).
- Missing prompt id raises KeyError.
- Invalid prompt_id strings raise ValueError (regex guard).
"""
import pathlib

import frontmatter
import pytest

from prompts.registry import load

PROMPT_IDS = [
    "rfq-gen",
    "vendor-gen",
    "messy-data-gen",
    "ui-ux-gen",
    "extraction",
    "comparison",
    "clarification",
]

VALID_MODEL_TIERS = {"reasoning", "cheap"}


class TestAllStubsLoad:
    """All 7 stubs load with required frontmatter keys and valid values."""

    @pytest.mark.parametrize("prompt_id", PROMPT_IDS)
    def test_load_returns_post(self, prompt_id: str) -> None:
        post = load(prompt_id)
        assert post is not None

    @pytest.mark.parametrize("prompt_id", PROMPT_IDS)
    def test_intent_non_empty(self, prompt_id: str) -> None:
        post = load(prompt_id)
        intent = post.metadata.get("intent", "")
        assert isinstance(intent, str) and len(intent.strip()) > 0, (
            f"Prompt '{prompt_id}' has empty intent"
        )

    @pytest.mark.parametrize("prompt_id", PROMPT_IDS)
    def test_model_tier_valid(self, prompt_id: str) -> None:
        post = load(prompt_id)
        tier = post.metadata.get("model_tier")
        assert tier in VALID_MODEL_TIERS, (
            f"Prompt '{prompt_id}' model_tier='{tier}' not in {VALID_MODEL_TIERS}"
        )

    @pytest.mark.parametrize("prompt_id", PROMPT_IDS)
    def test_failure_handling_non_empty(self, prompt_id: str) -> None:
        post = load(prompt_id)
        fh = post.metadata.get("failure_handling", "")
        assert isinstance(fh, str) and len(fh.strip()) > 0, (
            f"Prompt '{prompt_id}' has empty failure_handling"
        )


class TestIdMatchesFilename:
    """Each stub's frontmatter id must equal the filename stem (before .vN.md)."""

    def test_id_matches_filename_stem(self) -> None:
        prompts_dir = pathlib.Path(__file__).parents[1] / "prompts"
        stubs = sorted(prompts_dir.glob("*.v*.md"))
        assert len(stubs) == 7, f"Expected 7 stubs, found {len(stubs)}: {stubs}"
        for stub_path in stubs:
            # stem is everything before the first .vN part, e.g. "extraction" from "extraction.v1.md"
            name = stub_path.name  # e.g. extraction.v1.md
            # strip ".vN.md" suffix
            stem = name.rsplit(".", 2)[0]  # extraction
            post = frontmatter.load(stub_path)
            fm_id = post.metadata.get("id")
            assert fm_id == stem, (
                f"{stub_path.name}: frontmatter id='{fm_id}' does not match filename stem='{stem}'"
            )


class TestLatestVersionResolution:
    """Latest-by-filename resolution uses injectable base_dir (tmp_path only)."""

    def test_resolves_highest_version(self, tmp_path: pathlib.Path) -> None:
        # Write two temp version files into tmp_path — no writes to the real prompts dir.
        v1 = tmp_path / "foo.v1.md"
        v2 = tmp_path / "foo.v2.md"
        v1.write_text(
            "---\nid: foo\nversion: 1\nintent: test\nmodel_tier: cheap\nfailure_handling: none\n---\nbody v1\n"
        )
        v2.write_text(
            "---\nid: foo\nversion: 2\nintent: test\nmodel_tier: cheap\nfailure_handling: none\n---\nbody v2\n"
        )
        post = load("foo", base_dir=tmp_path)
        assert post.metadata["version"] == 2, (
            f"Expected version 2, got {post.metadata['version']}"
        )

    def test_no_writes_to_real_prompts_dir(self, tmp_path: pathlib.Path) -> None:
        """Ensure the tmp_path test above doesn't pollute the real prompts directory."""
        prompts_dir = pathlib.Path(__file__).parents[1] / "prompts"
        before = set(prompts_dir.glob("foo.v*.md"))
        assert len(before) == 0, (
            "Unexpected 'foo' prompt found in real prompts dir — test isolation broken"
        )


class TestMissingPrompt:
    """Requesting an unknown prompt id raises KeyError."""

    def test_missing_prompt_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="no prompt 'does-not-exist'"):
            load("does-not-exist")


class TestInvalidPromptId:
    """Invalid prompt_id values raise ValueError (regex guard before glob)."""

    def test_path_traversal_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="invalid prompt_id"):
            load("../etc/passwd")

    def test_spaces_raise_value_error(self) -> None:
        with pytest.raises(ValueError, match="invalid prompt_id"):
            load("foo bar")

    def test_uppercase_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="invalid prompt_id"):
            load("Extraction")
