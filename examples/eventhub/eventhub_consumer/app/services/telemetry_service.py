from __future__ import annotations

from typing import Any


def process_telemetry(telemetry: dict[str, Any]) -> str:
    """Simulate telemetry transformation and aggregation logic."""
    metric_name = str(telemetry.get("metric", "unknown_metric"))
    metric_value = telemetry.get("value", "n/a")
    return f"metric={metric_name} value={metric_value} status=recorded"
