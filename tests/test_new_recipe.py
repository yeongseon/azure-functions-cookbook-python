"""Tests for the ``scripts/new_recipe.py`` recipe scaffolder."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tomllib

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
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    expected = {
        "function_app.py",
        "README.md",
        "recipe.yaml",
        "host.json",
        "local.settings.json.example",
        "pyproject.toml",
        "requirements.txt",
    }
    assert {p.name for p in target.iterdir()} == expected


def test_generated_recipe_yaml_is_consistent(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    data = yaml.safe_load((target / "recipe.yaml").read_text())
    assert data["slug"] == "my-new-recipe"
    assert data["title"] == "My New Recipe"
    assert data["category"] == "apis-and-ingress"
    assert data["verification"] == "docs"
    assert data["description"]
    assert data["difficulty"] == "Beginner"
    assert data.get("docs_url") is None
    # recipe.yaml title must match the README `# heading` (mirrors test_recipes guard)
    first_line = (target / "README.md").read_text().splitlines()[0]
    assert first_line == f"# {data['title']}"


def test_generated_function_app_compiles_and_defines_app(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    source = (target / "function_app.py").read_text()
    compile(source, str(target / "function_app.py"), "exec")
    assert "app = func.FunctionApp" in source


def test_generated_recipe_targets_python_311_and_current_family_floors(
    examples_dir: Path,
) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )

    project = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["requires-python"] == ">=3.11"
    assert project["tool"]["ruff"]["target-version"] == "py311"
    assert project["project"]["dependencies"] == [
        "azure-functions>=1.21.3",
        "azure-functions-logging>=0.15.0",
        "azure-functions-openapi>=0.30.0",
    ]
    assert (target / "requirements.txt").read_text() == (
        "azure-functions-logging>=0.15.0\n"
        "azure-functions-openapi>=0.30.0\n"
        "azure-functions>=1.21.3\n"
    )


def test_rejects_unknown_category(examples_dir: Path) -> None:
    with pytest.raises(ValueError, match="unknown category"):
        new_recipe.create_recipe(
            "nope", "my_recipe", difficulty="Beginner", examples_dir=examples_dir
        )


def test_rejects_non_snake_case_name(examples_dir: Path) -> None:
    with pytest.raises(ValueError, match="snake_case"):
        new_recipe.create_recipe(
            "apis-and-ingress", "MyRecipe", difficulty="Beginner", examples_dir=examples_dir
        )


def test_rejects_existing_recipe(examples_dir: Path) -> None:
    new_recipe.create_recipe(
        "apis-and-ingress", "dup_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    with pytest.raises(ValueError, match="already exists"):
        new_recipe.create_recipe(
            "apis-and-ingress", "dup_recipe", difficulty="Beginner", examples_dir=examples_dir
        )


def test_generated_pyproject_declares_wheel_file_selection(examples_dir: Path) -> None:
    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )

    project = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["tool"]["hatch"]["build"]["targets"]["wheel"]["include"] == ["function_app.py"]


def test_generated_recipe_builds_a_real_wheel(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Regression for #367: without explicit wheel file selection, Hatchling
    # cannot determine which files to ship for a flat function_app.py
    # module and raises ValueError at build time -- a TOML-string
    # inspection test cannot catch this; only an actual build does.
    from hatchling.build import build_wheel

    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    output_dir = target / "dist"
    output_dir.mkdir()

    monkeypatch.chdir(target)
    wheel_filename = build_wheel(str(output_dir))

    assert (output_dir / wheel_filename).is_file()

    import zipfile

    with zipfile.ZipFile(output_dir / wheel_filename) as wheel:
        assert "function_app.py" in wheel.namelist()


def test_generated_recipe_builds_a_real_editable_wheel(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hatchling.build import build_editable

    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    output_dir = target / "dist"
    output_dir.mkdir()

    monkeypatch.chdir(target)
    wheel_filename = build_editable(str(output_dir))

    assert (output_dir / wheel_filename).is_file()


def test_rejects_invalid_difficulty(examples_dir: Path) -> None:
    with pytest.raises(ValueError, match="difficulty must be one of"):
        new_recipe.create_recipe(
            "apis-and-ingress", "my_recipe", difficulty="Expert", examples_dir=examples_dir
        )


def test_description_with_colon_round_trips_through_yaml(examples_dir: Path) -> None:
    # Regression for #368: a normal one-line description containing ": "
    # (e.g. "HTTP API: paginated results") corrupted the manually
    # string-interpolated recipe.yaml, and yaml.safe_load raised
    # ScannerError before any metadata guard could even run.
    target = new_recipe.create_recipe(
        "apis-and-ingress",
        "paged_api",
        description="HTTP API: paginated results",
        difficulty="Beginner",
        examples_dir=examples_dir,
    )

    data = yaml.safe_load((target / "recipe.yaml").read_text())

    assert data["description"] == "HTTP API: paginated results"


def test_generated_recipe_passes_the_readme_table_guard(examples_dir: Path) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tests._recipes import Recipe

    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    data = yaml.safe_load((target / "recipe.yaml").read_text())
    recipe = Recipe(
        slug=data["slug"],
        title=data["title"],
        category=data["category"],
        description=data["description"],
        docs_url=data.get("docs_url"),
        difficulty=data.get("difficulty"),
        verification=data["verification"],
        example_path=f"apis-and-ingress/{target.name}",
    )

    table_script = Path(__file__).resolve().parents[1] / "scripts" / "gen_recipe_table.py"
    spec = importlib.util.spec_from_file_location("gen_recipe_table", table_script)
    assert spec and spec.loader
    gen_recipe_table = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen_recipe_table)

    rendered = gen_recipe_table.render([recipe])

    assert recipe.title in rendered
    assert "Beginner" in rendered


def test_generated_recipe_passes_the_docs_url_guard(examples_dir: Path) -> None:
    import sys
    from unittest.mock import patch

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tests import test_recipes as guards
    from tests._recipes import Recipe

    target = new_recipe.create_recipe(
        "apis-and-ingress", "my_new_recipe", difficulty="Beginner", examples_dir=examples_dir
    )
    data = yaml.safe_load((target / "recipe.yaml").read_text())
    recipe = Recipe(
        slug=data["slug"],
        title=data["title"],
        category=data["category"],
        description=data["description"],
        docs_url=data.get("docs_url"),
        difficulty=data.get("difficulty"),
        verification=data["verification"],
        example_path=f"apis-and-ingress/{target.name}",
    )

    with patch.object(guards, "EXAMPLES_DIR", examples_dir):
        # No docs_url was generated, so this guard must pass trivially
        # instead of requiring a docs page that was never created.
        guards.test_recipe_docs_url_maps_to_source_page(recipe)
