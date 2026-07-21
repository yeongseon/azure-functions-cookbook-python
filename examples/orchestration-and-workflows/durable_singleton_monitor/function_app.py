from __future__ import annotations

import json
from collections.abc import Generator
from datetime import timedelta
from typing import Any

import azure.durable_functions as df
import azure.functions as func

try:
    from pydantic import BaseModel
except ImportError:

    class BaseModel:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, object]:
            return self.__dict__.copy()


from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi

setup_logging(format="json")
logger = get_logger(__name__)
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
MONITOR_INSTANCE_ID = "external-api-monitor"


class MonitorStatus(BaseModel):
    instance_id: str
    ensured: bool


async def _ensure_monitor(client: df.DurableOrchestrationClient) -> str:
    existing = await client.get_status(MONITOR_INSTANCE_ID)
    if existing is None or existing.runtime_status in {
        df.OrchestrationRuntimeStatus.Completed,
        df.OrchestrationRuntimeStatus.Failed,
        df.OrchestrationRuntimeStatus.Terminated,
    }:
        await client.start_new("monitor_orchestrator", instance_id=MONITOR_INSTANCE_ID)
    return MONITOR_INSTANCE_ID


@app.route(route="monitor/start", methods=["POST"])
@with_context
@openapi(
    summary="Ensure singleton monitor", tags=["Durable"], route="/api/monitor/start", method="post"
)
@app.durable_client_input(client_name="client")
async def start_monitor(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    instance_id = await _ensure_monitor(client)
    logger.info("Ensured singleton monitor orchestration", extra={"instance_id": instance_id})
    body = MonitorStatus(instance_id=instance_id, ensured=True)
    return func.HttpResponse(
        body=json.dumps(body.model_dump()), status_code=202, mimetype="application/json"
    )


@app.function_name(name="ensure_monitor_timer")
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer")
@app.durable_client_input(client_name="client")
@with_context
async def ensure_monitor_timer(
    timer: func.TimerRequest, client: df.DurableOrchestrationClient
) -> None:
    instance_id = await _ensure_monitor(client)
    logger.info(
        "Timer checked singleton monitor",
        extra={"instance_id": instance_id, "past_due": timer.past_due},
    )


@app.orchestration_trigger(context_name="context")
def monitor_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, None]:
    result = yield context.call_activity("poll_external_state", None)
    if result.get("changed"):
        yield context.call_activity("emit_alert", result)
    next_check = context.current_utc_datetime + timedelta(minutes=5)
    yield context.create_timer(next_check)
    context.continue_as_new(None)


@app.activity_trigger(input_name="payload")
def poll_external_state(payload: object) -> dict[str, object]:
    _ = payload
    result = {"target": "inventory-api", "changed": True, "version": "etag-2026-04-17T12:00:00Z"}
    logger.info("Polled external API state", extra=result)
    return result


@app.activity_trigger(input_name="payload")
def emit_alert(payload: dict[str, object]) -> None:
    logger.warning("Detected monitored state change", extra=payload)
