"""Use identity-based Azure Storage Queue connections in Azure Functions."""

from __future__ import annotations

import logging

import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="storage_queue_trigger_identity")
@app.queue_trigger(
    arg_name="message",
    queue_name="orders",
    connection="StorageConnection",
)
def storage_queue_trigger_identity(message: func.QueueMessage) -> None:
    """Process queue messages using either connection string or managed identity settings."""
    payload = message.get_body().decode("utf-8")
    logging.info("Received queue message through StorageConnection: %s", payload)
