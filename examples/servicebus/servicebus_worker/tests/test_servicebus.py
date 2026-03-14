from app.services.servicebus_service import process_message


def test_process_message_returns_expected_summary() -> None:
    payload = {"task": "email-user", "priority": "high"}

    outcome = process_message(payload)

    assert outcome == "task=email-user priority=high status=processed"
