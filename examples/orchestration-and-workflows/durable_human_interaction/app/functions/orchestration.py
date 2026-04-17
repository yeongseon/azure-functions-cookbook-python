from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta
from typing import Any

import azure.durable_functions as df
import azure.functions as func

from app.services.approval_service import APPROVAL_EVENT_NAME, APPROVED_STATUS, TIMED_OUT_STATUS

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
    await client.raise_event(instance_id, APPROVAL_EVENT_NAME, "Approved by API")
    return func.HttpResponse(f"{APPROVAL_EVENT_NAME} raised for instance {instance_id}.")


@bp.orchestration_trigger(context_name="context")
def approval_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, str]:
    timeout_at = context.current_utc_datetime + timedelta(minutes=5)
    event_task = context.wait_for_external_event(APPROVAL_EVENT_NAME)
    timeout_task = context.create_timer(timeout_at)

    winner = yield context.task_any([event_task, timeout_task])
    if winner == event_task:
        if not timeout_task.is_completed:
            cancelable_timeout: Any = timeout_task
            cancelable_timeout.cancel()
        return APPROVED_STATUS

    return TIMED_OUT_STATUS
