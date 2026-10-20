"""Regression tests for #168: @with_context + @validate_http handlers must
expose a worker-visible parameter literally named ``context``.

The official Azure Functions Python worker recognizes exactly one unbound
(no-binding) parameter name on a decorated handler: ``context``. A handler
decorated with ``@with_context(param="invocation_context")`` instead exposes
``invocation_context`` to the worker's indexer, which rejects the function at
load time with a ``FunctionLoadError`` (`the following parameters are
declared in Python but not in the function definition`). ``@validate_http``'s
``WorkerCompat`` wrapper already passes a literally-named ``context``
parameter through to the worker untouched -- renaming away from it was an
unnecessary workaround that regressed worker registration. These tests
pin the correct, worker-compatible contract directly against each affected
recipe's real decorated handler object, without requiring a full upstream
worker checkout.
"""

from __future__ import annotations

import inspect

from azure.functions.decorators.function_app import Function

from tests._isolation import load_example_module

AFFECTED_EXAMPLES: dict[str, list[str]] = {
    "ai-and-agents/ai_image_generation": ["generate_image"],
    "ai-and-agents/openai_direct_chat": ["chat"],
    "ai-and-agents/embedding_vector_search": ["search"],
    "ai-and-agents/streaming_ai_response": ["stream_chat"],
    "ai-and-agents/langgraph_agent": ["invoke_agent"],
    "ai-and-agents/langgraph_tool_use": ["invoke_tool_agent"],
    "ai-and-agents/langgraph_rag_agent": ["chat"],
    "ai-and-agents/rag_knowledge_api": ["ask", "ingest"],
    "apis-and-ingress/apim_function_backend": ["get_catalog_item"],
    "security-and-tenancy/tenant_isolation": ["query_tenant_invoices"],
    "data-and-pipelines/db_input_output": ["create_item"],
    "realtime/websocket_proxy": ["publish"],
}


def _find_function(functions: list[Function], name: str) -> Function:
    for function in functions:
        if function.get_function_name() == name:
            return function
    raise AssertionError(f"handler {name!r} not registered on app")


def test_affected_handlers_expose_literal_context_parameter() -> None:
    """Every handler the #168 regression report identified must expose a
    parameter literally named ``context`` to the SDK Function object the
    worker indexes -- not ``invocation_context`` or any other name."""
    for example_path, handler_names in AFFECTED_EXAMPLES.items():
        module = load_example_module(example_path)
        # FunctionApp.get_functions() is not idempotent (re-validates
        # function-name uniqueness on each call), so call it once per
        # module load and look handlers up from the same returned list.
        functions = module.app.get_functions()
        for handler_name in handler_names:
            function = _find_function(functions, handler_name)
            params = inspect.signature(function.get_user_function()).parameters
            assert "invocation_context" not in params, (
                f"{example_path}:{handler_name} still exposes the worker-"
                "incompatible 'invocation_context' name"
            )
            assert "context" in params, (
                f"{example_path}:{handler_name} does not expose the worker-"
                "required 'context' parameter"
            )


def test_affected_handlers_use_default_with_context_param() -> None:
    """None of the affected recipes should still configure
    ``@with_context(param="invocation_context")`` in source -- the default
    (``param="context"``) is correct and matches the worker's requirement."""
    for example_path in AFFECTED_EXAMPLES:
        source = (
            load_example_module(example_path).__loader__.get_source(  # type: ignore[union-attr]
                load_example_module(example_path).__name__
            )
            or ""
        )
        assert 'param="invocation_context"' not in source
