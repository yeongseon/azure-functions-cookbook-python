from collections.abc import Iterator
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import pytest

from tools import verification as verification
from tools import verification_lanes as lanes
from tools.verification_environment import clean
from tools.verification_evidence import Summary, redact, save


def test_cleanup_never_traverses_artifact_symlink(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    external = tmp_path / "shared"
    external.mkdir()
    (external / "retained.txt").write_text("preserve")
    (root / "dist").symlink_to(external, target_is_directory=True)
    clean(root)
    assert (external / "retained.txt").read_text() == "preserve"


@pytest.mark.parametrize(
    "text,canary",
    [
        ('{"Authorization": "Bearer CANARY_a"}', "CANARY_a"),
        ("{'Authorization': 'Basic CANARY_b'}", "CANARY_b"),
        ('{"password":"alpha CANARY_c beta"}', "CANARY_c"),
        ('{"token":"with \\"escaped\\" CANARY_d"}', "CANARY_d"),
        ("SharedAccessKey=CANARY_e;InstrumentationKey=CANARY_f", "CANARY_e"),
        ("Proxy-Authorization: Bearer CANARY_g", "CANARY_g"),
    ],
)
def test_redaction_consumes_complete_credentials(text: str, canary: str) -> None:
    assert canary not in redact(text)


def test_redaction_keeps_json_valid_and_preserves_binary_and_symlink(tmp_path: Path) -> None:
    canary = '{"Authorization": "Bearer CANARY_h"}'
    assert json.loads(redact(canary))["Authorization"] == "[REDACTED]"
    image = b"\x89PNG\xff\xfe\x00"
    (tmp_path / "image.png").write_bytes(image)
    external = tmp_path.parent / (tmp_path.name + ".log")
    external.write_text("password=CANARY_i")
    (tmp_path / "link.log").symlink_to(external)
    save(tmp_path, Summary("test", (canary,)))
    assert "CANARY_h" not in (tmp_path / "summary.json").read_text()
    assert json.loads((tmp_path / "summary.json").read_text())["lane"] == "test"
    assert (tmp_path / "image.png").read_bytes() == image
    assert external.read_text() == "password=CANARY_i"


def test_offline_deselects_only_bicep_compilation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test-results/test").mkdir(parents=True)
    with patch.object(verification, "pytest_lane", return_value=Summary("test", ())) as runner:
        verification.offline()
    assert (
        "--deselect=tests/test_bicep_linux_plans.py::test_fixed_python_plan_site_templates_compile_without_bcp025"
        in runner.call_args.args[1]
    )
    assert "--ignore=tests/test_bicep_linux_plans.py" not in runner.call_args.args[1]
    with (
        patch.object(lanes, "bicep_command", return_value=["bicep"]),
        patch.object(lanes, "pytest_lane", return_value=Summary("bicep", ())) as dedicated,
    ):
        lanes.bicep()
    assert "tests/test_bicep_linux_plans.py" in dedicated.call_args.args[1]


@pytest.mark.parametrize("orchestrator", ["integration", "host_smoke"])
def test_cancellation_stops_scheduling_and_saves_incomplete_families(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orchestrator: str
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VERIFICATION_HOST_RECIPE", raising=False)
    stopped = []

    @contextmanager
    def service(directory: Path) -> Iterator[str]:
        try:
            yield "storage"
        finally:
            stopped.append(True)

    calls = []

    def runner(command: list[str], log: Path, timeout: float) -> int:
        if "--version" in command:
            return 0
        calls.append(command)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return 0

    with (
        patch.object(verification, "azurite", service),
        patch.object(shutil, "which", return_value="available"),
        patch.object(verification, "run", runner),
        patch.object(lanes, "run", runner),
    ):
        with pytest.raises(KeyboardInterrupt):
            getattr(verification, orchestrator)()
    assert len(calls) == 2
    assert stopped == [True]
    lane = "host-smoke" if orchestrator == "host_smoke" else "integration"
    summary = json.loads((tmp_path / "test-results" / lane / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    entries = json.loads((tmp_path / "test-results" / lane / "lanes.json").read_text())
    assert any(entry["exit_code"] == 130 for entry in entries)
    if lane == "integration":
        assert any(entry["reason"] == "Required family not executed" for entry in entries)
