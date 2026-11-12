"""Drift guard for repeated recipe files (#464).

Recipes stay standalone copies; ``scripts/gen_recipe_snippets.py`` keeps the standard ones equal to
one canonical file and requires every intentional difference to be listed with a reason.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gen_recipe_snippets.py"
_SPEC = importlib.util.spec_from_file_location("gen_recipe_snippets", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
gen = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = gen  # dataclasses resolve string annotations through sys.modules
_SPEC.loader.exec_module(gen)

CANONICAL = "standard\n"


def _snippets(tmp_path: Path, variants: dict[str, str] | None = None) -> tuple[Path, list[object]]:
    snippet_dir = tmp_path / "snippets"
    snippet_dir.mkdir()
    (snippet_dir / "file.txt").write_text(CANONICAL)
    return snippet_dir, [gen.Snippet("shared.txt", "file.txt", variants or {})]


def _recipe(examples: Path, name: str, content: str | None = CANONICAL) -> Path:
    project = examples / "category" / name
    project.mkdir(parents=True)
    (project / "function_app.py").write_text("")
    if content is not None:
        (project / "shared.txt").write_text(content)
    return project


@pytest.fixture
def examples(tmp_path: Path) -> Path:
    root = tmp_path / "examples"
    root.mkdir()
    return root


def test_repository_recipes_match_their_canonical_snippets() -> None:
    """Offline: every standard copy equals the canonical file; all differences are listed."""
    problems = gen.find_problems(gen.EXAMPLES)

    assert problems == [], (
        "Recipe snippets drifted; run: python scripts/gen_recipe_snippets.py\n"
        + "\n".join(map(str, problems))
    )


def test_the_managed_files_cover_the_bulk_of_the_recipes() -> None:
    """Offline: the guard is not vacuous: most recipes carry each standard file unchanged."""
    projects = gen.recipe_projects()
    for snippet in gen.SNIPPET_FILES:
        canonical = (gen.SNIPPETS / snippet.canonical).read_bytes()
        identical = [
            p
            for p in projects
            if (p / snippet.relative).is_file() and (p / snippet.relative).read_bytes() == canonical
        ]
        assert len(identical) >= 20, snippet.relative


def test_every_canonical_file_is_used_and_listed_once() -> None:
    """Offline: no orphaned canonical file and no snippet defined twice."""
    names = {path.name for path in gen.SNIPPETS.iterdir()}

    assert names == {snippet.canonical for snippet in gen.SNIPPET_FILES}
    assert len({snippet.relative for snippet in gen.SNIPPET_FILES}) == len(gen.SNIPPET_FILES)


def test_matching_copies_and_recipes_without_the_file_are_clean(
    tmp_path: Path, examples: Path
) -> None:
    snippet_dir, snippets = _snippets(tmp_path)
    _recipe(examples, "same")
    _recipe(examples, "absent", content=None)

    assert gen.find_problems(examples, snippets, snippet_dir) == []


def test_a_drifted_copy_is_reported_and_sync_restores_only_that_copy(
    tmp_path: Path, examples: Path
) -> None:
    snippet_dir, snippets = _snippets(tmp_path)
    drifted = _recipe(examples, "drifted", "edited\n")
    clean = _recipe(examples, "clean")

    problems = gen.find_problems(examples, snippets, snippet_dir)
    written = gen.sync(examples, snippets, snippet_dir)

    assert [str(p) for p in problems] == ["drift: category/drifted/shared.txt"]
    assert written == [drifted / "shared.txt"]
    assert (drifted / "shared.txt").read_text() == CANONICAL
    assert (clean / "shared.txt").read_text() == CANONICAL
    assert gen.find_problems(examples, snippets, snippet_dir) == []


def test_a_listed_variant_is_accepted_and_never_overwritten(tmp_path: Path, examples: Path) -> None:
    snippet_dir, snippets = _snippets(tmp_path, {"category/custom": "needs its own setting"})
    custom = _recipe(examples, "custom", "custom\n")

    assert gen.find_problems(examples, snippets, snippet_dir) == []
    assert gen.sync(examples, snippets, snippet_dir) == []
    assert (custom / "shared.txt").read_text() == "custom\n"


@pytest.mark.parametrize(
    ("variants", "content", "kind"),
    [
        ({"category/custom": "reason"}, CANONICAL, "variant-equals-canonical"),
        ({"category/custom": "reason"}, None, "variant-for-missing-file"),
        ({"category/gone": "reason"}, CANONICAL, "variant-for-missing-file"),
        ({"category/custom": " "}, "custom\n", "variant-without-reason"),
    ],
)
def test_stale_or_unexplained_variant_entries_fail(
    tmp_path: Path, examples: Path, variants: dict[str, str], content: str | None, kind: str
) -> None:
    """A variant entry must point at a real, different copy and carry a reason."""
    snippet_dir, snippets = _snippets(tmp_path, variants)
    _recipe(examples, "custom", content)

    kinds = [problem.kind for problem in gen.find_problems(examples, snippets, snippet_dir)]

    assert kind in kinds
    assert gen.sync(examples, snippets, snippet_dir) == []


def test_check_mode_fails_on_drift_without_writing_and_default_mode_fixes_it(
    tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    snippet_dir, snippets = _snippets(tmp_path)
    drifted = _recipe(examples, "drifted", "edited\n")

    assert gen.main(["--check"], examples, snippets, snippet_dir) == 1
    assert "drift: category/drifted/shared.txt" in capsys.readouterr().err
    assert (drifted / "shared.txt").read_text() == "edited\n"

    assert gen.main([], examples, snippets, snippet_dir) == 0
    assert (drifted / "shared.txt").read_text() == CANONICAL
    assert gen.main(["--check"], examples, snippets, snippet_dir) == 0


def test_default_mode_still_fails_on_a_bad_variant_entry(
    tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    snippet_dir, snippets = _snippets(tmp_path, {"category/gone": "reason"})
    _recipe(examples, "other")

    assert gen.main([], examples, snippets, snippet_dir) == 1
    assert "variant-for-missing-file: category/gone/shared.txt" in capsys.readouterr().err
