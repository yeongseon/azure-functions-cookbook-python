from app.services.heartbeat_service import log_heartbeat


def test_log_heartbeat() -> None:
    assert log_heartbeat(past_due=False) == "host_json_tuning timer fired. past_due=False"
