"""Generate the machine-readable ``recipes.json`` index from ``recipe.yaml`` files.

``recipe.yaml`` is the single source of truth for recipe metadata. This script
serializes the parsed index (see
``src/azure_functions_python_cookbook/recipes.py``) to ``recipes.json`` at the
repository root.

Usage::

    python scripts/gen_recipe_index.py            # rewrite recipes.json in place
    python scripts/gen_recipe_index.py --check     # exit 1 if recipes.json is stale
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from azure_functions_python_cookbook.recipes import index_as_json  # noqa: E402

INDEX_PATH = REPO_ROOT / "recipes.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate recipes.json from recipe.yaml files.")
    parser.add_argument("--check", action="store_true", help="Fail if recipes.json is out of date")
    args = parser.parse_args(argv)

    generated = index_as_json()
    current = INDEX_PATH.read_text() if INDEX_PATH.exists() else ""

    if args.check:
        if current != generated:
            print(
                "recipes.json is stale. Run: python scripts/gen_recipe_index.py",
                file=sys.stderr,
            )
            return 1
        print("recipes.json is up to date.")
        return 0

    if current != generated:
        INDEX_PATH.write_text(generated)
        print("Updated recipes.json.")
    else:
        print("recipes.json already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
