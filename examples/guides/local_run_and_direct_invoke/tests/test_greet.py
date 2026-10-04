"""Tests for greet service."""

from __future__ import annotations

from app.services.greet_service import build_greeting


def test_build_greeting_with_name() -> None:
    assert build_greeting("Alice") == {"greeting": "Hello, Alice!"}
