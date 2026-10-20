"""Regression guard for #353: the docs-site changelog surface must not
disagree with the canonical Release Please version/history.

docs/changelog.md embeds the root CHANGELOG.md live via a mkdocs snippet
(`--8<-- "CHANGELOG.md"`), so it cannot silently diverge from it. This test
guards the other half of the chain: the root CHANGELOG.md's newest entry
must match the version Release Please currently owns in
.release-please-manifest.json, so the embedded page always reflects the
latest tagged release.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

_ROOT = Path(__file__).resolve().parents[1]


def test_docs_changelog_embeds_the_canonical_root_changelog() -> None:
    changelog_page = (_ROOT / "docs" / "changelog.md").read_text(encoding="utf-8")

    assert '--8<-- "CHANGELOG.md"' in changelog_page, (
        "docs/changelog.md must embed the root CHANGELOG.md via a mkdocs snippet "
        "instead of maintaining an independent copy."
    )


def test_root_changelog_newest_entry_matches_the_release_please_manifest() -> None:
    manifest = json.loads((_ROOT / ".release-please-manifest.json").read_text())
    manifest_version = manifest["."]

    changelog_text = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    newest_entry = re.search(r"^## \[?(\d+\.\d+\.\d+)\]?", changelog_text, re.MULTILINE)

    assert newest_entry, "CHANGELOG.md: no '## [X.Y.Z]' version heading found"
    assert newest_entry.group(1) == manifest_version, (
        f"CHANGELOG.md's newest entry is {newest_entry.group(1)} but "
        f".release-please-manifest.json says {manifest_version}."
    )
