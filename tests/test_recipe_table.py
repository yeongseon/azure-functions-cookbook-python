"""Drift guard: README recipe tables must match ``scripts/gen_recipe_table.py``."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "gen_recipe_table.py"
_spec = importlib.util.spec_from_file_location("gen_recipe_table", _SCRIPT)
assert _spec and _spec.loader
gen_recipe_table = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_recipe_table)


def test_readme_recipe_tables_are_up_to_date() -> None:
    current = gen_recipe_table.README.read_text()
    expected = gen_recipe_table._splice(current, gen_recipe_table.render())
    assert current == expected, (
        "README recipe tables are stale. Run: python scripts/gen_recipe_table.py"
    )


def test_all_recipes_appear_in_generated_tables() -> None:
    section = gen_recipe_table.render()
    for recipe in gen_recipe_table.RECIPES:
        link = f"examples/{recipe.example_path}/"
        assert link in section, f"{recipe.example_path} missing from generated recipe tables"


# READMEs whose Ecosystem table hardcodes the total example count in the
# "this repo" row. The count drifts silently as recipes are added/removed
# unless enforced against the actual inventory (len(RECIPES)).
_README_FILES = ["README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md"]
_ECOSYSTEM_ROW_TOKEN = "**azure-functions-cookbook-python**"


@pytest.mark.parametrize("readme_name", _README_FILES)
def test_ecosystem_example_count_matches_inventory(readme_name: str) -> None:
    """The Ecosystem-table 'this repo' total must match the recipe inventory."""
    expected = len(gen_recipe_table.RECIPES)
    readme_path = _ROOT / readme_name
    row = next(
        (
            line
            for line in readme_path.read_text(encoding="utf-8").splitlines()
            if _ECOSYSTEM_ROW_TOKEN in line
        ),
        None,
    )
    assert row is not None, f"{readme_name}: Ecosystem row '{_ECOSYSTEM_ROW_TOKEN}' not found"
    last_cell = row.strip().strip("|").split("|")[-1]
    match = re.search(r"[\d,]+", last_cell)
    assert match, f"{readme_name}: no example count found in Ecosystem row:\n{row}"
    actual = int(match.group().replace(",", ""))
    assert actual == expected, (
        f"{readme_name}: Ecosystem example count is {actual} but the repository has "
        f"{expected} recipes. Update the '{_ECOSYSTEM_ROW_TOKEN}' row to '{expected}'."
    )


# Regression for #353: docs/index.md hardcodes the total pattern/example
# count and a per-library dogfood-coverage breakdown. Both silently drifted
# from the actual recipes.json/examples inventory. Enforce them against the
# live counts instead of letting docs/index.md diverge again.
_DOGFOOD_LIBRARIES = (
    "azure-functions-logging",
    "azure-functions-openapi",
    "azure-functions-validation",
    "azure-functions-db",
)


def _count_examples_using(library: str) -> int:
    count = 0
    for recipe in gen_recipe_table.RECIPES:
        pyproject = _ROOT / "examples" / recipe.example_path / "pyproject.toml"
        if pyproject.is_file() and library in pyproject.read_text(encoding="utf-8"):
            count += 1
    return count


def test_docs_index_pattern_and_example_counts_match_inventory() -> None:
    expected = len(gen_recipe_table.RECIPES)
    index_text = (_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    pattern_match = re.search(r"\*\*(\d+) patterns\*\*", index_text)
    examples_match = re.search(r"\*\*(\d+) runnable example projects\*\*", index_text)
    assert pattern_match, "docs/index.md: '**N patterns**' line not found"
    assert examples_match, "docs/index.md: '**N runnable example projects**' line not found"
    assert int(pattern_match.group(1)) == expected, (
        f"docs/index.md pattern count is {pattern_match.group(1)} but the repository has "
        f"{expected} recipes."
    )
    assert int(examples_match.group(1)) == expected, (
        f"docs/index.md example count is {examples_match.group(1)} but the repository has "
        f"{expected} recipes."
    )


def test_docs_index_dogfood_coverage_matches_inventory() -> None:
    index_text = (_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    coverage_line = next(
        (line for line in index_text.splitlines() if line.startswith("- Dogfood coverage:")),
        None,
    )
    assert coverage_line is not None, "docs/index.md: 'Dogfood coverage:' line not found"

    for library in _DOGFOOD_LIBRARIES:
        expected = _count_examples_using(library)
        match = re.search(rf"(\d+) (?:examples? )?use `{re.escape(library)}`", coverage_line)
        assert match, f"docs/index.md: no count found for `{library}` in dogfood coverage line"
        actual = int(match.group(1))
        assert actual == expected, (
            f"docs/index.md: dogfood coverage count for `{library}` is {actual} but "
            f"{expected} examples actually declare it as a dependency."
        )
