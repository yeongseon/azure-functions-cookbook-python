"""Contract tests for the Makefile command surface (#428).

Plans come from ``make -n``. Behaviour comes from real ``make`` runs in a scratch project whose
Hatch, pip and PATH tools are stubs that only log their calls: nothing is installed, no test lane
starts and no network is used.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

import pytest
import yaml

pytestmark = pytest.mark.repo_infra

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKE = shutil.which("make") or "make"
FAIL_ON_SKIP = "-p tools.pytest_fail_on_skip"
PATH_TOOLS = ("uv", "git", "func", "azurite", "bicep")
VERIFY_ONLY_LANES = (
    "scripts/run_recipe_tests.py",
    "tools/compile_bicep_templates.py",
    "-m worker_registration",
    "-m smoke",
    "-m e2e",
    "hatch build",
    "mkdocs build",
)


def _hatch_scripts(env: str) -> dict[str, str]:
    envs: dict[str, dict[str, dict[str, str]]] = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["tool"]["hatch"]["envs"]
    return {**envs["default"]["scripts"], **envs.get(env, {}).get("scripts", {})}


_HATCH_RUN = re.compile(r"\bhatch run (?:(?P<env>[\w-]+):)?(?P<script>[\w-]+)")


def _expand(plan: str) -> str:
    """Replace every ``hatch run <script>`` in *plan* by the command line that script runs."""

    def command(match: re.Match[str]) -> str:
        return _hatch_scripts(match["env"] or "default").get(match["script"], match[0])

    expanded = _HATCH_RUN.sub(command, plan)
    return expanded if expanded == plan else _expand(expanded)


def _plan(*args: str) -> str:
    result = subprocess.run(
        [MAKE, "-n", "--no-print-directory", "-C", str(REPO_ROOT), *args],
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _stub(path: Path, name: str, log: Path, body: str = "") -> Path:
    """An executable that appends ``name|arguments|PYTEST_ADDOPTS`` to *log*, then runs *body*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'#!/bin/sh\nprintf "%s|%s|%s\\n" "{name}" "$*" "${{PYTEST_ADDOPTS-}}" >> "{log}"\n{body}'
    )
    path.chmod(0o755)
    return path


