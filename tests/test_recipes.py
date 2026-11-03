"""Consistency guard for per-example ``recipe.yaml`` metadata.

Ensures every example ships a well-formed ``recipe.yaml`` whose fields agree with
the directory layout and the authored example README, so the metadata stays a
trustworthy single source of truth.
"""

from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse

import pytest
import yaml

from azure_functions_python_cookbook.recipes import (
    DIFFICULTY_LEVELS,
    RECIPES,
    REQUIRED_FIELDS,
    VERIFICATION_LEVELS,
    Recipe,
    RecipeMetadataError,
    check_recipes,
    load_index,
)
from scripts.run_recipe_tests import recipe_projects
from tests._isolation import EXAMPLES_DIR

_TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


def test_every_example_has_a_recipe() -> None:
    example_dirs = {p.parent for p in EXAMPLES_DIR.glob("*/*/function_app.py")}
    recipe_dirs = {r.directory for r in RECIPES}
    missing = {d.relative_to(EXAMPLES_DIR).as_posix() for d in example_dirs - recipe_dirs}
    assert not missing, f"examples without recipe.yaml: {sorted(missing)}"


def test_recipes_discovered() -> None:
    assert RECIPES, "No recipe.yaml files discovered"
    assert len(RECIPES) == len(load_index())


def test_slugs_are_unique() -> None:
    slugs = [r.slug for r in RECIPES]
    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    assert not dupes, f"duplicate recipe slugs: {dupes}"


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_fields_present(recipe: Recipe) -> None:
    for field in REQUIRED_FIELDS:
        assert getattr(recipe, field), f"{recipe.example_path}: empty `{field}`"


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_verification_level_is_known(recipe: Recipe) -> None:
    assert recipe.verification in VERIFICATION_LEVELS, (
        f"{recipe.example_path}: unknown verification level `{recipe.verification}`"
    )


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


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_docs_url_maps_to_source_page(recipe: Recipe) -> None:
    if recipe.docs_url is None:
        return

    docs_path = urlparse(recipe.docs_url).path.partition("/cookbook/")[2].rstrip("/")
    page_name = "index.md" if docs_path == f"patterns/{recipe.category}" else f"{recipe.slug}.md"
    source_page = EXAMPLES_DIR.parent / "docs" / "patterns" / recipe.category / page_name
    assert source_page.is_file(), (
        f"{recipe.example_path}: docs_url `{recipe.docs_url}` has no source page `{source_page}`"
    )


_VALID_DIFFICULTY = DIFFICULTY_LEVELS


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_recipe_difficulty_is_valid_or_absent(recipe: Recipe) -> None:
    assert recipe.difficulty is None or recipe.difficulty in _VALID_DIFFICULTY, (
        f"{recipe.example_path}: difficulty `{recipe.difficulty}` "
        f"must be one of {sorted(_VALID_DIFFICULTY)} or omitted"
    )


@pytest.fixture(scope="module")
def automated_levels() -> dict[str, str]:
    """Per recipe path: `func-host` if it is in ci-test.yml's host-smoke matrix, else `unit` if
    scripts/run_recipe_tests.py runs a suite for it, else `docs`."""
    root = EXAMPLES_DIR.parent
    workflow = yaml.safe_load((root / ".github/workflows/ci-test.yml").read_text())
    matrix = workflow["jobs"]["host-smoke"]["strategy"]["matrix"]["recipe"]
    levels = dict.fromkeys((recipe.example_path for recipe in RECIPES), "docs")
    # Later entries win: a host-smoke recipe outranks one that only has a local suite.
    for level, directories in (
        ("unit", recipe_projects()),
        ("func-host", [root / entry["path"] for entry in matrix]),
    ):
        levels |= {path.relative_to(EXAMPLES_DIR).as_posix(): level for path in directories}
    return levels


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda r: r.example_path)
def test_verification_level_matches_required_automation(
    recipe: Recipe, automated_levels: dict[str, str]
) -> None:
    """Offline: `verification` is the level the required CI automation backs for the recipe.

    Precedence: `func-host` if it is in the required host-smoke matrix, else `unit` if the required
    per-recipe job runs a recipe-local suite, else `docs`. No required job reaches `azure`.
    """
    backed = automated_levels[recipe.example_path]
    assert recipe.verification == backed, (
        f"{recipe.example_path}: `verification: {recipe.verification}` but the required "
        f"automation backs `{backed}` (host-smoke matrix > per-recipe suite > docs)"
    )


def test_shipped_recipes_pass_the_metadata_check() -> None:
    assert check_recipes(RECIPES) == []


def _write_recipe(root: Path, name: str, text: str) -> None:
    directory = root / "cat" / name
    directory.mkdir(parents=True)
    (directory / "recipe.yaml").write_text(text)


def test_check_recipes_names_the_file_for_each_problem(tmp_path: Path) -> None:
    _write_recipe(tmp_path, "blank", "")
    _write_recipe(
        tmp_path,
        "bad",
        "slug: dup\ntitle: T\ncategory: cat\ndescription: d\n"
        "verification: nope\ndifficulty: Easy\n",
    )
    _write_recipe(
        tmp_path, "twin", "slug: dup\ntitle: T\ncategory: cat\ndescription: d\nverification: unit\n"
    )

    problems = check_recipes(load_index(tmp_path))

    assert "cat/blank/recipe.yaml: empty or missing `slug`" in problems
    assert any(p.startswith("cat/bad/recipe.yaml: unknown verification `nope`") for p in problems)
    assert any(p.startswith("cat/bad/recipe.yaml: difficulty `Easy`") for p in problems)
    assert "duplicate recipe slug `dup` in: cat/bad, cat/twin" in problems


@pytest.mark.parametrize(
    ("text", "message"),
    [("slug: [unclosed\n", "invalid YAML"), ("- just\n- a list\n", "expected a mapping, got list")],
)
def test_load_index_rejects_unreadable_yaml_naming_the_file(
    tmp_path: Path, text: str, message: str
) -> None:
    _write_recipe(tmp_path, "broken", text)

    with pytest.raises(RecipeMetadataError, match=message) as error:
        load_index(tmp_path)

    assert "broken" in str(error.value)
