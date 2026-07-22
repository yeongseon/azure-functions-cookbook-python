"""Drift guard: README recipe tables must match ``scripts/gen_recipe_table.py``."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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
