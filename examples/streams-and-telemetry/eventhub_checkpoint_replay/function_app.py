# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false

from __future__ import annotations

import json
import os
from typing import Any

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp()

_LAST_OFFSET_BY_PARTITION: dict[str, int] = {}
_PROCESSED_EVENT_IDS: set[str] = set()
EVENTHUB_NAME = os.getenv("EVENTHUB_NAME", "telemetry")


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _load_payload(event: func.EventHubEvent) -> dict[str, Any]:
    body_text = event.get_body().decode("utf-8", errors="replace")
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        payload = {"raw": body_text}

    if isinstance(payload, dict):
        return payload
    return {"value": payload}


def _get_partition_id(event: func.EventHubEvent) -> str:
    direct_partition_id = getattr(event, "partition_id", None)
    if direct_partition_id is not None:
        return str(direct_partition_id)

    metadata = getattr(event, "metadata", None)
    if isinstance(metadata, dict):
        for key in (
            "partition_id",
            "PartitionId",
            "x-opt-partition-id",
            "PartitionContext.PartitionId",
        ):
            if key in metadata and metadata[key] is not None:
                return str(metadata[key])

    partition_key = getattr(event, "partition_key", None)
    if partition_key is not None:
        return f"key:{partition_key}"

    return "unknown"


def _build_event_id(partition_id: str, sequence_number: int | None, offset: int | None) -> str:
    return f"{partition_id}:{sequence_number}:{offset}"


@app.event_hub_message_trigger(
    arg_name="event",
    event_hub_name=EVENTHUB_NAME,
    connection="EventHubConnection",
)
def replay_safe_eventhub_consumer(event: func.EventHubEvent) -> None:
    payload = _load_payload(event)
    partition_id = _get_partition_id(event)
    partition_key = getattr(event, "partition_key", None)
    sequence_number = _coerce_int(getattr(event, "sequence_number", None))
    offset = _coerce_int(getattr(event, "offset", None))
    previous_offset = _LAST_OFFSET_BY_PARTITION.get(partition_id)
    replay_detected = (
        previous_offset is not None and offset is not None and offset <= previous_offset
    )
    event_id = _build_event_id(partition_id, sequence_number, offset)

    logger.info(
        "Event Hub event received",
        extra={
            "event_hub": EVENTHUB_NAME,
            "partition_id": partition_id,
            "partition_key": partition_key,
            "sequence_number": sequence_number,
            "offset": offset,
            "previous_offset": previous_offset,
            "replay_detected": replay_detected,
        },
    )

    if event_id in _PROCESSED_EVENT_IDS:
        logger.warning(
            "Event Hub replay detected; duplicate delivery skipped",
            extra={
                "event_id": event_id,
                "partition_id": partition_id,
                "sequence_number": sequence_number,
                "offset": offset,
            },
        )
        return

    _PROCESSED_EVENT_IDS.add(event_id)
    if offset is not None:
        _LAST_OFFSET_BY_PARTITION[partition_id] = offset

    logger.info(
        "Event Hub event processed",
        extra={
            "event_id": event_id,
            "device_id": payload.get("device_id"),
            "reading": payload.get("reading"),
            "status": "processed",
            "checkpoint_status": "pending-host-checkpoint",
        },
    )
