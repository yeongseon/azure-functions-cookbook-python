"""Durable Functions fan-out/fan-in orchestration example."""

from __future__ import annotations

from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-fanout",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_fanout(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("fan_out_fan_in_orchestrator")
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def fan_out_fan_in_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, list[str]]:
    items: list[str] = [f"item-{index}" for index in range(1, 6)]
    tasks = [context.call_activity("process_item", item) for item in items]
    results = yield context.task_all(tasks)
    return results


@bp.activity_trigger(input_name="payload")
def process_item(payload: str) -> str:
    return f"Processed {payload}"


app.register_functions(bp)
