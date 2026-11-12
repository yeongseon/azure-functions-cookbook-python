"""Guard the README 'Choose Another Option When...' section (#470).

The section links to official alternatives and to recipes; those links must resolve, and every
translated README must carry the same links so the translation cannot point at stale targets.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
READMES = ["README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md"]
_HEADING = "## Choose Another Option When..."
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _section(name: str) -> str:
    text = (ROOT / name).read_text(encoding="utf-8")
    start = text.index(_HEADING)
    return text[start : text.index("\n## ", start + 1)]


def _targets(name: str) -> list[str]:
    return _LINK.findall(_section(name))


def test_section_stays_short() -> None:
    assert len(_section("README.md").splitlines()) <= 20


def test_local_links_resolve() -> None:
    for target in _targets("README.md"):
        if not target.startswith("https://"):
            assert (ROOT / target.split("#")[0]).exists(), target


def test_official_links_use_https_documentation_hosts() -> None:
    hosts = ("https://learn.microsoft.com/", "https://docs.langchain.com/")
    for target in _targets("README.md"):
        if "://" in target:
            assert target.startswith(hosts), target


@pytest.mark.parametrize("name", READMES[1:])
def test_translations_link_to_the_same_targets(name: str) -> None:
    assert _targets(name) == _targets("README.md")
