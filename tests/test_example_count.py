"""Guard against example-count drift between the filesystem and prose.

The number of runnable example projects is documented in a few human-readable
places (``DESIGN.md``, the repository ``README.md``). Those hardcoded counts
have historically drifted from reality as recipes were added. This test derives
the count from the filesystem — the single source of truth — and fails CI when
any documented count diverges, so prose and reality stay in lockstep.
"""

from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"


def _actual_example_count() -> int:
    """Count example projects as ``examples/<category>/<name>/function_app.py``."""
    return len(list(EXAMPLES_DIR.glob("*/*/function_app.py")))


def test_examples_exist() -> None:
    assert _actual_example_count() > 0, "No example projects discovered under examples/."


def test_design_doc_count_matches_filesystem() -> None:
    text = (REPO_ROOT / "DESIGN.md").read_text(encoding="utf-8")
    match = re.search(r"Runnable sample projects \((\d+) total\)", text)
    assert match is not None, (
        "Could not find the 'Runnable sample projects (N total)' count in DESIGN.md."
    )
    documented = int(match.group(1))
    actual = _actual_example_count()
    assert documented == actual, (
        f"DESIGN.md documents {documented} example projects but the filesystem has {actual}. "
        f"Update the 'Runnable sample projects (N total)' count in DESIGN.md."
    )


def test_readme_count_matches_filesystem() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"\*\(this repo\)\*.*?\|\s*(\d+) examples\s*\|", text)
    assert match is not None, (
        "Could not find the '(this repo) | ... | N examples |' row in README.md."
    )
    documented = int(match.group(1))
    actual = _actual_example_count()
    assert documented == actual, (
        f"README.md documents {documented} example projects but the filesystem has {actual}. "
        f"Update the '(this repo)' row count in README.md."
    )
