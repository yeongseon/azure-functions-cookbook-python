"""Durable Functions human interaction with external event and timeout."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-approval",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_approval(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("approval_orchestrator")
    return client.create_check_status_response(req, instance_id)


@bp.route(
    route="approve/{instance_id}",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def approve_instance(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = req.route_params["instance_id"]
    await client.raise_event(instance_id, "ApprovalEvent", "Approved by API")
    return func.HttpResponse(f"ApprovalEvent raised for instance {instance_id}.")


@bp.orchestration_trigger(context_name="context")
def approval_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, str]:
    timeout_at = context.current_utc_datetime + timedelta(minutes=5)
    event_task = context.wait_for_external_event("ApprovalEvent")
    timeout_task = context.create_timer(timeout_at)

    winner = yield context.task_any([event_task, timeout_task])
    if winner == event_task:
        if not timeout_task.is_completed:
            timeout_task.cancel()
        return "Approved"

    return "Timed out"


app.register_functions(bp)
