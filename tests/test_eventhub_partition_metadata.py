"""Regression coverage for #374: read nested Event Hub partition metadata.

The documented Event Hubs trigger metadata nests the partition id under a
``PartitionContext`` object (``metadata["PartitionContext"]["PartitionId"]``);
it is not a flattened ``"PartitionContext.PartitionId"`` key. Because
``_get_partition_id`` only checked flattened top-level keys, it returned
``"unknown"`` for every SDK event, so two distinct events from different
partitions that happened to share a sequence number and offset collided on
the same synthesized event id and the second was skipped as a false
duplicate.

Constructs real ``func.EventHubEvent`` objects with ``Datum``-wrapped JSON
trigger metadata, matching the documented SDK shape; no Event Hub deployment
is involved.
"""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import azure.functions as func
from azure.functions.meta import Datum

from tests._isolation import load_example_module

EXAMPLE_PATH = "streams-and-telemetry/eventhub_checkpoint_replay"


def _event(
    partition_id: str, sequence_number: int, offset: str, device_id: str
) -> func.EventHubEvent:
    return func.EventHubEvent(
        body=json.dumps({"device_id": device_id, "reading": 10}).encode(),
        sequence_number=sequence_number,
        offset=offset,
        trigger_metadata={
            "PartitionContext": Datum(
                json.dumps({"PartitionId": partition_id, "EventHubPath": "telemetry"}), "json"
            )
        },
    )


def test_get_partition_id_reads_nested_partition_context() -> None:
    module = load_example_module(EXAMPLE_PATH)
    event = _event("0", sequence_number=0, offset="0", device_id="device-0")

    assert module._get_partition_id(event) == "0"


def test_events_from_distinct_partitions_with_equal_sequence_and_offset_are_both_processed() -> (
    None
):
    module = load_example_module(EXAMPLE_PATH)
    handler = module.replay_safe_eventhub_consumer.build().get_user_function()
    events = [
        _event(partition_id, sequence_number=0, offset="0", device_id=f"device-{partition_id}")
        for partition_id in ("0", "1")
    ]

    with patch.object(module, "logger", new=Mock()) as logger:
        for event in events:
            handler(event=event)

        processed = [
            call.kwargs["extra"]
            for call in logger.info.call_args_list
            if call.args[0] == "Event Hub event processed"
        ]
        skipped = [call.kwargs["extra"] for call in logger.warning.call_args_list]

    assert len(processed) == 2
    assert len(skipped) == 0
    assert {entry["event_id"] for entry in processed} == {"0:0:0", "1:0:0"}


def test_repeated_event_same_partition_sequence_and_offset_is_still_a_duplicate() -> None:
    module = load_example_module(EXAMPLE_PATH)
    handler = module.replay_safe_eventhub_consumer.build().get_user_function()
    first = _event("0", sequence_number=5, offset="100", device_id="device-0")
    duplicate = _event("0", sequence_number=5, offset="100", device_id="device-0")

    with patch.object(module, "logger", new=Mock()) as logger:
        handler(event=first)
        handler(event=duplicate)

        processed = [
            call.kwargs["extra"]
            for call in logger.info.call_args_list
            if call.args[0] == "Event Hub event processed"
        ]
        skipped = [call.kwargs["extra"] for call in logger.warning.call_args_list]

    assert len(processed) == 1
    assert len(skipped) == 1
    assert skipped[0]["event_id"] == "0:5:100"
