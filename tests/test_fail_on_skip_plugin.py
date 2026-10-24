"""Tests for ``tools/pytest_fail_on_skip.py``, the plugin that fails required lanes on skips."""

from __future__ import annotations

import pytest

pytest_plugins = ["pytester"]

_PLUGIN = ("-p", "tools.pytest_fail_on_skip", "--no-cov", "-p", "no:cacheprovider")


@pytest.mark.parametrize(
    "body",
    [
        "@pytest.mark.skip\ndef test_a(): ...",
        "def test_a(): pytest.skip('not here')",
        "@pytest.mark.xfail\ndef test_a(): assert False",
    ],
    ids=["marked-skip", "runtime-skip", "xfail"],
)
def test_skipped_or_xfailed_test_fails_the_lane(pytester: pytest.Pytester, body: str) -> None:
    """Offline: a skipped or xfailed test turns a green run into exit status 1."""
    pytester.makepyfile(f"import pytest\n{body}\n")

    result = pytester.runpytest_inprocess(*_PLUGIN)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["*fail-on-skip: 1 skipped*"])


def test_module_skipped_at_collection_fails_even_if_other_modules_pass(
    pytester: pytest.Pytester,
) -> None:
    """Offline: a module-level ``importorskip`` cannot hide behind passing modules."""
    pytester.makepyfile(
        test_missing="import pytest\npytest.importorskip('no_such_module_for_fail_on_skip')\n",
        test_ok="def test_ok(): ...",
    )

    result = pytester.runpytest_inprocess(*_PLUGIN)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["*fail-on-skip: 1 skipped*test_missing.py*"])


def test_suite_without_skips_still_passes(pytester: pytest.Pytester) -> None:
    """Offline: the plugin does not fail a run that executed every test."""
    pytester.makepyfile("def test_a(): ...")

    assert pytester.runpytest_inprocess(*_PLUGIN).ret == pytest.ExitCode.OK


def test_zero_selected_tests_stay_exit_status_five(pytester: pytest.Pytester) -> None:
    """Offline: selecting nothing is never reported as success."""
    pytester.makepyfile("def test_a(): ...")

    result = pytester.runpytest_inprocess(*_PLUGIN, "-k", "nothing")

    assert result.ret == pytest.ExitCode.NO_TESTS_COLLECTED
