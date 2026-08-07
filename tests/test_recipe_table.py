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
            for line in readme_path.read_text().splitlines()
            if _ECOSYSTEM_ROW_TOKEN in line
        ),
        None,
    )
    assert row is not None, (
        f"{readme_name}: Ecosystem row '{_ECOSYSTEM_ROW_TOKEN}' not found"
    )
    numbers = re.findall(r"\d+", row)
    assert numbers, f"{readme_name}: no example count found in Ecosystem row:\n{row}"
    actual = int(numbers[-1])
    assert actual == expected, (
        f"{readme_name}: Ecosystem example count is {actual} but the repository has "
        f"{expected} recipes. Update the '{_ECOSYSTEM_ROW_TOKEN}' row to '{expected}'."
    )
