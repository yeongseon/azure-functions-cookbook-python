from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

from app.services.telemetry_service import process_telemetry

eventhub_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@eventhub_blueprint.event_hub_message_trigger(
    arg_name="event",
    event_hub_name="telemetry",
    connection="EventHubConnection",
)
def process_event_hub_message(event: func.EventHubEvent) -> None:
    """Process a telemetry event and log stream offsets for traceability."""
    body_text = event.get_body().decode("utf-8", errors="replace")

    try:
        telemetry: dict[str, Any] = json.loads(body_text)
    except json.JSONDecodeError:
        telemetry = {"raw": body_text}

    partition_key = getattr(event, "partition_key", None)
    sequence_number = getattr(event, "sequence_number", None)
    offset = getattr(event, "offset", None)

    logger.info(
        "Event Hub message partition_key=%s sequence_number=%s offset=%s",
        partition_key,
        sequence_number,
        offset,
    )

    outcome = process_telemetry(telemetry)
    logger.info("Telemetry processed: %s", outcome)
