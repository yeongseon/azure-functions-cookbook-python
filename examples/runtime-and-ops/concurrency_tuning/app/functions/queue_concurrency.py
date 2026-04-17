"""Queue trigger demonstrating dynamic concurrency settings."""

from __future__ import annotations

import azure.functions as func

from app.services.concurrency_service import process_concurrent_message

queue_concurrency_blueprint = func.Blueprint()


@queue_concurrency_blueprint.function_name(name="queue_dynamic_concurrency_demo")
@queue_concurrency_blueprint.queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="AzureWebJobsStorage",
)
def queue_dynamic_concurrency_demo(message: func.QueueMessage) -> None:
    """Process queue work while host-level dynamic concurrency controls scaling behavior."""
    body = message.get_body().decode("utf-8")
    process_concurrent_message(body)
