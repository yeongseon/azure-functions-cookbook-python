# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportAny=false

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import TypedDict

import azure.functions as func

logger = logging.getLogger(__name__)

app = func.FunctionApp()


class MetricSummary(TypedDict):
    count: int
    sum: float


class BatchSummary(TypedDict):
    event_count: int
    total_value: float
    metrics: dict[str, MetricSummary]
    partition_keys: list[str]


def _parse_event_body(event: func.EventHubEvent) -> dict[str, object]:
    body_text = event.get_body().decode("utf-8", errors="replace")

    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        payload = {"raw": body_text}

    if not isinstance(payload, dict):
        return {"raw": payload}

    return payload


def aggregate_batch(events: list[func.EventHubEvent]) -> BatchSummary:
    metric_totals: dict[str, MetricSummary] = defaultdict(lambda: {"count": 0, "sum": 0.0})
    partition_keys: list[str] = []
    total_value = 0.0

    for event in events:
        payload = _parse_event_body(event)
        metric_name = str(payload.get("metric", "unknown_metric"))
        value = payload.get("value", 0)

        if isinstance(value, bool):
            numeric_value = float(int(value))
        elif isinstance(value, int | float):
            numeric_value = float(value)
        elif isinstance(value, str):
            try:
                numeric_value = float(value)
            except ValueError:
                numeric_value = 0.0
        else:
            numeric_value = 0.0

        metric_totals[metric_name]["count"] += 1
        metric_totals[metric_name]["sum"] += numeric_value
        total_value += numeric_value

        partition_key = getattr(event, "partition_key", None)
        if partition_key is not None:
            partition_keys.append(str(partition_key))

    return {
        "event_count": len(events),
        "total_value": round(total_value, 2),
        "metrics": {
            metric: {
                "count": totals["count"],
                "sum": round(float(totals["sum"]), 2),
            }
            for metric, totals in metric_totals.items()
        },
        "partition_keys": partition_keys,
    }


@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name="telemetry",
    connection="EventHubConnection",
    cardinality=func.Cardinality.MANY,
)
def process_eventhub_batch_window(events: list[func.EventHubEvent]) -> None:
    summary = aggregate_batch(events)

    logger.info(
        "Processing Event Hub batch size=%s partition_keys=%s",
        summary["event_count"],
        summary["partition_keys"],
    )
    logger.info(
        "Window processed: event_count=%s total_value=%s metrics=%s",
        summary["event_count"],
        summary["total_value"],
        summary["metrics"],
    )
