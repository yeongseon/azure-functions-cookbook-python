"""Static guard: ``@validate_http`` must never sit above a binding decorator.

When ``@validate_http`` is applied *above* (outer to) an Azure Functions binding
decorator (e.g. ``@app.route``, ``@app.durable_client_input``,
``@app.cosmos_db_output``), the validation decorator receives an SDK
``FunctionBuilder`` instead of the handler. As of azure-functions-validation
0.11.1 this raises a ``RuntimeError`` at import time, but importing every example
under every host configuration is expensive. This AST-only check statically
scans all example source files so a regressed recipe fails fast and clearly,
independent of whether the example is imported during the smoke/e2e suites.

See [how the worker binds handlers, §2](https://yeongseon.dev/azure-functions-python/platform/how-the-worker-binds-handlers/#binding)
-- why decorator order matters.
"""

from __future__ import annotations

import ast

from tests._isolation import EXAMPLES_DIR


def _decorator_leaf_name(dec: ast.expr) -> str | None:
    """Return the final identifier of a decorator, or ``None``.

    Handles bare ``@name``, attribute ``@mod.name`` and call ``@mod.name(...)``.
    """
    node: ast.expr = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_binding_decorator(dec: ast.expr) -> bool:
    """Return ``True`` for an ``@<obj>.<name>(...)`` Azure Functions binding.

    Binding/trigger decorators are attribute accesses on the FunctionApp (or a
    Blueprint) instance -- ``@app.route``, ``@app.durable_client_input``, etc.
    ``@validate_http`` and ``@with_context`` are bare names, so they are not
    treated as bindings.
    """
    node: ast.expr = dec.func if isinstance(dec, ast.Call) else dec
    return isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)


def _find_dead_handlers(tree: ast.AST) -> list[str]:
    """Return handler names where ``@validate_http`` is above a binding decorator."""
    dead: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        validate_idx: int | None = None
        binding_indices: list[int] = []
        for i, dec in enumerate(node.decorator_list):
            if validate_idx is None and _decorator_leaf_name(dec) == "validate_http":
                validate_idx = i
            if _is_binding_decorator(dec):
                binding_indices.append(i)
        if validate_idx is None or not binding_indices:
            continue
        # index 0 is the topmost/outermost decorator; a binding below
        # @validate_http means @validate_http wrapped a FunctionBuilder.
        if any(validate_idx < binding_idx for binding_idx in binding_indices):
            dead.append(node.name)
    return dead


def test_no_example_places_validate_http_above_a_binding_decorator() -> None:
    offenders: list[str] = []
    for py_file in sorted(EXAMPLES_DIR.rglob("*.py")):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for handler in _find_dead_handlers(tree):
            rel = py_file.relative_to(EXAMPLES_DIR).as_posix()
            offenders.append(f"{rel}:{handler}")
    assert not offenders, (
        "@validate_http is placed ABOVE a binding decorator (inactive validation, "
        "no endpoint metadata) in:\n  " + "\n  ".join(offenders) + "\n"
        "Move @validate_http BELOW the binding decorator (innermost) so it wraps "
        "the handler directly."
    )
