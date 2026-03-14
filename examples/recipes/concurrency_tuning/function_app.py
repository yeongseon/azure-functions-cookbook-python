"""Queue-triggered function used to demonstrate dynamic concurrency settings."""

from __future__ import annotations

import logging

import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="queue_dynamic_concurrency_demo")
@app.queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="AzureWebJobsStorage",
)
def queue_dynamic_concurrency_demo(message: func.QueueMessage) -> None:
    """Process queue work while host-level dynamic concurrency controls scaling behavior."""
    body = message.get_body().decode("utf-8")
    logging.info("Processing queue item with dynamic concurrency enabled: %s", body)
