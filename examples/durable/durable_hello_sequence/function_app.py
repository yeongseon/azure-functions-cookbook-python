"""Durable Functions orchestration chaining activity calls in sequence."""

from __future__ import annotations

from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-sequence",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_sequence(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("hello_sequence_orchestrator")
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def hello_sequence_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, list[str]]:
    cities: list[str] = ["Tokyo", "Seattle", "London"]
    results: list[str] = []
    for city in cities:
        greeting = yield context.call_activity("say_hello", city)
        results.append(greeting)
    return results


@bp.activity_trigger(input_name="payload")
def say_hello(payload: str) -> str:
    return f"Hello {payload}!"


app.register_functions(bp)
