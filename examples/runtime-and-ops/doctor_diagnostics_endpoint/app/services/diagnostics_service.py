from __future__ import annotations

import os
from typing import Any

from azure_functions_doctor.doctor import Doctor, SectionResult


def get_health_payload() -> dict[str, str]:
    """Return a simple liveness payload without invoking Doctor."""
    return {"status": "healthy"}


def resolve_target_path() -> str:
    """Return ``AFD_TARGET_PATH`` if set, otherwise the current working directory."""
    return os.getenv("AFD_TARGET_PATH") or os.getcwd()


def run_project_diagnostics(target_path: str | None = None) -> list[SectionResult]:
    """Run all Doctor checks against ``target_path`` (or the resolved default)."""
    path = target_path or resolve_target_path()
    doctor = Doctor(path=path)
    return doctor.run_all_checks()


def summarize(sections: list[SectionResult]) -> dict[str, Any]:
    """Reduce a full ``SectionResult`` list to a compact overall/pass-fail summary."""
    overall = "pass" if all(section["status"] == "pass" for section in sections) else "fail"
    return {
        "overall": overall,
        "sections": [
            {
                "title": section["title"],
                "category": section["category"],
                "status": section["status"],
            }
            for section in sections
        ],
    }
