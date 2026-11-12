"""Offline tests for ``tools/compat_report.py`` and ``tools/pytest_outcome_json.py``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import compat_report as report

pytestmark = pytest.mark.repo_infra


def _write_outcomes(path: Path, *records: tuple[str, str, str]) -> Path:
    tests = [{"nodeid": n, "outcome": o, "reason": r} for n, o, r in records]
    path.write_text(json.dumps({"tests": tests}), encoding="utf-8")
    return path


_PASS = ("t.py::test_ok", "passed", "")
_FAIL = ("t.py::test_bad", "failed", "")
_ERROR = ("t.py::test_err", "error", "")
_SKIP = ("t.py::test_skip", "skipped", "no func")


def test_parse_outcomes_counts_each_outcome_and_skip_reasons(tmp_path: Path) -> None:
    counts = report.parse_outcomes(
        _write_outcomes(
            tmp_path / "o.json", _PASS, _FAIL, _ERROR, _SKIP, ("t.py::x", "xfailed", "r")
        )
    )

    assert (counts.tests, counts.passed, counts.failed, counts.errors, counts.skipped) == (
        5,
        1,
        1,
        1,
        2,
    )
    assert counts.skip_reasons == ["t.py::test_skip: no func", "t.py::x: r"]
    assert counts.failures == ["t.py::test_bad", "t.py::test_err"]


def test_parse_pins_ignores_comments_and_normalizes_names(tmp_path: Path) -> None:
    pins = tmp_path / "c.txt"
    pins.write_text(
        "# header\nPyYAML==6.0.3  # inline\n\nazure_functions==1.25.0\n", encoding="utf-8"
    )

    assert report.parse_pins(pins) == {"pyyaml": "6.0.3", "azure-functions": "1.25.0"}


def test_parse_pins_rejects_an_unpinned_line(tmp_path: Path) -> None:
    pins = tmp_path / "c.txt"
    pins.write_text("requests>=2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected `name==version`"):
        report.parse_pins(pins)


def test_compare_pins_reports_drift_and_missing_packages() -> None:
    problems = report.compare_pins({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9"})
    assert problems == ["b: pinned 2, installed 9", "c: pinned 3, installed missing"]


def test_installed_versions_reads_the_environment() -> None:
    assert "pytest" in report.installed_versions()


@pytest.mark.parametrize(
    ("counts", "needle"),
    [
        (report.Counts(), "selected 0 test(s); at least 3 required"),
        (report.Counts(tests=3, passed=2, failed=1), "1 failed and 0 errored"),
        (report.Counts(tests=3, passed=2, skipped=1), "1 skipped"),
        (report.Counts(tests=2, passed=2), "at least 3 required"),
    ],
)
def test_verdict_rejects_weak_evidence(counts: report.Counts, needle: str) -> None:
    assert any(needle in reason for reason in report.verdict(counts, 3, []))


def test_verdict_accepts_a_full_green_run_and_flags_pin_drift() -> None:
    good = report.Counts(tests=3, passed=3)
    assert report.verdict(good, 3, []) == []
    assert report.verdict(good, 3, ["x: pinned 1, installed 2"]) == [
        "dependency drift: x: pinned 1, installed 2"
    ]


def _run(tmp_path: Path, outcomes: Path, pins: str, min_tests: int = 1) -> tuple[int, Path]:
    constraints = tmp_path / "constraints.txt"
    constraints.write_text(pins, encoding="utf-8")
    out = tmp_path / "out"
    code = report.main(
        [
            "--outcomes",
            str(outcomes),
            "--constraints",
            str(constraints),
            "--min-tests",
            str(min_tests),
            "--out",
            str(out),
        ]
    )
    return code, out


def test_main_writes_a_readable_report_for_a_green_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("PR_HEAD_SHA", "def456")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    installed = report.installed_versions()["pytest"]

    code, out = _run(
        tmp_path, _write_outcomes(tmp_path / "o.json", _PASS), f"pytest=={installed}\n"
    )

    data = json.loads((out / "report.json").read_text())
    markdown = (out / "report.md").read_text()
    assert code == 0
    assert data["result"] == "passed"
    assert data["commit"] == {
        "tested": "abc123",
        "pull_request_head": "def456",
        "event": "pull_request",
    }
    assert data["counts"]["selected"] == 1
    assert data["installed_toolkit_packages"] == {
        k: v for k, v in data["installed_all"].items() if k.startswith("azure-")
    }
    assert f"| pytest | {installed} | {installed} |" in markdown
    assert "abc123" in summary.read_text()


def test_main_fails_and_explains_a_skipped_lane(tmp_path: Path) -> None:
    code, out = _run(tmp_path, _write_outcomes(tmp_path / "o.json", _PASS, _SKIP), "")

    data = json.loads((out / "report.json").read_text())
    assert code == 1
    assert data["result"] == "failed"
    assert data["skip_reasons"] == ["t.py::test_skip: no func"]
    assert "Skipped tests and reasons" in (out / "report.md").read_text()


def test_main_fails_when_the_junit_file_is_missing(tmp_path: Path) -> None:
    code, out = _run(tmp_path, tmp_path / "missing.json", "")

    assert code == 1
    assert "no outcome file" in json.loads((out / "report.json").read_text())["reasons"][0]


def test_main_fails_on_dependency_drift(tmp_path: Path) -> None:
    code, _ = _run(tmp_path, _write_outcomes(tmp_path / "o.json", _PASS), "pytest==0.0.1\n")
    assert code == 1


def test_version_of_handles_missing_and_failing_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    assert report._version_of(["definitely-not-a-real-tool"]) == "unavailable"
    assert report._version_of(["python3", "--version"]).startswith("Python")


pytest_plugins = ["pytester"]


def test_outcome_plugin_records_each_test_once_with_its_worst_outcome(
    pytester: pytest.Pytester,
) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def broken():
            raise RuntimeError("setup")

        def test_ok(): ...
        def test_bad(): assert False
        def test_error(broken): ...
        @pytest.mark.skip(reason="no func")
        def test_skip(): ...
        @pytest.mark.xfail(reason="known")
        def test_xfail(): assert False
        def test_runtime_skip(): pytest.skip("late")
        """
    )
    target = pytester.path / "out" / "outcomes.json"

    pytester.runpytest_inprocess(
        "-p",
        "tools.pytest_outcome_json",
        "--outcome-json",
        str(target),
        "--no-cov",
        "-p",
        "no:cacheprovider",
    )

    records = {
        Path(t["nodeid"]).name.split("::")[-1]: t for t in json.loads(target.read_text())["tests"]
    }
    assert {k: v["outcome"] for k, v in records.items()} == {
        "test_ok": "passed",
        "test_bad": "failed",
        "test_error": "error",
        "test_skip": "skipped",
        "test_xfail": "xfailed",
        "test_runtime_skip": "skipped",
    }
    assert records["test_skip"]["reason"] == "no func"
    assert records["test_runtime_skip"]["reason"] == "late"
    assert records["test_xfail"]["reason"] == "known"


def test_outcome_plugin_is_inert_without_the_option(pytester: pytest.Pytester) -> None:
    pytester.makepyfile("def test_ok(): ...")
    result = pytester.runpytest_inprocess("-p", "tools.pytest_outcome_json", "--no-cov")
    assert result.ret == 0
    assert not list(pytester.path.rglob("*.json"))
