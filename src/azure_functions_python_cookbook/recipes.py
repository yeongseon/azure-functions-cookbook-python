"""Machine-readable recipe index and lookup helper.

Each ``examples/<category>/<name>/recipe.yaml`` is the single source of truth for
a recipe's identity. This module discovers and parses them into a
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
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = _REPO_ROOT / "examples"

REQUIRED_FIELDS = ("slug", "title", "category", "description", "verification")
VERIFICATION_LEVELS = frozenset({"docs", "unit", "func-host", "azure"})
DIFFICULTY_LEVELS = frozenset({"Beginner", "Intermediate", "Advanced"})


class RecipeMetadataError(ValueError):
    """A ``recipe.yaml`` could not be read as a mapping; the message names the file."""


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
    verification: str = ""

    @property
    def directory(self) -> Path:
        """Return the example directory this recipe describes."""
        return EXAMPLES_DIR / self.example_path

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


def _read_mapping(path: Path) -> dict[str, Any]:
    """Parse ``path`` as a YAML mapping (an empty file is an empty mapping)."""
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as error:
        raise RecipeMetadataError(f"{path}: invalid YAML: {error}") from error
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RecipeMetadataError(f"{path}: expected a mapping, got {type(data).__name__}")
    return data


def check_recipes(recipes: list[Recipe]) -> list[str]:
    """Return one actionable message per metadata problem (empty list when valid)."""
    problems: list[str] = []
    for recipe in recipes:
        where = f"{recipe.example_path}/recipe.yaml"
        problems.extend(
            f"{where}: empty or missing `{field}`"
            for field in REQUIRED_FIELDS
            if not getattr(recipe, field)
        )
        if recipe.verification and recipe.verification not in VERIFICATION_LEVELS:
            problems.append(
                f"{where}: unknown verification `{recipe.verification}` "
                f"(expected one of {sorted(VERIFICATION_LEVELS)})"
            )
        if recipe.difficulty is not None and recipe.difficulty not in DIFFICULTY_LEVELS:
            problems.append(
                f"{where}: difficulty `{recipe.difficulty}` "
                f"must be one of {sorted(DIFFICULTY_LEVELS)} or omitted"
            )
    slugs = [recipe.slug for recipe in recipes if recipe.slug]
    problems.extend(
        f"duplicate recipe slug `{slug}` in: "
        + ", ".join(r.example_path for r in recipes if r.slug == slug)
        for slug in sorted({slug for slug in slugs if slugs.count(slug) > 1})
    )
    return problems


def load_index(examples_dir: Path = EXAMPLES_DIR) -> list[Recipe]:
    """Discover and parse every ``recipe.yaml`` under ``examples_dir``."""
    recipes: list[Recipe] = []
    for path in sorted(examples_dir.glob("*/*/recipe.yaml")):
        data = _read_mapping(path)
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
                verification=str(data.get("verification", "")),
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

    ``query`` is split on whitespace; a recipe matches when **all** terms are
    present (case-insensitively, order-independent) in the slug, title, category,
    description, and tags. ``tag`` filters to recipes carrying that exact tag.
    Passing neither returns the full index. Results preserve index order.
    """
    items = RECIPES if recipes is None else recipes
    terms = query.lower().split()
    wanted_tag = tag.strip().lower() if tag else None
    matches: list[Recipe] = []
    for recipe in items:
        if wanted_tag is not None and wanted_tag not in recipe.tags:
            continue
        if terms:
            haystack = recipe.search_text()
            if not all(term in haystack for term in terms):
                continue
        matches.append(recipe)
    return matches
