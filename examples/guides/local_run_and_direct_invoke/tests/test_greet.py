"""Tests for greet service."""

from __future__ import annotations

from app.services.greet_service import build_greeting


def test_build_greeting_with_name() -> None:
    resp = build_greeting("Alice")
    assert resp.status_code == 200
    assert "Alice" in resp.get_body().decode()


def test_build_greeting_without_name() -> None:
    resp = build_greeting(None)
    assert resp.status_code == 400
    assert "error" in resp.get_body().decode()
