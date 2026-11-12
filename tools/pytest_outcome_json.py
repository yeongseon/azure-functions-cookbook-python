"""Pytest plugin: ``-p tools.pytest_outcome_json --outcome-json PATH``.

Writes one record per test (``passed``, ``failed``, ``error``, ``skipped`` or ``xfailed``, with the
skip reason) as JSON when the session ends, so ``tools/compat_report.py`` can count outcomes without
parsing XML. A test counts once, with its worst phase outcome.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_RANK = {"passed": 0, "skipped": 1, "xfailed": 1, "failed": 2, "error": 3}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.getgroup("outcome-json").addoption(
        "--outcome-json", default=None, help="Write per-test outcomes to this JSON file"
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--outcome-json"):
        config.pluginmanager.register(_Collector(Path(config.getoption("--outcome-json"))))


def _reason(report: pytest.TestReport) -> str:
    longrepr: Any = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2]).removeprefix("Skipped: ")
    return str(getattr(report, "wasxfail", "") or "no reason given")


class _Collector:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._records: dict[str, dict[str, str]] = {}

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call" and report.outcome == "passed":
            return
        if report.skipped:
            outcome = "xfailed" if hasattr(report, "wasxfail") else "skipped"
        elif report.failed:
            outcome = "failed" if report.when == "call" else "error"
        else:
            outcome = "passed"
        current = self._records.get(report.nodeid)
        if current is None or _RANK[outcome] > _RANK[current["outcome"]]:
            reason = _reason(report) if outcome in ("skipped", "xfailed") else ""
            self._records[report.nodeid] = {"outcome": outcome, "reason": reason}

    def pytest_sessionfinish(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tests = [{"nodeid": key, **value} for key, value in sorted(self._records.items())]
        self._path.write_text(json.dumps({"tests": tests}, indent=2) + "\n", encoding="utf-8")
