"""Tests for host config service."""

from __future__ import annotations

from app.services.host_config_service import log_host_config_status


def test_log_host_config_status_not_past_due() -> None:
    log_host_config_status(past_due=False)


def test_log_host_config_status_past_due() -> None:
    log_host_config_status(past_due=True)
