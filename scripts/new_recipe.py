"""Scaffold a new flat cookbook recipe.

Usage:
    python scripts/new_recipe.py --category apis-and-ingress --name my_recipe

Creates ``examples/<category>/<name>/`` pre-populated with the standard flat
recipe file set (function_app.py, README.md, recipe.yaml, host.json,
local.settings.json.example, pyproject.toml) so a new example passes the
auto-discovery smoke and recipe-metadata guards out of the box.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLES_DIR = REPO_ROOT / "examples"
DOCS_BASE = "https://yeongseon.github.io/azure-functions-cookbook-python/patterns"


def _title_from_name(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split("_"))


def _function_app_py(title: str) -> str:
    return f'''from __future__ import annotations

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging
from azure_functions_openapi import openapi

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="ping")
@openapi(summary="{title} ping", description="Health probe for the {title} recipe.")
def ping(req: func.HttpRequest) -> func.HttpResponse:
    """Return a simple OK response."""
    logger.info("{title} ping received")
    return func.HttpResponse("ok", status_code=200)
'''


def _readme_md(title: str, category: str, slug: str, description: str) -> str:
    docs_url = f"{DOCS_BASE}/{category}/{slug}/"
    return f"""# {title}

📖 [Full documentation]({docs_url})

{description}

## Run

```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoints

- `GET /api/ping` — health probe
"""


def _recipe_yaml(slug: str, title: str, category: str, description: str) -> str:
    docs_url = f"{DOCS_BASE}/{category}/{slug}/"
    return (
        f"slug: {slug}\n"
        f"title: {title}\n"
        f"category: {category}\n"
        f"description: {description}\n"
        f"docs_url: {docs_url}\n"
    )


_HOST_JSON = {
    "version": "2.0",
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)",
    },
}

_LOCAL_SETTINGS = {
    "IsEncrypted": False,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
    },
}


def _pyproject_toml(name: str, title: str) -> str:
    return f"""[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{title} example for Azure Functions."
requires-python = ">=3.10"
dependencies = [
  "azure-functions>=1.21.3",
  "azure-functions-logging>=0.5.0",
  "azure-functions-openapi>=0.10.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.5",
  "ruff>=0.11.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
"""


def create_recipe(
    category: str,
    name: str,
    *,
    description: str | None = None,
    examples_dir: Path = DEFAULT_EXAMPLES_DIR,
) -> Path:
    """Create a new flat recipe directory and return its path.

    Raises ``ValueError`` if the category does not exist, the name is not a
    valid snake_case identifier, or the target already exists.
    """
    if not name.replace("_", "").isalnum() or not name.islower() or name[0].isdigit():
        raise ValueError(f"name must be lowercase snake_case: {name!r}")

    category_dir = examples_dir / category
    if not category_dir.is_dir():
        available = sorted(
            p.name for p in examples_dir.iterdir() if p.is_dir() and not p.name.startswith("_")
        )
        raise ValueError(f"unknown category {category!r}; choose one of: {', '.join(available)}")

    target = category_dir / name
    if target.exists():
        raise ValueError(f"recipe already exists: {target}")

    slug = name.replace("_", "-")
    title = _title_from_name(name)
    desc = description or f"{title} recipe for Azure Functions Python v2."

    target.mkdir(parents=True)
    (target / "function_app.py").write_text(_function_app_py(title))
    (target / "README.md").write_text(_readme_md(title, category, slug, desc))
    (target / "recipe.yaml").write_text(_recipe_yaml(slug, title, category, desc))
    (target / "host.json").write_text(json.dumps(_HOST_JSON, indent=2) + "\n")
    (target / "local.settings.json.example").write_text(
        json.dumps(_LOCAL_SETTINGS, indent=2) + "\n"
    )
    (target / "pyproject.toml").write_text(_pyproject_toml(name, title))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new flat cookbook recipe.")
    parser.add_argument("--category", required=True, help="Existing examples/ category directory")
    parser.add_argument("--name", required=True, help="Recipe directory name (snake_case)")
    parser.add_argument("--description", default=None, help="One-line recipe description")
    args = parser.parse_args(argv)

    try:
        target = create_recipe(args.category, args.name, description=args.description)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rel = target.relative_to(REPO_ROOT)
    print(f"Created recipe: {rel}")
    print("Next steps:")
    print(f"  1. Implement the trigger logic in {rel}/function_app.py")
    print(f"  2. Refine the description in {rel}/README.md and {rel}/recipe.yaml")
    print("  3. Run: hatch run pytest tests/test_recipes.py tests/test_example_discovery.py -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
