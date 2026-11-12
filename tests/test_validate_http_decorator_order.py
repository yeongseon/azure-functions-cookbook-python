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

import pytest

from tests._isolation import EXAMPLES_DIR
from tools.recipe_discovery import recipe_files

pytestmark = pytest.mark.repo_infra


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


def _db_binding_receivers(tree: ast.AST) -> set[str]:
    """Names bound to a ``DbBindings(...)`` instance (e.g. ``db``).

    ``@db.output`` / ``@db.input`` are azure-functions-db wrappers, not Azure
    Functions SDK binding decorators, so they never produce a ``FunctionBuilder``.
    """
    receivers: set[str] = set()
    for node in ast.walk(tree):
        value: ast.expr | None = None
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            value, targets = node.value, list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value, targets = node.value, [node.target]
        if isinstance(value, ast.Call) and _decorator_leaf_name(value) == "DbBindings":
            receivers.update(t.id for t in targets if isinstance(t, ast.Name))
    return receivers


def _is_binding_decorator(dec: ast.expr, db_receivers: frozenset[str] = frozenset()) -> bool:
    """Return ``True`` for an ``@<obj>.<name>(...)`` Azure Functions binding.

    Binding/trigger decorators are attribute accesses on the FunctionApp (or a
    Blueprint) instance -- ``@app.route``, ``@app.durable_client_input``, etc.
    ``@validate_http`` and ``@with_context`` are bare names, so they are not
    treated as bindings. Attribute decorators on a ``DbBindings`` instance
    (``@db.output``) are SDK-independent wrappers and are excluded.
    """
    node: ast.expr = dec.func if isinstance(dec, ast.Call) else dec
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id not in db_receivers
    )


def _find_dead_handlers(tree: ast.AST) -> list[str]:
    """Return handler names where ``@validate_http`` is above a binding decorator."""
    dead: list[str] = []
    db_receivers = frozenset(_db_binding_receivers(tree))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        validate_idx: int | None = None
        binding_indices: list[int] = []
        for i, dec in enumerate(node.decorator_list):
            if validate_idx is None and _decorator_leaf_name(dec) == "validate_http":
                validate_idx = i
            if _is_binding_decorator(dec, db_receivers):
                binding_indices.append(i)
        if validate_idx is None or not binding_indices:
            continue
        # index 0 is the topmost/outermost decorator; a binding below
        # @validate_http means @validate_http wrapped a FunctionBuilder.
        if any(validate_idx < binding_idx for binding_idx in binding_indices):
            dead.append(node.name)
    return dead


def _find_db_above_validate(tree: ast.AST) -> list[str]:
    """Return handler names where a ``DbBindings`` decorator is ABOVE ``@validate_http``.

    ``validate_http`` advertises passthrough params as positional-or-keyword but
    accepts only ``req`` positionally; azure-functions-db>=0.9.0 forwards the
    advertised signature positionally, so an outer ``@db.output``/``@db.input``
    raises ``TypeError`` (#503).
    """
    bad: list[str] = []
    db_receivers = _db_binding_receivers(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        validate_idx: int | None = None
        db_indices: list[int] = []
        for i, dec in enumerate(node.decorator_list):
            if validate_idx is None and _decorator_leaf_name(dec) == "validate_http":
                validate_idx = i
            target = dec.func if isinstance(dec, ast.Call) else dec
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id in db_receivers
            ):
                db_indices.append(i)
        if validate_idx is not None and any(i < validate_idx for i in db_indices):
            bad.append(node.name)
    return bad


def test_no_example_places_validate_http_above_a_binding_decorator() -> None:
    offenders: list[str] = []
    for py_file in recipe_files(EXAMPLES_DIR, "*.py"):
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


def test_no_example_places_db_decorator_above_validate_http() -> None:
    offenders: list[str] = []
    for py_file in recipe_files(EXAMPLES_DIR, "*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for handler in _find_db_above_validate(tree):
            rel = py_file.relative_to(EXAMPLES_DIR).as_posix()
            offenders.append(f"{rel}:{handler}")
    assert not offenders, (
        "A DbBindings decorator (@db.output/@db.input) is placed ABOVE @validate_http "
        "(TypeError on azure-functions-db>=0.9.0, #503) in:\n  "
        + "\n  ".join(offenders)
        + "\nPlace it BELOW @validate_http, directly above the handler."
    )


_DB_SOURCE = """
db = DbBindings()
{decorators}
def h(req, out): ...
"""


def _tree(decorators: str) -> ast.AST:
    return ast.parse(_DB_SOURCE.format(decorators=decorators))


def test_db_output_below_validate_http_is_accepted_and_not_a_binding() -> None:
    tree = _tree("@app.route(route='x')\n@validate_http(body=B)\n@db.output('out', url='u')")
    assert _find_dead_handlers(tree) == []
    assert _find_db_above_validate(tree) == []


def test_db_output_above_validate_http_is_flagged() -> None:
    tree = _tree("@app.route(route='x')\n@db.output('out', url='u')\n@validate_http(body=B)")
    assert _find_db_above_validate(tree) == ["h"]
    assert _find_dead_handlers(tree) == []


def test_annotated_dbbindings_receiver_and_sdk_binding_still_detected() -> None:
    tree = ast.parse(
        "db: Any = DbBindings()\n@validate_http(body=B)\n@app.route(route='x')\ndef h(req): ...\n"
    )
    assert _find_dead_handlers(tree) == ["h"]
    assert _db_binding_receivers(tree) == {"db"}
