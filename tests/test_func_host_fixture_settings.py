"""Regression tests for #366: the Functions-host E2E fixture must preserve
a developer's pre-existing ``local.settings.json`` on every exit path.

These tests are deterministic and require no Core Tools, Azurite, or real
process: ``subprocess.Popen`` is mocked (returning a stand-in object, or
raising, per scenario), so only the fixture's filesystem backup/restore
lifecycle is exercised.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.e2e import conftest as host

_ORIGINAL_CONTENT = '{"Values":{"RecipeProfile":"keep-my-local-setting"}}\n'


def _make_example(tmp_path: Path, name: str, *, with_existing_settings: bool) -> Path:
    project = tmp_path / "apis-and-ingress" / name
    project.mkdir(parents=True)
    if with_existing_settings:
        (project / "local.settings.json").write_text(_ORIGINAL_CONTENT)
    return project


def test_preexisting_settings_restored_after_successful_run(tmp_path: Path) -> None:
    example = _make_example(tmp_path, "demo-success", with_existing_settings=True)
    settings_path = example / "local.settings.json"

    with (
        patch.object(host, "EXAMPLES_ROOT", tmp_path),
        patch("subprocess.Popen", return_value=object()),
        patch.object(host, "wait_for_port", return_value=None),
        patch.object(host, "_kill_process_group", return_value=None),
    ):
        with host.run_func_host("apis-and-ingress/demo-success", port=17071):
            pass

    assert settings_path.read_text() == _ORIGINAL_CONTENT


def test_preexisting_settings_restored_when_test_body_raises(tmp_path: Path) -> None:
    example = _make_example(tmp_path, "demo-body-error", with_existing_settings=True)
    settings_path = example / "local.settings.json"

    with pytest.raises(RuntimeError, match="boom"):
        with (
            patch.object(host, "EXAMPLES_ROOT", tmp_path),
            patch("subprocess.Popen", return_value=object()),
            patch.object(host, "wait_for_port", return_value=None),
            patch.object(host, "_kill_process_group", return_value=None),
        ):
            with host.run_func_host("apis-and-ingress/demo-body-error", port=17072):
                raise RuntimeError("boom")

    assert settings_path.read_text() == _ORIGINAL_CONTENT


def test_preexisting_settings_restored_on_host_readiness_failure(tmp_path: Path) -> None:
    example = _make_example(tmp_path, "demo-not-ready", with_existing_settings=True)
    settings_path = example / "local.settings.json"

    class _FakeProc:
        def communicate(self, timeout: float | None = None) -> tuple[bytes, bytes]:
            return b"host did not start", b""

    with (
        patch.object(host, "EXAMPLES_ROOT", tmp_path),
        patch("subprocess.Popen", return_value=_FakeProc()),
        patch.object(host, "wait_for_port", side_effect=TimeoutError("not ready")),
    ):
        with pytest.raises(pytest.fail.Exception):
            with host.run_func_host("apis-and-ingress/demo-not-ready", port=17073):
                pass

    assert settings_path.read_text() == _ORIGINAL_CONTENT


def test_preexisting_settings_restored_on_process_launch_exception(tmp_path: Path) -> None:
    example = _make_example(tmp_path, "demo-launch-error", with_existing_settings=True)
    settings_path = example / "local.settings.json"

    with pytest.raises(FileNotFoundError):
        with (
            patch.object(host, "EXAMPLES_ROOT", tmp_path),
            patch("subprocess.Popen", side_effect=FileNotFoundError("func not found")),
        ):
            with host.run_func_host("apis-and-ingress/demo-launch-error", port=17074):
                pass

    assert settings_path.read_text() == _ORIGINAL_CONTENT


def test_generated_settings_still_removed_when_none_existed(tmp_path: Path) -> None:
    """The fixture's own current behavior -- cleaning up settings it
    generated when no original file existed -- must be unchanged."""
    example = _make_example(tmp_path, "demo-no-original", with_existing_settings=False)
    settings_path = example / "local.settings.json"

    with (
        patch.object(host, "EXAMPLES_ROOT", tmp_path),
        patch("subprocess.Popen", return_value=object()),
        patch.object(host, "wait_for_port", return_value=None),
        patch.object(host, "_kill_process_group", return_value=None),
    ):
        with host.run_func_host("apis-and-ingress/demo-no-original", port=17075):
            assert settings_path.exists()

    assert not settings_path.exists()
