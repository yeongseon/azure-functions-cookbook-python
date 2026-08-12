"""Tests for the machine-readable recipe index and ``find_recipe`` helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from azure_functions_python_cookbook.recipes import (
    RECIPES,
    Recipe,
    _derive_tags,
    find_recipe,
    index_as_dicts,
    index_as_json,
    load_index,
)

_ROOT = Path(__file__).resolve().parents[1]


def _make_recipe(
    slug: str = "hello",
    title: str = "Hello",
    category: str = "apis-and-ingress",
    description: str = "A greeting",
    example_path: str = "apis-and-ingress/hello",
    tags: tuple[str, ...] = ("apis-and-ingress", "hello"),
) -> Recipe:
    return Recipe(
        slug=slug,
        title=title,
        category=category,
        description=description,
        example_path=example_path,
        docs_url=None,
        difficulty=None,
        tags=tags,
    )


def test_index_is_non_empty_and_typed() -> None:
    assert RECIPES
    assert all(isinstance(recipe, Recipe) for recipe in RECIPES)


def test_recipe_as_dict_round_trips_fields() -> None:
    recipe = _make_recipe()
    assert recipe.as_dict() == {
        "slug": "hello",
        "title": "Hello",
        "category": "apis-and-ingress",
        "description": "A greeting",
        "example_path": "apis-and-ingress/hello",
        "docs_url": None,
        "difficulty": None,
        "tags": ["apis-and-ingress", "hello"],
    }


def test_search_text_is_lowercased_and_includes_tags() -> None:
    text = _make_recipe(title="MixedCase", tags=("alpha", "beta")).search_text()
    assert text == text.lower()
    assert "alpha" in text
    assert "mixedcase" in text


def test_derive_tags_merges_explicit_category_and_slug_tokens() -> None:
    tags = _derive_tags(["Custom", "  ", ""], "Data-And-Pipelines", "etl_enrichment_v2")
    assert tags == tuple(sorted({"custom", "data-and-pipelines", "etl", "enrichment", "v2"}))


def test_derive_tags_handles_non_list_and_empty_inputs() -> None:
    assert _derive_tags(None, "", "-") == ()


def test_index_as_dicts_defaults_to_global_index() -> None:
    assert index_as_dicts() == [recipe.as_dict() for recipe in RECIPES]


def test_index_as_dicts_accepts_explicit_recipes() -> None:
    recipe = _make_recipe()
    assert index_as_dicts([recipe]) == [recipe.as_dict()]


def test_index_as_json_is_pretty_and_newline_terminated() -> None:
    rendered = index_as_json([_make_recipe()])
    assert rendered.endswith("}\n]\n") or rendered.endswith("\n")
    assert "\n  " in rendered


def test_load_index_parses_temp_examples(tmp_path: Path) -> None:
    recipe_dir = tmp_path / "cat" / "example"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text(
        "slug: demo\ntitle: Demo\ncategory: cat\ndescription: d\ntags:\n  - special\n"
    )
    recipes = load_index(tmp_path)
    assert len(recipes) == 1
    assert recipes[0].example_path == "cat/example"
    assert "special" in recipes[0].tags


def test_load_index_tolerates_empty_recipe_yaml(tmp_path: Path) -> None:
    recipe_dir = tmp_path / "cat" / "blank"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text("")
    recipes = load_index(tmp_path)
    assert len(recipes) == 1
    assert recipes[0].slug == ""
    assert recipes[0].tags == ()


def test_find_recipe_without_filters_returns_all() -> None:
    assert find_recipe() == RECIPES


def test_find_recipe_by_query_matches_description() -> None:
    corpus = [
        _make_recipe(slug="a", description="uses Azure OpenAI", tags=()),
        _make_recipe(slug="b", description="plain HTTP", tags=()),
    ]
    results = find_recipe("openai", recipes=corpus)
    assert [r.slug for r in results] == ["a"]


def test_find_recipe_by_tag_filters_exact() -> None:
    corpus = [
        _make_recipe(slug="a", tags=("durable",)),
        _make_recipe(slug="b", tags=("http",)),
    ]
    assert [r.slug for r in find_recipe(tag="Durable", recipes=corpus)] == ["a"]


def test_find_recipe_combines_query_and_tag() -> None:
    corpus = [
        _make_recipe(slug="a", description="retry pattern", tags=("durable",)),
        _make_recipe(slug="b", description="retry pattern", tags=("http",)),
    ]
    assert [r.slug for r in find_recipe("retry", tag="durable", recipes=corpus)] == ["a"]


def test_find_recipe_no_match_returns_empty() -> None:
    assert find_recipe("this-string-matches-nothing-xyz") == []


def test_find_recipe_multi_term_requires_all_terms() -> None:
    corpus = [
        _make_recipe(slug="a", title="Durable Retry Pattern", tags=()),
        _make_recipe(slug="b", title="Durable Timer", tags=()),
    ]
    results = find_recipe("durable retry", recipes=corpus)
    assert [r.slug for r in results] == ["a"]


def test_find_recipe_multi_term_is_order_independent() -> None:
    corpus = [
        _make_recipe(slug="a", title="Durable Retry Pattern", tags=()),
    ]
    assert [r.slug for r in find_recipe("retry durable", recipes=corpus)] == ["a"]


def test_find_recipe_multi_term_no_match_when_one_term_absent() -> None:
    corpus = [
        _make_recipe(slug="a", title="Durable Retry Pattern", tags=()),
    ]
    assert find_recipe("durable queue", recipes=corpus) == []


def test_recipes_json_index_is_up_to_date() -> None:
    """Drift guard: committed recipes.json must match the generated index."""
    committed = (_ROOT / "recipes.json").read_text()
    assert committed == index_as_json(), (
        "recipes.json is stale. Run: python scripts/gen_recipe_index.py"
    )


def test_generator_check_mode_passes_when_index_current() -> None:
    script = _ROOT / "scripts" / "gen_recipe_index.py"
    spec = importlib.util.spec_from_file_location("gen_recipe_index", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main(["--check"]) == 0
