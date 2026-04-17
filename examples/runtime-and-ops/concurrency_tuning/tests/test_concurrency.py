"""Tests for concurrency service."""

from __future__ import annotations

from app.services.concurrency_service import process_concurrent_message


def test_process_concurrent_message() -> None:
    result = process_concurrent_message("work-item-1")
    assert result is True


def test_process_concurrent_message_empty() -> None:
    result = process_concurrent_message("")
    assert result is True
