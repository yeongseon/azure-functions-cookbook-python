"""Consistency guard for per-example ``recipe.yaml`` metadata.

Ensures every example ships a well-formed ``recipe.yaml`` whose fields agree with
the directory layout and the authored example README, so the metadata stays a
trustworthy single source of truth.
"""

from __future__ import annotations

import re

import pytest

from tests._isolation import EXAMPLES_DIR
from tests._recipes import RECIPES, REQUIRED_FIELDS, Recipe, load_recipes

_TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


def test_every_example_has_a_recipe() -> None:
    example_dirs = {p.parent for p in EXAMPLES_DIR.glob("*/*/function_app.py")}
    recipe_dirs = {r.directory for r in RECIPES}
    missing = {d.relative_to(EXAMPLES_DIR).as_posix() for d in example_dirs - recipe_dirs}
    assert not missing, f"examples without recipe.yaml: {sorted(missing)}"


def test_recipes_discovered() -> None:
    assert RECIPES, "No recipe.yaml files discovered"
    assert len(RECIPES) == len(load_recipes())


def test_slugs_are_unique() -> None:
    slugs = [r.slug for r in RECIPES]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    assert not dupes, f"duplicate recipe slugs: {dupes}"


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_fields_present(recipe: Recipe) -> None:
    for field in REQUIRED_FIELDS:
        assert getattr(recipe, field), f"{recipe.example_path}: empty `{field}`"


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_category_matches_directory(recipe: Recipe) -> None:
    expected = recipe.example_path.split("/")[0]
    assert recipe.category == expected, (
        f"{recipe.example_path}: category `{recipe.category}` != directory `{expected}`"
    )


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_slug_is_hyphenated(recipe: Recipe) -> None:
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", recipe.slug), (
        f"{recipe.example_path}: slug `{recipe.slug}` is not lowercase-hyphenated"
    )


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_title_matches_readme(recipe: Recipe) -> None:
    readme = recipe.directory / "README.md"
    assert readme.exists(), f"{recipe.example_path}: missing README.md"
    match = _TITLE_RE.search(readme.read_text())
    assert match, f"{recipe.example_path}: README has no `# Title` heading"
    readme_title = match.group(1).strip().replace("`", "")
    assert recipe.title == readme_title, (
        f"{recipe.example_path}: title `{recipe.title}` != README heading `{readme_title}`"
    )


_VALID_DIFFICULTY = {"Beginner", "Intermediate", "Advanced"}


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_difficulty_is_valid_or_absent(recipe: Recipe) -> None:
    assert recipe.difficulty is None or recipe.difficulty in _VALID_DIFFICULTY, (
        f"{recipe.example_path}: difficulty `{recipe.difficulty}` "
        f"must be one of {sorted(_VALID_DIFFICULTY)} or omitted"
    )
