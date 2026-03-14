"""Use identity-based Service Bus connections in Azure Functions."""

from __future__ import annotations

import logging

import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="servicebus_queue_trigger_identity")
@app.service_bus_queue_trigger(
    arg_name="message",
    queue_name="orders",
    connection="ServiceBusConnection",
)
def servicebus_queue_trigger_identity(message: func.ServiceBusMessage) -> None:
    """Process Service Bus messages through connection string or managed identity."""
    payload = message.get_body().decode("utf-8")
    logging.info("Received Service Bus message through ServiceBusConnection: %s", payload)
