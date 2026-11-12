"""Keep the translated READMEs honest snapshots of the canonical English README.

Policy: CONTRIBUTING.md, "Documentation and Translations". Translations may lag, but each
must say which English release it was aligned with and point back to the English README.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ["README.ko.md", "README.ja.md", "README.zh-CN.md"]
_SNAPSHOT = re.compile(r"<!-- translation-snapshot: v(\d+)\.(\d+)\.(\d+) (\d{4}-\d{2}-\d{2}) -->")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


@pytest.mark.parametrize("name", TRANSLATIONS)
def test_translation_declares_snapshot_and_links_to_english(name: str) -> None:
    text = (ROOT / name).read_text(encoding="utf-8")
    match = _SNAPSHOT.search(text)
    assert match, f"{name}: missing '<!-- translation-snapshot: vX.Y.Z YYYY-MM-DD -->' comment"
    assert "(README.md)" in text, f"{name}: must link back to the canonical English README.md"
    assert "releases/tag/v" + ".".join(match.groups()[:3]) in text, (
        f"{name}: visible banner must link the snapshot release named in the comment"
    )


@pytest.mark.parametrize("name", TRANSLATIONS)
def test_snapshot_version_is_not_ahead_of_the_manifest(name: str) -> None:
    manifest = (ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
    current = _version(re.search(r'"\.":\s*"(\d+\.\d+\.\d+)"', manifest).group(1))  # type: ignore[union-attr]
    match = _SNAPSHOT.search((ROOT / name).read_text(encoding="utf-8"))
    assert match
    assert tuple(int(g) for g in match.groups()[:3]) <= current


def test_english_readme_states_it_is_canonical() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "English README is canonical" in text
    assert "CONTRIBUTING.md#documentation-and-translations" in text
