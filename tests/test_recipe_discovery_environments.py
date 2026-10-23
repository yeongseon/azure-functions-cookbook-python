from pathlib import Path
from unittest.mock import patch

from scripts import gen_requirements
from tools.recipe_discovery import recipe_files
from tools.recipe_security import inventory


def test_generated_recipe_environments_and_caches_are_not_sources(tmp_path: Path) -> None:
    recipe = tmp_path / "examples/demo/app"
    recipe.mkdir(parents=True)
    (recipe / "function_app.py").write_text("VALUE = 1\n")
    for folder in (".venv/lib/site-packages/sdk", "__pycache__", "site-packages/sdk", "venv/sdk"):
        generated = recipe / folder
        generated.mkdir(parents=True)
        (generated / "function_app.py").write_text("invalid python !\n")
        (generated / "pyproject.toml").write_text("invalid toml !\n")
    assert recipe_files(tmp_path / "examples", "function_app.py") == (recipe / "function_app.py",)
    with patch.object(gen_requirements, "EXAMPLES", tmp_path / "examples"):
        assert gen_requirements.recipe_projects() == (recipe,)
    assert list(inventory(tmp_path)) == ["examples/demo/app"]
