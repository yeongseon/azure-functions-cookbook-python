"""Pytest plugin for required lanes: ``-p tools.pytest_fail_on_skip``.

A skipped or xfailed test is not evidence. Zero selected tests already exits 5.
Relies on pytest's default terminal reporter (it is inert under ``-p no:terminal``).
"""

from __future__ import annotations

import pytest


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if exitstatus != 0 or reporter is None:
        return
    unexpected = [r.nodeid for key in ("skipped", "xfailed") for r in reporter.stats.get(key, [])]
    if unexpected:
        reporter.write_line(f"fail-on-skip: {len(unexpected)} skipped: {unexpected[:5]}", red=True)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
