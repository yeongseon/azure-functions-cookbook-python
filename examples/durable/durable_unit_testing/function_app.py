"""Durable Functions sample used for orchestrator unit testing."""

from __future__ import annotations

from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-unit-test",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_unit_test(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("hello_test_orchestrator")
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def hello_test_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, list[str]]:
    names: list[str] = ["Tokyo", "Seattle", "London"]
    outputs: list[str] = []
    for name in names:
        result = yield context.call_activity("say_hello", name)
        outputs.append(result)
    return outputs


@bp.activity_trigger(input_name="payload")
def say_hello(payload: str) -> str:
    return f"Hello {payload}!"


app.register_functions(bp)
