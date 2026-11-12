"""Keep the stability page aligned with the recipe metadata it summarizes (#466)."""

from __future__ import annotations

from pathlib import Path
import re
import tomllib

import pytest
import yaml

pytestmark = pytest.mark.repo_infra

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "stability-and-compatibility.md"
LEVELS = {"docs", "unit", "func-host", "azure"}


def _recipes() -> list[Path]:
    return sorted((ROOT / "examples").glob("*/*/recipe.yaml"))


def test_page_is_in_the_docs_navigation() -> None:
    assert "stability-and-compatibility.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def test_levels_used_by_recipes_are_the_documented_ones() -> None:
    levels = {yaml.safe_load(p.read_text(encoding="utf-8"))["verification"] for p in _recipes()}
    assert levels <= LEVELS


def test_azure_claim_matches_recipe_metadata() -> None:
    """Docs say no recipe is verified in deployed Azure; revise them if that changes."""
    azure = [
        p.parent.name
        for p in _recipes()
        if yaml.safe_load(p.read_text(encoding="utf-8"))["verification"] == "azure"
    ]
    assert azure == [], (
        f"Recipes now declare verification: azure ({azure}); revise the stability docs"
    )


def test_langgraph_recipe_list_matches_declared_dependencies() -> None:
    declaring = set()
    for recipe in _recipes():
        pyproject = recipe.parent / "pyproject.toml"
        if not pyproject.is_file():
            continue
        deps = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
        specs = list(deps.get("dependencies", []))
        for group in deps.get("optional-dependencies", {}).values():
            specs.extend(group)
        if any(re.match(r"azure[-_.]functions[-_.]langgraph\b", spec, re.I) for spec in specs):
            declaring.add(recipe.parent.name)
    text = PAGE.read_text(encoding="utf-8")
    listed = set(re.findall(r"`(\w+_agent|langgraph_\w+)`", text.split("## LangGraph recipes")[1]))
    assert declaring <= listed, (
        f"LangGraph recipes missing from the stability page: {declaring - listed}"
    )
