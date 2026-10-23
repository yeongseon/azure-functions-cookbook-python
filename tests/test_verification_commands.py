import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_azure_preflight_blocks_before_pytest(tmp_path: Path) -> None:
    # Given: no deployed endpoint and an isolated results directory.
    environment = {key: value for key, value in os.environ.items() if key != "E2E_BASE_URL"}
    environment["PYTHONPATH"] = str(ROOT)
    # When: the public runner is invoked.
    result = subprocess.run(
        [sys.executable, "-m", "tools.verification", "azure-e2e"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    # Then: no tests ran and missing prerequisite evidence is explicit.
    assert result.returncode != 0
    assert "INCOMPLETE" in result.stdout
    assert "E2E_BASE_URL" in result.stdout
    assert not list(tmp_path.rglob("junit.xml"))


def test_doctor_fails_when_required_tool_is_hidden(monkeypatch: pytest.MonkeyPatch) -> None:
    from tools import verification_environment as environment

    # Given: all required tools except bandit are discoverable.
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "bandit" else name)
    # When / Then: diagnostics fail closed, without invoking tests.
    assert environment.doctor() != 0


def test_new_recipe_joins_metadata_reporting_matrix(tmp_path: Path) -> None:
    from scripts.new_recipe import create_recipe
    from tools.verification_manifest import recipes

    # Given: a temporary examples category, never the working tree.
    (tmp_path / "examples/apis-and-ingress").mkdir(parents=True)
    # When: the unchanged recipe generator creates a recipe.
    create_recipe(
        "apis-and-ingress",
        "new_probe",
        difficulty="Beginner",
        examples_dir=tmp_path / "examples",
    )
    # Then: manifest discovery immediately includes its family and unsupported Azure status.
    discovered = recipes(tmp_path)
    assert len(discovered) == 1
    assert discovered[0].family == "apis-and-ingress"
    assert discovered[0].path == "apis-and-ingress/new_probe"
    assert not discovered[0].azure_supported


def test_clean_preserves_tracked_artifacts_and_environments(tmp_path: Path) -> None:
    from tools.verification_environment import clean

    # Given: even an artifact-looking path may be tracked.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "test-results").mkdir()
    (tmp_path / "test-results/retained.txt").write_text("tracked")
    (tmp_path / "test-results/generated.txt").write_text("generated")
    (tmp_path / "items.db").write_bytes(b"tracked database")
    (tmp_path / ".venv").mkdir()
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "items.db", "test-results/retained.txt"],
        check=True,
    )
    # When: generated-only cleanup runs.
    clean(tmp_path)
    # Then: tracked files and development environment are intact.
    assert (tmp_path / "items.db").read_bytes() == b"tracked database"
    assert (tmp_path / "test-results/retained.txt").read_text() == "tracked"
    assert not (tmp_path / "test-results/generated.txt").exists()
    assert (tmp_path / ".venv").is_dir()
