"""Regression coverage for #362: align the cold start warmup binding with
its parameter.

The recipe declared ``@app.warm_up_trigger("warmup")``, which produces a
``warmupTrigger`` input named ``warmup``, but its Python handler only
accepted ``warmup_context``. The generated binding's input name and the
registered callable's keyword argument disagreed, so dispatching by the
binding name raised ``TypeError`` before ``_preload_dependencies()`` could
run -- defeating the recipe's entire warmup/preloading path.

Uses the actual ``FunctionApp.get_functions()`` metadata and the real
registered callable; no Functions host or Azure deployment is involved.
"""

from __future__ import annotations

import inspect
import json

from tests._isolation import load_example_module

EXAMPLE_PATH = "runtime-and-ops/cold_start_mitigation"


def test_warmup_binding_input_name_matches_python_parameter() -> None:
    module = load_example_module(EXAMPLE_PATH)
    function = next(f for f in module.app.get_functions() if f.get_function_name() == "warmup")
    bindings = json.loads(function.get_function_json())["bindings"]
    binding = next(b for b in bindings if b["type"] == "warmupTrigger")
    handler = function.get_user_function()

    assert binding["name"] in inspect.signature(handler).parameters


def test_warmup_handler_dispatches_by_its_registered_binding_name_and_preloads() -> None:
    module = load_example_module(EXAMPLE_PATH)
    function = next(f for f in module.app.get_functions() if f.get_function_name() == "warmup")
    bindings = json.loads(function.get_function_json())["bindings"]
    binding = next(b for b in bindings if b["type"] == "warmupTrigger")
    handler = function.get_user_function()

    preload_calls: list[dict[str, bool]] = []

    def fake_preload() -> dict[str, bool]:
        result = {"dependencyLoaded": True, "sessionCached": True}
        preload_calls.append(result)
        return result

    module._preload_dependencies = fake_preload  # type: ignore[attr-defined]

    handler(**{binding["name"]: object()})

    assert preload_calls == [{"dependencyLoaded": True, "sessionCached": True}]
