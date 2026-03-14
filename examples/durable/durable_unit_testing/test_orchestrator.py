"""Unit test showing generator-style orchestration testing."""

from __future__ import annotations

from pathlib import Path
import sys
import types
from unittest.mock import Mock, call

sys.path.insert(0, str(Path(__file__).resolve().parent))


class _StubFunctionApp:
    def register_functions(self, bp: object) -> None:
        del bp


class _StubBlueprint:
    def route(self, **kwargs: object):
        del kwargs

        def _decorator(func: object) -> object:
            return func

        return _decorator

    def durable_client_input(self, **kwargs: object):
        del kwargs

        def _decorator(func: object) -> object:
            return func

        return _decorator

    def orchestration_trigger(self, **kwargs: object):
        del kwargs

        def _decorator(func: object) -> object:
            return func

        return _decorator

    def activity_trigger(self, **kwargs: object):
        del kwargs

        def _decorator(func: object) -> object:
            return func

        return _decorator


class _StubAuthLevel:
    ANONYMOUS = "ANONYMOUS"


if "azure" not in sys.modules:
    sys.modules["azure"] = types.ModuleType("azure")

azure_functions = types.ModuleType("azure.functions")
setattr(azure_functions, "FunctionApp", _StubFunctionApp)
setattr(azure_functions, "AuthLevel", _StubAuthLevel)
setattr(azure_functions, "HttpRequest", object)
setattr(azure_functions, "HttpResponse", object)
sys.modules["azure.functions"] = azure_functions

azure_durable = types.ModuleType("azure.durable_functions")
setattr(azure_durable, "Blueprint", _StubBlueprint)
setattr(azure_durable, "DurableOrchestrationClient", object)
setattr(azure_durable, "DurableOrchestrationContext", object)
sys.modules["azure.durable_functions"] = azure_durable


def test_hello_test_orchestrator_steps_generator() -> None:
    from function_app import hello_test_orchestrator

    context = Mock()
    context.call_activity.side_effect = ["task-1", "task-2", "task-3"]

    generator = hello_test_orchestrator(context)

    first_yield = next(generator)
    assert first_yield == "task-1"

    second_yield = generator.send("Hello Tokyo!")
    assert second_yield == "task-2"

    third_yield = generator.send("Hello Seattle!")
    assert third_yield == "task-3"

    try:
        generator.send("Hello London!")
    except StopIteration as stop:
        final_value = stop.value
    else:
        raise AssertionError("Orchestrator generator should have completed.")

    assert final_value == ["Hello Tokyo!", "Hello Seattle!", "Hello London!"]
    assert context.call_activity.call_args_list == [
        call("say_hello", "Tokyo"),
        call("say_hello", "Seattle"),
        call("say_hello", "London"),
    ]
