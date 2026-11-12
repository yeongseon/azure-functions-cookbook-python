"""Guard the user-facing release story: snapshots, never a PyPI package.

The cookbook releases tagged GitHub recipe snapshots. These tests keep the README (and its
translations), CONTRIBUTING, AGENTS and the release docs from claiming PyPI publication, manual
release steps or Release facts that contradict the workflows, ``pyproject.toml`` or each other.
"""

from __future__ import annotations

from pathlib import Path
import re
import tomllib

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
READMES = sorted(ROOT.glob("README*.md"))
POLICY_DOCS = [
    ROOT / "CONTRIBUTING.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "release_process.md",
    ROOT / "docs" / "snapshots-and-verification.md",
]
ALL_DOCS = [
    *READMES,
    ROOT / "SECURITY.md",
    *POLICY_DOCS,
    *(
        path
        for path in sorted((ROOT / "docs").glob("*.md"))
        if path.name not in {"changelog.md", "roadmap.md"}
    ),
]
_NEGATION = re.compile(r"\b(not|no|nothing|never|neither|without|rather than|instead of)\b", re.I)
_PUBLISH_CLAIM = re.compile(
    r"\b(published|available|distributed|released)\s+(on|to|via|in)\s+PyPI", re.I
)
_INSTALL_COOKBOOK = re.compile(
    r"(pip|uv pip|pipx)\s+install\s+[^\n`]*azure[-_]functions[-_](python[-_])?cookbook", re.I
)
_MANUAL_RELEASE = re.compile(
    r"twine upload|hatch publish|make (release|tag-release|publish-pypi)\b|git tag -a v", re.I
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unique(paths: list[Path]) -> list[Path]:
    return list(dict.fromkeys(paths))


@pytest.mark.parametrize("path", _unique(ALL_DOCS), ids=lambda p: str(p.relative_to(ROOT)))
def test_docs_never_claim_the_cookbook_is_on_pypi(path: Path) -> None:
    for number, line in enumerate(_text(path).splitlines(), start=1):
        assert not _INSTALL_COOKBOOK.search(line), (
            f"{path.name}:{number} tells readers to pip install the cookbook"
        )
        for match in _PUBLISH_CLAIM.finditer(line):
            before = line[max(0, match.start() - 60) : match.end()]
            assert _NEGATION.search(before), (
                f"{path.name}:{number} claims PyPI publication: {line.strip()}"
            )


@pytest.mark.parametrize("path", POLICY_DOCS[:2] + [ROOT / "README.md"], ids=lambda p: p.name)
def test_policy_docs_describe_no_manual_release_flow(path: Path) -> None:
    for number, line in enumerate(_text(path).splitlines(), start=1):
        if _NEGATION.search(line) or re.search(r"deleted|retired|no longer", line, re.I):
            continue  # e.g. "there are no release Makefile targets; `make release-*` was deleted"
        assert not _MANUAL_RELEASE.search(line), (
            f"{path.name}:{number} documents a manual release step"
        )


@pytest.mark.parametrize("path", _unique([ROOT / "README.md", *POLICY_DOCS]), ids=lambda p: p.name)
def test_policy_docs_state_the_cookbook_is_not_a_pypi_package(path: Path) -> None:
    lines = [line for line in _text(path).splitlines() if "pypi" in line.lower()]
    assert any(_NEGATION.search(line) for line in lines), (
        f"{path.name} never says it is not on PyPI"
    )


@pytest.mark.parametrize("path", READMES, ids=lambda p: p.name)
def test_every_readme_points_to_snapshots_and_verification(path: Path) -> None:
    text = _text(path)
    assert "docs/snapshots-and-verification.md" in text
    assert "https://github.com/yeongseon/azure-functions-cookbook-python/releases" in text
    if path.name == "README.md":
        assert "`main` is moving development content" in text


def test_docs_do_not_deny_the_tag_triggered_workflow_that_exists() -> None:
    triggered = []
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        data = yaml.load(_text(workflow), Loader=yaml.BaseLoader)
        on = data.get("on") or {}
        if isinstance(on, dict) and isinstance(on.get("push"), dict) and on["push"].get("tags"):
            triggered.append(workflow.name)
    assert "tag-verification.yml" in triggered
    for path in POLICY_DOCS:
        flattened = " ".join(_text(path).split())
        assert not re.search(r"no workflow is triggered by a tag", flattened, re.I), path.name
    assert "tag-verification.yml" in _text(ROOT / "CONTRIBUTING.md")


def test_snapshot_page_python_range_matches_pyproject() -> None:
    pyproject = tomllib.loads(_text(ROOT / "pyproject.toml"))
    requires = pyproject["project"]["requires-python"]
    assert f"`{requires}`" in _text(ROOT / "docs" / "snapshots-and-verification.md")
    release_workflow = _text(ROOT / ".github" / "workflows" / "tag-verification.yml")
    for bound in requires.split(","):
        assert f'"{bound}"' in release_workflow


def test_snapshot_page_lists_every_verification_level_without_certifying() -> None:
    text = _text(ROOT / "docs" / "snapshots-and-verification.md")
    for level in (
        "Static and generated-artifact checks",
        "Recipe unit tests and import checks",
        "Local Functions host with Azurite",
        "Real Azure deployment",
    ):
        assert level in text
    assert 'not read "CI passed" as "Azure-certified"' in text.replace("**", "")
    assert not re.search(r"\b(is|are) (Azure-certified|production-ready)\b", text)


def test_release_notes_policy_keeps_release_please_in_charge() -> None:
    text = _text(ROOT / "docs" / "snapshots-and-verification.md")
    assert "Release Please decides versions" in text
    assert "Do not edit version strings" in text
    assert "major recipe addition" in text
