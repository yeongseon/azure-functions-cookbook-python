from __future__ import annotations

from app.services.heartbeat_service import log_heartbeat


def test_log_heartbeat_not_past_due() -> None:
    assert log_heartbeat(past_due=False) == "host_json_tuning timer fired. past_due=False"


def test_log_heartbeat_past_due() -> None:
    assert log_heartbeat(past_due=True) == "host_json_tuning timer fired. past_due=True"
