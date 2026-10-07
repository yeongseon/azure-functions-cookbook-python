"""Drift guard for the LLM-facing index files.

``llms.txt`` and ``llms-full.txt`` restate the package version, the recipe count,
and the per-category inventory. Those numbers have drifted from reality before
(the files still advertised 0.1.2 and a ``recipes/`` layout long after both were
gone). These tests derive every number from the filesystem, which is the single
source of truth, so prose and reality stay in lockstep.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
LLMS_FILES = ("llms.txt", "llms-full.txt")

CATEGORY_LABELS = {
    "apis-and-ingress": "APIs & Ingress",
    "scheduled-and-background": "Scheduled & Background",
    "blob-and-file-triggers": "Blob & File Triggers",
    "async-apis-and-jobs": "Async APIs & Jobs",
    "messaging-and-pubsub": "Messaging & Pub/Sub",
    "streams-and-telemetry": "Streams & Telemetry",
    "data-and-pipelines": "Data & Pipelines",
    "orchestration-and-workflows": "Orchestration & Workflows",
    "reliability": "Reliability",
    "security-and-tenancy": "Security & Tenancy",
    "runtime-and-ops": "Runtime & Ops",
    "realtime": "Realtime",
    "ai-and-agents": "AI & Agents",
    "guides": "Guides",
}


def _package_version() -> str:
    init = (REPO_ROOT / "src" / "azure_functions_python_cookbook" / "__init__.py").read_text(
        encoding="utf-8"
    )
    match = re.search(r'__version__ = "([^"]+)"', init)
    assert match is not None, "Could not read __version__ from the package __init__."
    return match.group(1)


def _recipe_counts() -> Counter[str]:
    return Counter(path.parent.parent.name for path in EXAMPLES_DIR.glob("*/*/recipe.yaml"))


@pytest.mark.parametrize("filename", LLMS_FILES)
def test_version_matches_package(filename: str) -> None:
    # Given: an LLM index file that restates the package version.
    text = (REPO_ROOT / filename).read_text(encoding="utf-8")

    # When: its `Version:` line is read.
    match = re.search(r"^- Version: (\S+)", text, re.MULTILINE)
    assert match is not None, f"{filename}: no `- Version: ...` line found."

    # Then: it equals the version declared by the package.
    assert match.group(1) == _package_version()


@pytest.mark.parametrize("filename", LLMS_FILES)
def test_total_recipe_count_matches_filesystem(filename: str) -> None:
    # Given: an LLM index file that advertises a recipe total.
    text = (REPO_ROOT / filename).read_text(encoding="utf-8")
    total = sum(_recipe_counts().values())

    # When/Then: the advertised total equals the discovered recipe count.
    assert f"{total} published recipes" in text, (
        f"{filename}: expected the phrase '{total} published recipes'."
    )


@pytest.mark.parametrize("filename", LLMS_FILES)
def test_no_stale_recipes_directory_reference(filename: str) -> None:
    # Given: the `recipes/` directory was replaced by `docs/patterns/`.
    text = (REPO_ROOT / filename).read_text(encoding="utf-8")

    # When/Then: no index file still points readers at the removed layout.
    assert "`recipes/`" not in text, f"{filename}: still references the removed `recipes/` layout."


def test_llms_txt_category_counts_match_filesystem() -> None:
    # Given: the compact index lists each category with a bracketed count.
    text = (REPO_ROOT / "llms.txt").read_text(encoding="utf-8")

    # When: the `- <Label> (<n>):` bullets are parsed.
    documented = {
        label: int(count) for label, count in re.findall(r"^- (.+?) \((\d+)\):", text, re.MULTILINE)
    }

    # Then: every category appears exactly once with its real recipe count.
    expected = {CATEGORY_LABELS[key]: value for key, value in _recipe_counts().items()}
    assert documented == expected


def test_llms_full_category_counts_match_filesystem() -> None:
    # Given: the full index has one `### <Label> (<n>)` section per category.
    text = (REPO_ROOT / "llms-full.txt").read_text(encoding="utf-8")

    # When: those headings are parsed.
    documented = {
        label: int(count)
        for label, count in re.findall(r"^### (.+?) \((\d+)\)$", text, re.MULTILINE)
    }

    # Then: every category appears exactly once with its real recipe count.
    expected = {CATEGORY_LABELS[key]: value for key, value in _recipe_counts().items()}
    assert documented == expected


def test_llms_full_inventory_lists_every_example_path() -> None:
    # Given: the full index claims to map every recipe to its example project.
    text = (REPO_ROOT / "llms-full.txt").read_text(encoding="utf-8")

    # When: each discovered example path is looked up in the inventory tables.
    missing = [
        path.parent.relative_to(REPO_ROOT).as_posix()
        for path in sorted(EXAMPLES_DIR.glob("*/*/recipe.yaml"))
        if f"`{path.parent.relative_to(REPO_ROOT).as_posix()}`" not in text
    ]

    # Then: none are absent.
    assert missing == [], f"llms-full.txt is missing inventory rows for: {missing}"


def test_llms_full_inventory_titles_match_recipe_metadata() -> None:
    # Given: inventory rows restate each recipe's authored title.
    text = (REPO_ROOT / "llms-full.txt").read_text(encoding="utf-8")

    # When: every recipe.yaml title is checked against its inventory row.
    mismatched: list[str] = []
    for path in sorted(EXAMPLES_DIR.glob("*/*/recipe.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        example_path = path.parent.relative_to(REPO_ROOT).as_posix()
        row = f"| {data['title']} | "
        if row not in text or f"`{example_path}` |" not in text:
            mismatched.append(example_path)

    # Then: every title is present verbatim.
    assert mismatched == [], f"llms-full.txt inventory titles out of sync for: {mismatched}"
