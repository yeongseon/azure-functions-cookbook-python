"""Auto-discovered smoke tests for every examples/ recipe.

Rather than hand-writing one ``test_module_loads`` per example, this module
parametrizes a single import + app-registration smoke over every recipe listed
in ``recipe.yaml`` (the metadata single source of truth). Adding a new example
is automatically covered here once its ``recipe.yaml`` exists.

Behavior-specific assertions (service helpers, handler logic) live in
``tests/test_examples.py`` as opt-in per-example tests.
"""

from __future__ import annotations

import azure.functions as func
import pytest

from tests._isolation import load_example_module as _load_example_module
from tests._recipes import RECIPES

EXAMPLE_PATHS = [r.example_path for r in RECIPES]


def test_examples_discovered() -> None:
    """Guard against a broken glob silently collecting zero examples."""
    assert EXAMPLE_PATHS, "No recipes discovered via recipe.yaml metadata"


@pytest.mark.parametrize("example_path", EXAMPLE_PATHS)
def test_example_module_loads(example_path: str) -> None:
    """Every example imports cleanly and exposes a Functions app object."""
    module = _load_example_module(example_path)
    app = getattr(module, "app", None)
    assert app is not None, f"{example_path}/function_app.py does not define `app`"
    assert isinstance(app, (func.FunctionApp, func.Blueprint)) or hasattr(app, "get_functions"), (
        f"{example_path} `app` is not a FunctionApp/Blueprint-like object"
    )
