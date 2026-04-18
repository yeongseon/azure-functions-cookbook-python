from __future__ import annotations

import json
import os
from collections.abc import Generator
from datetime import timedelta
from typing import Any, TypeVar

import azure.durable_functions as df
import azure.functions as func

try:
    from pydantic import BaseModel, Field
except ImportError:

    class BaseModel:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, object]:
            return self.__dict__.copy()

    def Field(default: object = None, **_: object) -> object:
        return default


try:
    from azure_functions_logging import get_logger, setup_logging, with_context
except ImportError:
    import logging

    def setup_logging(*_: object, **__: object) -> None:
        logging.basicConfig(level=logging.INFO)

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def with_context(function):
        return function


try:
    from azure_functions_openapi.decorator import openapi
except ImportError:

    def openapi(*_: object, **__: object):
        def decorator(function):
            return function

        return decorator


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(*_: object, **__: object):
        def decorator(function):
            return function

        return decorator


setup_logging(format="json")
logger = get_logger(__name__)
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
F = TypeVar("F")


class ReminderRequest(BaseModel):
    recipient: str = Field(..., description="Reminder recipient address")
    subject: str = Field(..., description="Reminder subject line")
    delay_days: int = Field(default=7, ge=1, le=30)


class ReminderAccepted(BaseModel):
    instance_id: str
    recipient: str
    delay_days: int
    status_query_get_uri: str | None = None


@app.route(route="reminders/start", methods=["POST"])
@with_context
@openapi(
    summary="Start durable reminder",
    description="Schedules a long-delay reminder by starting a Durable Functions orchestration.",
    tags=["Scheduled"],
    operation_id="startReminder",
    route="/api/reminders/start",
    method="post",
)
@app.durable_client_input(client_name="client")
@validate_http(body=ReminderRequest, response_model=ReminderAccepted)
async def start_reminder(
    req: func.HttpRequest,
    body: ReminderRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    payload = body.model_dump()
    instance_id = await client.start_new("reminder_orchestrator", client_input=payload)
    logger.info("Started reminder orchestration", extra={"instance_id": instance_id, **payload})
    response = await client.create_check_status_response(req, instance_id)
    response_body = ReminderAccepted(
        instance_id=instance_id,
        recipient=payload["recipient"],
        delay_days=int(payload["delay_days"]),
        status_query_get_uri=response.headers.get("Location"),
    )
    return func.HttpResponse(
        body=json.dumps(response_body.model_dump()),
        status_code=202,
        mimetype="application/json",
        headers={"Location": response.headers.get("Location", "")},
    )


@app.orchestration_trigger(context_name="context")
def reminder_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, dict[str, object]]:
    payload = context.get_input() or {}
    delay_days = int(payload.get("delay_days", 7))
    due_time = context.current_utc_datetime + timedelta(days=delay_days)
    yield context.create_timer(due_time)
    result = yield context.call_activity("send_reminder", payload)
    return {"status": "completed", **result}


@app.activity_trigger(input_name="payload")
def send_reminder(payload: dict[str, object]) -> dict[str, object]:
    result = {
        "recipient": payload.get("recipient", "unknown@example.com"),
        "subject": payload.get("subject", "Reminder"),
        "delivery": "queued",
    }
    logger.info("Reminder callback reached delivery step", extra=result)
    return result
