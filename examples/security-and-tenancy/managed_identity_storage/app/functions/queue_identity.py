"""Queue trigger using identity-based storage connections."""

from __future__ import annotations

import azure.functions as func

from app.services.storage_identity_service import process_identity_message

queue_identity_blueprint = func.Blueprint()


@queue_identity_blueprint.function_name(name="queue_identity_trigger")
@queue_identity_blueprint.queue_trigger(
    arg_name="message",
    queue_name="tasks",
    connection="AzureWebJobsStorage",
)
def queue_identity_trigger(message: func.QueueMessage) -> None:
    """Process queue messages using identity-based connection."""
    body = message.get_body().decode("utf-8")
    result = process_identity_message(body)
    if not result:
        raise ValueError("Failed to process identity message")
