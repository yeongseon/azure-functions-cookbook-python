from __future__ import annotations

import json
from typing import Any

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp()


def _load_order_event(msg: func.ServiceBusMessage) -> dict[str, Any]:
    raw_body = msg.get_body().decode("utf-8", errors="replace")
    payload = json.loads(raw_body)
    payload.setdefault("message_id", getattr(msg, "message_id", None))
    payload.setdefault("correlation_id", getattr(msg, "correlation_id", None))
    payload.setdefault("delivery_count", int(getattr(msg, "delivery_count", 1)))
    return payload


def _base_log_context(payload: dict[str, Any], handler_name: str) -> dict[str, Any]:
    return {
        "handler": handler_name,
        "order_id": payload.get("order_id"),
        "customer_id": payload.get("customer_id"),
        "message_id": payload.get("message_id"),
        "correlation_id": payload.get("correlation_id"),
        "delivery_count": payload.get("delivery_count"),
    }


@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="orders",
    subscription_name="email",
    connection="ServiceBusConnection",
)
def order_email_handler(msg: func.ServiceBusMessage) -> None:
    payload = _load_order_event(msg)
    logger.info(
        "Order event fan-out handled by email subscription",
        extra={
            **_base_log_context(payload, "order_email_handler"),
            "template": "order-confirmation",
            "recipient": payload.get("customer_email"),
        },
    )


@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="orders",
    subscription_name="inventory",
    connection="ServiceBusConnection",
)
def order_inventory_handler(msg: func.ServiceBusMessage) -> None:
    payload = _load_order_event(msg)
    items = payload.get("items", [])
    logger.info(
        "Order event fan-out handled by inventory subscription",
        extra={
            **_base_log_context(payload, "order_inventory_handler"),
            "item_count": len(items),
            "sku_list": [item.get("sku") for item in items],
        },
    )


@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="orders",
    subscription_name="analytics",
    connection="ServiceBusConnection",
)
def order_analytics_handler(msg: func.ServiceBusMessage) -> None:
    payload = _load_order_event(msg)
    logger.info(
        "Order event fan-out handled by analytics subscription",
        extra={
            **_base_log_context(payload, "order_analytics_handler"),
            "event_type": payload.get("event_type", "order.created"),
            "total_amount": payload.get("total_amount"),
        },
    )
