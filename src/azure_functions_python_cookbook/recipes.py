"""Machine-readable recipe index and lookup helper.

Each ``examples/<category>/<name>/recipe.yaml`` is the single source of truth for
a recipe's identity. This module discovers and parses them into a validated,
machine-readable index and exposes :func:`find_recipe` so a recipe can be
looked up by keyword or tag instead of manually browsing the ``examples/`` tree.

The canonical on-disk artifact is ``recipes.json`` at the repository root,
regenerated with ``python scripts/gen_recipe_index.py`` and drift-guarded by the
test suite.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = _REPO_ROOT / "examples"


@dataclass(frozen=True)
class Recipe:
    """Parsed ``recipe.yaml`` metadata for a single example."""

    slug: str
    title: str
    category: str
    description: str
    example_path: str
    docs_url: str | None
    difficulty: str | None
    tags: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of this recipe."""
        return {
            "slug": self.slug,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "example_path": self.example_path,
            "docs_url": self.docs_url,
            "difficulty": self.difficulty,
            "tags": list(self.tags),
        }

    def search_text(self) -> str:
        """Return the lowercased text searched by :func:`find_recipe`."""
        return " ".join(
            (self.slug, self.title, self.category, self.description, *self.tags)
        ).lower()


def _derive_tags(raw_tags: object, category: str, slug: str) -> tuple[str, ...]:
    """Build a normalized tag set from explicit tags plus category/slug tokens."""
    explicit = raw_tags if isinstance(raw_tags, list) else []
    tags = {str(tag).strip().lower() for tag in explicit if str(tag).strip()}
    if category:
        tags.add(category.lower())
    for token in slug.replace("_", "-").split("-"):
        if token:
            tags.add(token.lower())
    return tuple(sorted(tags))


def load_index(examples_dir: Path = EXAMPLES_DIR) -> list[Recipe]:
    """Discover and parse every ``recipe.yaml`` under ``examples_dir``."""
    recipes: list[Recipe] = []
    for path in sorted(examples_dir.glob("*/*/recipe.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        example_path = path.parent.relative_to(examples_dir).as_posix()
        category = str(data.get("category", ""))
        slug = str(data.get("slug", ""))
        recipes.append(
            Recipe(
                slug=slug,
                title=str(data.get("title", "")),
                category=category,
                description=str(data.get("description", "")),
                example_path=example_path,
                docs_url=data.get("docs_url"),
                difficulty=data.get("difficulty"),
                tags=_derive_tags(data.get("tags"), category, slug),
            )
        )
    return recipes


RECIPES: list[Recipe] = load_index()


def index_as_dicts(recipes: list[Recipe] | None = None) -> list[dict[str, object]]:
    """Return the recipe index as a list of JSON-serializable dicts."""
    items = RECIPES if recipes is None else recipes
    return [recipe.as_dict() for recipe in items]


def index_as_json(recipes: list[Recipe] | None = None) -> str:
    """Return the recipe index serialized as pretty-printed JSON (trailing newline)."""
    return json.dumps(index_as_dicts(recipes), indent=2, ensure_ascii=False) + "\n"


def find_recipe(
    query: str = "",
    *,
    tag: str | None = None,
    recipes: list[Recipe] | None = None,
) -> list[Recipe]:
    """Look up recipes by free-text ``query`` and/or exact ``tag``.

    ``query`` matches (case-insensitively) against the slug, title, category,
    description, and tags. ``tag`` filters to recipes carrying that exact tag.
    Passing neither returns the full index. Results preserve index order.
    """
    items = RECIPES if recipes is None else recipes
    needle = query.strip().lower()
    wanted_tag = tag.strip().lower() if tag else None
    matches: list[Recipe] = []
    for recipe in items:
        if wanted_tag is not None and wanted_tag not in recipe.tags:
            continue
        if needle and needle not in recipe.search_text():
            continue
        matches.append(recipe)
    return matches
