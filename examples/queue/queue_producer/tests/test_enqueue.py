from __future__ import annotations

from app.services.enqueue_service import build_queue_message, validate_payload


def test_validate_payload_rejects_missing_task_type() -> None:
    is_valid, error_message = validate_payload({"payload": {}})
    assert is_valid is False
    assert error_message == "Field 'task_type' is required and must be a non-empty string."


def test_validate_payload_accepts_valid_payload() -> None:
    is_valid, error_message = validate_payload({"task_type": "email", "payload": {"to": "a@b.com"}})
    assert is_valid is True
    assert error_message == ""


def test_build_queue_message_preserves_expected_shape() -> None:
    message = build_queue_message(
        {"task_type": "email", "payload": {"to": "user@example.com"}},
        "message-123",
    )
    assert message == {
        "message_id": "message-123",
        "task_type": "email",
        "payload": {"to": "user@example.com"},
    }
