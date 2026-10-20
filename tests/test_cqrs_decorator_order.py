"""Regression tests for #380: CQRS's create_order must keep its Azure
binding decorators (@app.route, @app.cosmos_db_output) on the same SDK
FunctionBuilder, outside ordinary wrappers (@with_context, @openapi,
@validate_http).

Placing @app.cosmos_db_output below those wrappers split the output
binding onto a different builder than the trigger, so app.get_functions()
raised ValueError("Function create_order does not have a trigger")
before the Python worker could even attempt registration.
"""

from __future__ import annotations

from tests._isolation import load_example_module

EXAMPLE_PATH = "data-and-pipelines/cqrs_read_projection"


def test_app_discovers_exactly_three_named_functions() -> None:
    module = load_example_module(EXAMPLE_PATH)

    functions = module.app.get_functions()

    names = sorted(function.get_function_name() for function in functions)
    assert names == ["create_order", "get_order_projection", "project_order_read_models"]


def test_create_order_has_http_and_cosmos_bindings_on_one_function() -> None:
    """create_order must carry its HTTP trigger/return and Cosmos output
    binding on a single SDK Function -- not split across an orphaned
    builder that lost its trigger."""
    module = load_example_module(EXAMPLE_PATH)
    functions = module.app.get_functions()
    create_order = next(f for f in functions if f.get_function_name() == "create_order")

    bindings = {(binding.name, binding.type) for binding in create_order.get_bindings()}

    assert ("req", "httpTrigger") in bindings
    assert ("$return", "http") in bindings
    assert ("order_doc", "cosmosDB") in bindings
    assert create_order.get_trigger() is not None
    assert create_order.get_trigger().type == "httpTrigger"
