from app.services.telemetry_service import process_telemetry


def test_process_telemetry_returns_expected_summary() -> None:
    telemetry = {"metric": "cpu", "value": 0.42}

    outcome = process_telemetry(telemetry)

    assert outcome == "metric=cpu value=0.42 status=recorded"
