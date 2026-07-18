"""Shared import-isolation helpers for example smoke and e2e tests.

Cookbook examples are standalone Azure Functions projects. Many of them use a
local ``app`` package (blueprint / app-layout examples), so importing several
examples in the same test process risks ``sys.modules`` collisions between one
example's ``app`` and the next. These helpers centralize the ``sys.path`` /
``sys.modules`` ``app.*`` cleanup so both ``tests/test_examples.py`` and
``tests/e2e/conftest.py`` share a single implementation instead of duplicating it.
"""

from __future__ import annotations

import importlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def clean_app_modules() -> None:
    """Remove all ``app`` and ``app.*`` modules from ``sys.modules``.

    Blueprint examples use a local ``app`` package. When loading multiple
    examples in the same process the cached ``app`` from one example will
    conflict with the next. Cleaning these entries forces a fresh import.
    """
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]


def load_example_module(example_path: str) -> ModuleType:
    """Import an example's ``function_app.py`` and return the module.

    ``example_path`` uses forward-slash separators for nested examples,
    e.g. ``"apis-and-ingress/hello_http_minimal"``.
    """
    module_path = EXAMPLES_DIR / example_path / "function_app.py"
    module_name = f"cookbook_example_{example_path.replace('/', '_')}"

    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean previous app.* modules to avoid import collisions.
    clean_app_modules()

    if module_name in sys.modules:
        del sys.modules[module_name]

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    try:
        spec = spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to load example module from {module_path}")
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)

    return module


def import_service(example_path: str, service_module: str) -> Any:
    """Import a service module from an example directory.

    Must be called *after* :func:`load_example_module` for the same example so
    that any ``app.core`` side-effects (e.g. ``configure_logging``) have already
    been executed.
    """
    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean cached ``app.*`` to ensure we load from the correct example.
    clean_app_modules()

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    try:
        return importlib.import_module(service_module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)


def import_function_module(example_path: str, function_module: str) -> Any:
    """Import a function Blueprint module from an example directory.

    Used when tests need to call the actual Azure Function handler
    (e.g. ``github_webhook``, ``mcp_endpoint``).
    """
    example_dir = str(EXAMPLES_DIR / example_path)

    # Clean cached ``app.*`` to ensure we load from the correct example.
    clean_app_modules()

    added_to_path = False
    if example_dir not in sys.path:
        sys.path.insert(0, example_dir)
        added_to_path = True

    try:
        return importlib.import_module(function_module)
    finally:
        if added_to_path and example_dir in sys.path:
            sys.path.remove(example_dir)
