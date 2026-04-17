from __future__ import annotations

from app.services.task_service import process_task


def test_process_task_returns_expected_summary() -> None:
    result = process_task(
        {"task_type": "email", "payload": {"to": "a@b.com", "template": "welcome"}}
    )
    assert result == "Task 'email' completed with payload keys: ['template', 'to']"
