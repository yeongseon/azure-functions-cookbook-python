from __future__ import annotations

import os
from typing import Any

from app.services import diagnostics_service


def test_get_health_payload_returns_healthy() -> None:
    assert diagnostics_service.get_health_payload() == {"status": "healthy"}


def test_resolve_target_path_uses_env_when_set(monkeypatch: Any) -> None:
    monkeypatch.setenv("AFD_TARGET_PATH", "/tmp/custom-target")
    assert diagnostics_service.resolve_target_path() == "/tmp/custom-target"


def test_resolve_target_path_defaults_to_cwd(monkeypatch: Any) -> None:
    monkeypatch.delenv("AFD_TARGET_PATH", raising=False)
    assert diagnostics_service.resolve_target_path() == os.getcwd()


def test_summarize_marks_pass_when_all_pass() -> None:
    sections = [
        {"title": "T1", "category": "c1", "status": "pass", "items": []},
        {"title": "T2", "category": "c2", "status": "pass", "items": []},
    ]
    result = diagnostics_service.summarize(sections)
    assert result["overall"] == "pass"
    assert result["sections"] == [
        {"title": "T1", "category": "c1", "status": "pass"},
        {"title": "T2", "category": "c2", "status": "pass"},
    ]


def test_summarize_marks_fail_when_any_fails() -> None:
    sections = [
        {"title": "T1", "category": "c1", "status": "pass", "items": []},
        {"title": "T2", "category": "c2", "status": "fail", "items": []},
    ]
    result = diagnostics_service.summarize(sections)
    assert result["overall"] == "fail"
