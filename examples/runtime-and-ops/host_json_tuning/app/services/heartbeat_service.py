from __future__ import annotations


def log_heartbeat(past_due: bool) -> str:
    return f"host_json_tuning timer fired. past_due={past_due}"
