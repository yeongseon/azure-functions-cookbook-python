# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false

from __future__ import annotations

import json
from typing import Any

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp()


def _load_session_payload(msg: func.ServiceBusMessage) -> dict[str, Any]:
    raw_body = msg.get_body().decode("utf-8", errors="replace")
    payload = json.loads(raw_body)
    payload.setdefault("message_id", getattr(msg, "message_id", None))
    payload.setdefault("session_id", getattr(msg, "session_id", None))
    payload.setdefault("delivery_count", int(getattr(msg, "delivery_count", 1)))
    return payload


@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="orders-with-sessions",
    connection="ServiceBusConnection",
    is_sessions_enabled=True,
)
def process_session_message(msg: func.ServiceBusMessage) -> None:
    payload = _load_session_payload(msg)
    logger.info(
        "Service Bus session message received",
        extra={
            "session_id": payload.get("session_id"),
            "message_id": payload.get("message_id"),
            "delivery_count": payload.get("delivery_count"),
            "customer_id": payload.get("customer_id"),
            "order_id": payload.get("order_id"),
            "step": payload.get("step"),
            "sequence": payload.get("sequence"),
        },
    )
