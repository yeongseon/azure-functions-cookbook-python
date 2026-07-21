"""Tests for the ``scripts/new_recipe.py`` recipe scaffolder."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "new_recipe.py"
_spec = importlib.util.spec_from_file_location("new_recipe", _SCRIPT)
assert _spec and _spec.loader
new_recipe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(new_recipe)


@pytest.fixture
def examples_dir(tmp_path: Path) -> Path:
    root = tmp_path / "examples"
    (root / "apis-and-ingress").mkdir(parents=True)
    return root


def test_create_recipe_writes_full_flat_file_set(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", examples_dir=examples_dir
    )
    expected = {
        "function_app.py",
        "README.md",
        "recipe.yaml",
        "host.json",
        "local.settings.json.example",
        "pyproject.toml",
    }
    assert {p.name for p in target.iterdir()} == expected


def test_generated_recipe_yaml_is_consistent(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", examples_dir=examples_dir
    )
    data = yaml.safe_load((target / "recipe.yaml").read_text())
    assert data["slug"] == "my-new-recipe"
    assert data["title"] == "My New Recipe"
    assert data["category"] == "apis-and-ingress"
    assert data["description"]
    # recipe.yaml title must match the README `# heading` (mirrors test_recipes guard)
    first_line = (target / "README.md").read_text().splitlines()[0]
    assert first_line == f"# {data['title']}"


def test_generated_function_app_compiles_and_defines_app(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", examples_dir=examples_dir
    )
    source = (target / "function_app.py").read_text()
    compile(source, str(target / "function_app.py"), "exec")
    assert "app = func.FunctionApp" in source


def test_rejects_unknown_category(examples_dir: Path) -> None:
    with pytest.raises(ValueError, match="unknown category"):
        new_recipe.create_recipe("nope", "my_recipe", examples_dir=examples_dir)


def test_rejects_non_snake_case_name(examples_dir: Path) -> None:
    with pytest.raises(ValueError, match="snake_case"):
        new_recipe.create_recipe("apis-and-ingress", "MyRecipe", examples_dir=examples_dir)


def test_rejects_existing_recipe(examples_dir: Path) -> None:
    new_recipe.create_recipe("apis-and-ingress", "dup_recipe", examples_dir=examples_dir)
    with pytest.raises(ValueError, match="already exists"):
        new_recipe.create_recipe("apis-and-ingress", "dup_recipe", examples_dir=examples_dir)