@dataclass(frozen=True)
class Project:
    """A scratch checkout: the real Makefile, a stub Hatch and pip, stub tools as the only PATH."""

    root: Path
    tools: Path
    log: Path
    pip_template: Path

    def make(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        environment = {"PATH": str(self.tools), "PYTHON": sys.executable, **env}
        return subprocess.run(
            [MAKE, "-C", str(self.root), "--no-print-directory", *args],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def rows(self) -> list[tuple[str, str, str]]:
        lines = self.log.read_text().splitlines() if self.log.exists() else []
        return [(tool, args, addopts) for tool, args, addopts in (x.split("|", 2) for x in lines)]

    def calls(self, tool: str) -> list[str]:
        return [args for name, args, _ in self.rows() if name == tool]


@pytest.fixture
def project(tmp_path: Path) -> Project:
    root, tools, log = tmp_path / "project", tmp_path / "tools", tmp_path / "calls.log"
    root.mkdir()
    shutil.copy(REPO_ROOT / "Makefile", root / "Makefile")
    sleep = shutil.which("sleep") or "sleep"
    hatch = _stub(
        tmp_path / "hatch.template",
        "hatch",
        log,
        f'[ -z "${{STUB_SLEEP-}}" ] || {{ {sleep} "$STUB_SLEEP"; printf "end||\\n" >> "{log}"; }}\n'
        'case "$*" in *"${STUB_FAIL:-@none@}"*) exit 1;; esac\n',
    )
    cp = shutil.which("cp") or "cp"
    pip = _stub(
        tmp_path / "pip.template",
        "pip",
        log,
        f'case "$*" in *hatch*) {cp} "{hatch}" "${{0%/*}}/hatch" 2> /dev/null;; esac\n',
    )
    (root / ".venv/bin").mkdir(parents=True)
    shutil.copy(hatch, root / ".venv/bin/hatch")
    shutil.copy(pip, root / ".venv/bin/pip")
    for tool in PATH_TOOLS:
        _stub(tools / tool, tool, log)
    return Project(root, tools, log, pip)


def _missing(result: subprocess.CompletedProcess[str]) -> list[str]:
    prefix = "MISSING  "
    return [
        line.removeprefix(prefix) for line in result.stdout.splitlines() if line.startswith(prefix)
    ]


def test_check_runs_every_check_exactly_once() -> None:
    """Offline: `make check` expands to one ruff check, one format check, one mypy and the lint."""
    plan = _expand(_plan("check"))

    assert plan.count("ruff check src tests") == 1
    assert plan.count("ruff format --check src tests") == 1
    assert plan.count("mypy src tests") == 1
    for part in (
        "tools/lint_hatch_matrix.py",
        "tools/lint_workflow_pins.py",
        "scripts/gen_recipe_index.py --check",
        "scripts/gen_recipe_table.py --check",
        "scripts/gen_requirements.py --check",
        "scripts/check_ecosystem_counts.py",
    ):
        assert plan.count(part) == 1, part


def test_recipe_tests_do_not_force_an_interpreter() -> None:
    """Offline: the runner passes ``sys.executable`` to uv, so the target must not pin UV_PYTHON."""
    assert "UV_PYTHON" not in _plan("recipe-tests")


@pytest.mark.parametrize("target", ["test", "check", "check-all", "verify", "integration", "bicep"])
def test_no_routine_target_upgrades_pip(target: str) -> None:
    """Offline: no plan upgrades pip; Hatch is only installed while it is missing."""
    assert "--upgrade" not in _plan(target)


def test_check_all_keeps_its_meaning() -> None:
    """Offline: `make check-all` stays lint, types, tests and security, without verify's lanes."""
    plan = _expand(_plan("check-all"))

    for part in (
        "mypy src tests",
        "tools/lint_hatch_matrix.py",
        "pytest -v tests",
        "bandit -r src",
    ):
        assert part in plan
    assert not [lane for lane in VERIFY_ONLY_LANES if lane in plan]


def test_verify_runs_each_lane_once_in_dependency_order() -> None:
    """Offline: verify is check, test, recipe suites, Bicep, worker, emulators, build, docs."""
    plan = _expand(_plan("verify"))
    lanes = [
        "mypy src tests",
        "tools/lint_hatch_matrix.py",
        "tools/lint_workflow_pins.py",
        "scripts/gen_requirements.py --check",
        "pytest -v tests",
        *VERIFY_ONLY_LANES[:2],
        "-m worker_registration",
        "-m smoke tests/e2e/",
        "-m e2e tests/e2e/",
        "hatch build",
        "mkdocs build --strict",
    ]

    assert [plan.count(lane) for lane in lanes] == [1] * len(lanes)
    positions = [plan.index(lane) for lane in lanes]
    assert positions == sorted(positions)


@pytest.mark.parametrize(("target", "lanes"), [("integration", 2), ("worker-registration", 1)])
def test_emulator_and_worker_lanes_fail_on_skips(target: str, lanes: int) -> None:
    """Offline: every pytest lane of these targets loads the fail-on-skip plugin."""
    assert _plan(target).count(f'PYTEST_ADDOPTS="{FAIL_ON_SKIP}"') == lanes


def test_verify_test_lane_fails_on_skips_while_make_test_stays_offline() -> None:
    """Offline: verify runs the opt-in real-host tests and rejects skips; `make test` does not."""
    strict = 'COOKBOOK_RUN_PAID_AI_HOST=true PYTEST_ADDOPTS="' + FAIL_ON_SKIP + '"'

    assert _plan("verify").count(strict) == 1
    for target in ("test", "check-all"):
        plan = _plan(target)
        assert "COOKBOOK_RUN_PAID_AI_HOST" not in plan
        assert "pytest_fail_on_skip" not in plan


def test_test_required_runs_the_suite_once_with_the_fail_on_skip_plugin(project: Project) -> None:
    """Offline: the strict lane replaces a stray PYTEST_ADDOPTS and opts the host tests in."""
    result = project.make("test-required", PYTEST_ADDOPTS="-k nothing")

    assert result.returncode == 0
    assert [row for row in project.rows() if row[0] == "hatch"] == [
        ("hatch", "run test", FAIL_ON_SKIP)
    ]


def test_install_ci_installs_into_the_selected_interpreter_and_not_through_hatch() -> None:
    """Offline: `install-ci` is `$(PYTHON) -m pip install -e ".[dev]"` and nothing else."""
    assert _plan("install-ci").strip() == 'python3 -m pip install -e ".[dev]"'
    assert (
        _plan("install-ci", "PYTHON=python3.12").strip() == 'python3.12 -m pip install -e ".[dev]"'
    )


def test_doctor_plan_runs_no_installer_bootstrap_or_test() -> None:
    """Offline: `doctor` has no prerequisite, so its plan cannot install anything or run a test."""
    plan = _plan("doctor")

    for forbidden in ("pip", "hatch run", "pytest", "-m venv"):
        assert forbidden not in plan


def test_doctor_passes_when_every_required_tool_is_present(project: Project) -> None:
    """Offline: `make doctor` lists each tool as ok and exits 0 (python >= 3.11 included)."""
    result = project.make("doctor")

    assert result.returncode == 0, result.stdout
    assert _missing(result) == []
    assert result.stdout.splitlines()[-1] == "doctor: ok"


@pytest.mark.parametrize("tool", PATH_TOOLS)
def test_doctor_names_a_missing_tool_and_exits_non_zero(project: Project, tool: str) -> None:
    """Offline: one absent PATH tool is named, every other tool stays ok, the exit is non-zero."""
    (project.tools / tool).unlink()

    result = project.make("doctor")

    assert result.returncode != 0
    assert _missing(result) == [tool]
    assert "doctor: INCOMPLETE" in result.stdout


@pytest.mark.parametrize("hatch", ["missing", "directory"])
def test_doctor_names_hatch_when_it_is_not_an_executable_file(project: Project, hatch: str) -> None:
    """Offline: an absent Hatch, or a directory at its path, is reported as MISSING."""
    path = project.root / ".venv/bin/hatch"
    path.unlink()
    if hatch == "directory":
        path.mkdir()

    result = project.make("doctor")

    assert result.returncode != 0
    assert _missing(result) == [".venv/bin/hatch"]


@pytest.mark.parametrize(
    ("version", "supported"),
    [("(3, 10, 12)", False), ("(3, 11, 0)", True), ("(3, 14, 4)", True)],
    ids=["3.10", "3.11", "3.14"],
)
def test_doctor_requires_python_3_11_or_newer(
    project: Project, tmp_path: Path, version: str, supported: bool
) -> None:
    """Offline: the selected interpreter is accepted from 3.11 and rejected below it."""
    python = tmp_path / "python"
    python.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" -c "import sys; sys.version_info = {version}; $2"\n'
    )
    python.chmod(0o755)

    result = project.make("doctor", PYTHON=str(python))

    assert (result.returncode == 0) is supported
    assert [line.split(" (")[0] for line in _missing(result)] == (
        [] if supported else ["python >= 3.11"]
    )


def test_doctor_names_python_when_the_selected_interpreter_is_absent(
    project: Project, tmp_path: Path
) -> None:
    """Offline: a PYTHON that does not exist is reported, with the way to select another."""
    result = project.make("doctor", PYTHON=str(tmp_path / "nowhere/python"))

    assert result.returncode != 0
    assert [line.split(" (")[0] for line in _missing(result)] == ["python >= 3.11"]
    assert "PYTHON=python3.11" in result.stdout


def test_doctor_looks_for_bicep_where_the_compile_tool_does(
    project: Project, tmp_path: Path
) -> None:
    """Offline: BICEP_CLI replaces the PATH lookup, so a bogus value is named as missing."""
    (project.tools / "bicep").unlink()
    cli = _stub(tmp_path / "elsewhere/bicep", "bicep", project.log)

    assert project.make("doctor", BICEP_CLI=str(cli)).returncode == 0
    bogus = project.make("doctor", BICEP_CLI=str(tmp_path / "nowhere/bicep"))
    assert bogus.returncode != 0
    assert _missing(bogus) == [str(tmp_path / "nowhere/bicep")]


def test_doctor_with_nothing_installed_names_every_tool_and_changes_nothing(tmp_path: Path) -> None:
    """Offline: an empty PATH and no .venv name all seven requirements and create nothing."""
    bare, empty = tmp_path / "bare", tmp_path / "empty"
    bare.mkdir()
    empty.mkdir()
    shutil.copy(REPO_ROOT / "Makefile", bare / "Makefile")

    result = subprocess.run(
        [MAKE, "-C", str(bare), "--no-print-directory", "doctor"],
        env={"PATH": str(empty)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert [name.split(" (")[0] for name in _missing(result)] == [
        "python >= 3.11",
        ".venv/bin/hatch",
        "uv",
        "git",
        "func",
        "azurite",
        "bicep",
    ]
    assert [path.name for path in bare.iterdir()] == ["Makefile"]


def test_routine_targets_never_call_pip_while_hatch_is_present(project: Project) -> None:
    """Offline: repeated runs neither install nor upgrade anything."""
    for _ in range(3):
        assert project.make("test").returncode == 0

    assert project.calls("pip") == []
    assert project.calls("hatch") == ["run test"] * 3


def test_missing_hatch_is_installed_once_and_pip_is_never_upgraded(project: Project) -> None:
    """Offline: bootstrap runs one `pip install hatch` and later runs find Hatch."""
    (project.root / ".venv/bin/hatch").unlink()

    for _ in range(2):
        assert project.make("test").returncode == 0

    assert project.calls("pip") == ["install --disable-pip-version-check --quiet hatch"]
    assert project.calls("hatch") == ["run test"] * 2


def test_a_directory_at_the_hatch_path_is_not_treated_as_installed(project: Project) -> None:
    """Offline: `-x` is true for a directory, so bootstrap must still install Hatch."""
    hatch = project.root / ".venv/bin/hatch"
    hatch.unlink()
    hatch.mkdir()

    assert project.make("bootstrap").returncode == 0

    assert project.calls("pip") == ["install --disable-pip-version-check --quiet hatch"]


def test_missing_virtual_environment_is_built_by_the_selected_interpreter(
    project: Project, tmp_path: Path
) -> None:
    """Offline: bootstrap creates .venv with PYTHON, installs Hatch, and a second run is silent."""
    shutil.rmtree(project.root / ".venv")
    mkdir = shutil.which("mkdir") or "mkdir"
    cp = shutil.which("cp") or "cp"
    make_venv = f'{mkdir} -p "$3/bin"; {cp} "{project.pip_template}" "$3/bin/pip"'
    python = _stub(
        tmp_path / "python3.11",
        "python",
        project.log,
        f'case "$*" in "-m venv "*) {make_venv};; esac\n',
    )

    first = project.make("bootstrap", PYTHON=str(python))
    second = project.make("bootstrap", PYTHON=str(python))

    assert first.returncode == second.returncode == 0
    assert project.calls("python") == ["-m venv .venv"]
    assert project.calls("pip") == ["install --disable-pip-version-check --quiet hatch"]
    assert second.stdout == ""


@pytest.mark.parametrize("missing", [["func"], ["azurite"], ["func", "azurite"]])
def test_integration_fails_before_any_lane_when_an_emulator_tool_is_missing(
    project: Project, missing: list[str]
) -> None:
    """Offline: a missing `func` or `azurite` is named and no test lane starts."""
    for tool in missing:
        (project.tools / tool).unlink()

    result = project.make("integration")

    assert result.returncode != 0
    assert f"missing required tool(s): {' '.join(missing)} " in result.stdout
    assert project.calls("hatch") == []


def test_integration_runs_smoke_then_e2e_with_only_the_fail_on_skip_plugin(
    project: Project,
) -> None:
    """Offline: both lanes run in order and replace a stray PYTEST_ADDOPTS rather than extend it."""
    result = project.make("integration", PYTEST_ADDOPTS="-k nothing")

    assert result.returncode == 0
    assert [row for row in project.rows() if row[0] == "hatch"] == [
        ("hatch", "run smoke", FAIL_ON_SKIP),
        ("hatch", "run e2e", FAIL_ON_SKIP),
    ]


def test_a_failing_smoke_lane_stops_integration_before_e2e(project: Project) -> None:
    """Offline: the first failing lane fails the target and later lanes never start."""
    result = project.make("integration", STUB_FAIL="run smoke")

    assert result.returncode != 0
    assert project.calls("hatch") == ["run smoke"]


def test_verify_stops_at_the_first_failing_part(project: Project) -> None:
    """Offline: a failing test run keeps every later part from running and fails `make verify`."""
    result = project.make("verify", STUB_FAIL="run test")

    assert result.returncode != 0
    assert project.calls("hatch")[-1] == "run test"
    assert "Full local verification passed." not in result.stdout


def test_verify_stays_serial_under_make_jobs(project: Project) -> None:
    """Offline: `make -j4 verify` never overlaps two parts (they share ports and environments)."""
    result = project.make("-j4", "verify", STUB_SLEEP="0.05")

    assert result.returncode == 0
    tools = [tool for tool, _, _ in project.rows()]
    assert tools == ["hatch", "end"] * (len(tools) // 2)
    assert len(project.calls("hatch")) == 15


@pytest.mark.parametrize("target", ["clean", "clean-all"])
def test_clean_removes_links_without_following_them(
    project: Project, tmp_path: Path, target: str
) -> None:
    """Offline: generated paths that are symlinks are unlinked and their targets are untouched."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    links = ["dist", "build", "__pycache__", ".pytest_cache", "pkg.egg-info"]
    if target == "clean-all":
        shutil.rmtree(project.root / ".venv")
        links += [".venv", ".mypy_cache", ".ruff_cache", "htmlcov", "site"]
    for name in links:
        (project.root / name).symlink_to(outside)

    result = project.make(target, PATH=os.defpath)

    assert result.returncode == 0, result.stderr
    assert (outside / "keep.txt").read_text() == "keep"
    assert not [name for name in links if os.path.lexists(project.root / name)]


def test_worker_environment_matches_the_scheduled_guard_job() -> None:
    """Offline: the Hatch `worker` env pins and pytest command equal the scheduled job's."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    env = pyproject["tool"]["hatch"]["envs"]["worker"]
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/scheduled-trigger-smoke.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["worker-registration-guard"]["steps"]
    install = next(step["run"] for step in steps if "pip install -e" in step.get("run", ""))
    guard = next(
        step["run"] for step in steps if "test_worker_registration_guard" in step.get("run", "")
    )

    assert set(env["extra-dependencies"]) == set(re.findall(r'"([\w.-]+~=[\d.]+)"', install))
    assert env["scripts"]["registration"] == guard.removeprefix("python -m ")
