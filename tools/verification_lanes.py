from __future__ import annotations

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from tools.verification_environment import bicep_command
from tools.verification_evidence import Summary, collect, publish, redact, save
from tools.verification_manifest import recipes
from tools.verification_process import configured, run


def fresh(directory: Path) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    (directory / "logs").mkdir(parents=True)


def finish(directory: Path, summary: Summary) -> Summary:
    summary = save(directory, summary)
    publish(summary)
    return summary


def pytest_lane(lane: str, selection: list[str]) -> Summary:
    directory = (Path("test-results") / lane).resolve()
    fresh(directory)
    command = [sys.executable, "-m", "pytest", *selection]
    if lane.startswith(("integration/", "host-smoke/")):
        command.extend(
            f"-Werror::{warning}:azure_functions_{package}.*"
            for warning in ("DeprecationWarning", "RuntimeWarning")
            for package in ("logging", "openapi", "validation", "doctor", "db", "langgraph")
        )
    try:
        with tempfile.TemporaryDirectory(prefix="cookbook-junit-") as temporary:
            raw = Path(temporary) / "junit.xml"
            with configured({"COVERAGE_FILE": str(Path(temporary) / ".coverage")}):
                code = run(
                    [*command, "--junitxml=" + str(raw)],
                    directory / "logs/pytest.log",
                    1800,
                )
            if raw.exists():
                (directory / "junit.xml").write_text(redact(raw.read_text()))
        summary = replace(collect(directory, command, code), lane=lane)
    except (OSError, ValueError, ET.ParseError) as error:
        summary = Summary(lane, tuple(command), reason=str(error))
    except KeyboardInterrupt:
        summary = Summary(
            lane, tuple(command), exit_code=130, reason="Interrupted; owned children stopped"
        )
        finish(directory, summary)
        raise
    return finish(directory, summary)


def task(lane: str, command: list[str]) -> Summary:
    directory = Path("test-results") / lane
    fresh(directory)
    code = run(command, directory / "logs/runner.log", 1800)
    summary = Summary(
        lane,
        tuple(command),
        1,
        int(code == 0),
        int(code != 0),
        0,
        "FAIL" if code else "PASS",
        code,
    )
    return finish(directory, summary)


def bicep() -> Summary:
    directory = Path("test-results/bicep")
    cli = bicep_command()
    if not cli:
        fresh(directory)
        return finish(
            directory,
            Summary(
                "bicep",
                ("bicep", "build"),
                reason="Bicep CLI unavailable; install bicep or az bicep first",
            ),
        )
    with configured({"BICEP_CLI": cli[0]}):
        return pytest_lane(
            "bicep", ["tests/test_bicep_compiles.py", "tests/test_bicep_linux_plans.py", "--no-cov"]
        )


def azure() -> Summary:
    directory = Path("test-results/azure-e2e")
    fresh(directory)
    applicability = [
        Summary(
            recipe.path,
            ("Azure",),
            status="NOT_APPLICABLE",
            exit_code=0,
            required=False,
            reason="No deployed-Azure suite exists for this recipe",
        )
        for recipe in recipes(Path(__file__).resolve().parents[1])
    ]
    (directory / "applicability.json").write_text(
        json.dumps([asdict(summary) for summary in applicability], indent=2)
    )
    url = os.environ.get("E2E_BASE_URL", "")
    reason = (
        "E2E_BASE_URL is required before tests"
        if not url
        else ("No deployed-Azure recipe suite is supported; local hosts cannot certify Azure")
    )
    return finish(directory, Summary("azure-e2e", ("make", "e2e-azure"), reason=reason))
