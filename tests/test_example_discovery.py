"""Auto-discovered smoke tests for every examples/ recipe.

Rather than hand-writing one ``test_module_loads`` per example, this module
globs ``examples/**/function_app.py`` and parametrizes a single import +
app-registration smoke over every discovered recipe. Adding a new example is
automatically covered here with no test edit required.

Behavior-specific assertions (service helpers, handler logic) live in
``tests/test_examples.py`` as opt-in per-example tests.
"""

from __future__ import annotations

import azure.functions as func
import pytest

from tests._isolation import EXAMPLES_DIR
from tests._isolation import load_example_module as _load_example_module


def _discover_examples() -> list[str]:
    """Return sorted forward-slash example paths relative to ``examples/``."""
    paths = [
        p.parent.relative_to(EXAMPLES_DIR).as_posix()
        for p in EXAMPLES_DIR.glob("*/*/function_app.py")
    ]
    return sorted(paths)


EXAMPLE_PATHS = _discover_examples()


def test_examples_discovered() -> None:
    """Guard against a broken glob silently collecting zero examples."""
    assert EXAMPLE_PATHS, "No examples discovered under examples/*/*/function_app.py"


@pytest.mark.parametrize("example_path", EXAMPLE_PATHS)
def test_example_module_loads(example_path: str) -> None:
    """Every example imports cleanly and exposes a Functions app object."""
    module = _load_example_module(example_path)
    app = getattr(module, "app", None)
    assert app is not None, f"{example_path}/function_app.py does not define `app`"
    assert isinstance(app, (func.FunctionApp, func.Blueprint)) or hasattr(app, "get_functions"), (
        f"{example_path} `app` is not a FunctionApp/Blueprint-like object"
    )
