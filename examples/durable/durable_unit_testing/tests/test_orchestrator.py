"""Unit test showing generator-style orchestration testing."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import Mock, call

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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
azure_functions.__dict__["FunctionApp"] = _StubFunctionApp
azure_functions.__dict__["AuthLevel"] = _StubAuthLevel
azure_functions.__dict__["HttpRequest"] = object
azure_functions.__dict__["HttpResponse"] = object
sys.modules["azure.functions"] = azure_functions

azure_durable = types.ModuleType("azure.durable_functions")
azure_durable.__dict__["Blueprint"] = _StubBlueprint
azure_durable.__dict__["DurableOrchestrationClient"] = object
azure_durable.__dict__["DurableOrchestrationContext"] = object
sys.modules["azure.durable_functions"] = azure_durable


def test_hello_test_orchestrator_steps_generator() -> None:
    from app.functions.orchestration import hello_test_orchestrator

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
