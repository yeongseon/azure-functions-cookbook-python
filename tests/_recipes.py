"""Loader for per-example ``recipe.yaml`` metadata.

Each ``examples/<category>/<name>/recipe.yaml`` is the single source of truth for
a recipe's identity (slug, title, category, description). This module discovers
and parses them so tests (and future doc generators) can consume a validated
list instead of re-deriving metadata from README prose.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from tests._isolation import EXAMPLES_DIR

REQUIRED_FIELDS = ("slug", "title", "category", "description")


@dataclass(frozen=True)
class Recipe:
    """Parsed ``recipe.yaml`` for a single example."""

    slug: str
    title: str
    category: str
    description: str
    docs_url: str | None
    example_path: (
        str  # forward-slash path relative to examples/, e.g. "apis-and-ingress/hello_http_minimal"
    )

    @property
    def directory(self) -> Path:
        return EXAMPLES_DIR / self.example_path


def load_recipes() -> list[Recipe]:
    """Return every recipe, sorted by example path."""
    recipes: list[Recipe] = []
    for path in sorted(EXAMPLES_DIR.glob("*/*/recipe.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        example_path = path.parent.relative_to(EXAMPLES_DIR).as_posix()
        recipes.append(
            Recipe(
                slug=data.get("slug", ""),
                title=data.get("title", ""),
                category=data.get("category", ""),
                description=data.get("description", ""),
                docs_url=data.get("docs_url"),
                example_path=example_path,
            )
        )
    return recipes


RECIPES = load_recipes()
