from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import shutil
import sys

from tools.verification_environment import clean, doctor
from tools.verification_evidence import Counts, Status, Summary, collect, load, report
from tools.verification_host import azurite
from tools.verification_lanes import azure, bicep, finish, fresh, pytest_lane, task
from tools.verification_manifest import LOCAL_SUITES, recipes
from tools.verification_process import configured, run


def aggregate(lane: str, outcomes: list[Summary]) -> Summary:
    required = [s for s in outcomes if s.required]
    status: Status = "PASS"
    if any(s.status == "FAIL" for s in required):
        status = "FAIL"
    elif not required or any(s.status != "PASS" for s in required):
        status = "INCOMPLETE"
    directory = Path("test-results") / lane
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "lanes.json").write_text(json.dumps([asdict(s) for s in outcomes], indent=2))
    return finish(
        directory,
        Summary(
            lane,
            ("make", lane),
            sum(s.selected for s in outcomes),
            sum(s.passed for s in outcomes),
            sum(s.failed for s in outcomes),
            sum(s.skipped for s in outcomes),
            status,
            int(status != "PASS"),
            scope="FULL_LOCAL" if lane == "verify" else "PARTIAL",
            families={s.lane: Counts(s.selected, s.passed, s.failed, s.skipped) for s in outcomes},
            reason="; ".join(f"{s.lane}={s.status}" for s in outcomes),
        ),
    )


def integration() -> Summary:
    directory = Path("test-results/integration").resolve()
    fresh(directory)
    for tool in ("func", "azurite"):
        run([tool, "--version"], directory / f"logs/{tool}-version.log", 15)
    outcomes: list[Summary] = []
    missing = [name for name in ("func", "azurite") if not shutil.which(name)]
    if missing:
        return finish(
            directory,
            Summary("integration", ("make", "integration"), reason="Missing " + ", ".join(missing)),
        )
    try:
        with azurite(directory):
            for family, path, marker in LOCAL_SUITES:
                outcomes.append(
                    pytest_lane("integration/" + family, [path, "-m", marker, "--no-cov"])
                )
    except (OSError, RuntimeError, TimeoutError) as error:
        outcomes.append(Summary("services", ("azurite", "func"), reason=str(error)))
    except KeyboardInterrupt:
        complete_cancelled("integration", outcomes, [family for family, _, _ in LOCAL_SUITES])
        raise
    for summary in outcomes:
        source = Path("test-results") / summary.lane / "junit.xml"
        if source.exists():
            target = directory / "junit" / (source.parent.name + ".xml")
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
    missing_families = {family for family, _, _ in LOCAL_SUITES} - {
        summary.lane.removeprefix("integration/") for summary in outcomes
    }
    outcomes.extend(
        Summary("integration/" + family, ("pytest",), reason="Required family not executed")
        for family in sorted(missing_families)
    )
    return aggregate("integration", outcomes)


def host_smoke() -> Summary:
    directory = Path("test-results/host-smoke").resolve()
    fresh(directory)
    selection = os.environ.get("VERIFICATION_HOST_RECIPE", "")
    cases = {
        "hello-http": "tests/e2e/test_http_examples.py::TestHelloHttpMinimal",
        "validated-openapi-logging": "tests/e2e/test_package_runtime.py",
    }
    if selection and selection not in cases:
        return finish(directory, Summary("host-smoke", ("func",), reason="Unknown host recipe"))
    outcomes: list[Summary] = []
    selected = {name: path for name, path in cases.items() if not selection or name == selection}
    try:
        with azurite(directory), configured({"VERIFICATION_ISOLATED_RECIPES": "1"}):
            for name, path in selected.items():
                outcomes.append(pytest_lane("host-smoke/" + name, [path, "-m", "e2e", "--no-cov"]))
        return aggregate("host-smoke", outcomes)
    except KeyboardInterrupt:
        complete_cancelled("host-smoke", outcomes, list(selected))
        raise
    except (OSError, RuntimeError, TimeoutError) as error:
        return finish(directory, Summary("host-smoke", ("func",), reason=str(error)))


def verify() -> Summary:
    directory = Path("test-results/verify")
    fresh(directory)
    outcomes = []
    for target in (
        "check",
        "test",
        "recipe-tests",
        "bicep",
        "worker-registration",
        "integration",
        "build",
        "docs",
    ):
        path = Path("test-results") / target / "summary.json"
        path.unlink(missing_ok=True)
        try:
            code = run(["make", target], directory / f"logs/{target}.log", 3600)
        except KeyboardInterrupt:
            outcomes.append(Summary(target, ("make", target), exit_code=130, reason="Interrupted"))
            return aggregate("verify", outcomes)
        summary = (
            load(path)
            if path.exists()
            else Summary(
                target,
                ("make", target),
                reason="Required lane summary missing",
                exit_code=code or 2,
            )
        )
        if code and summary.status == "PASS":
            summary = replace(summary, status="FAIL", exit_code=code)
        outcomes.append(summary)
    return aggregate("verify", outcomes)


def offline() -> Summary:
    selection = [
        "tests",
        "--ignore=tests/test_bicep_compiles.py",
        "--deselect=tests/test_bicep_linux_plans.py::"
        "test_fixed_python_plan_site_templates_compile_without_bcp025",
        "--ignore=tests/e2e",
        "--cov-report=term-missing",
        "--cov-report=xml:test-results/test/coverage.xml",
    ]
    result = pytest_lane("test", selection)
    inventory = recipes(Path.cwd())
    path = Path("test-results/test/recipes.json")
    path.write_text(json.dumps([asdict(recipe) for recipe in inventory], indent=2))
    for family in sorted({r.family for r in inventory}):
        print(f"recipe inventory {family}: {sum(r.family == family for r in inventory)} selected")
    return result


def complete_cancelled(lane: str, outcomes: list[Summary], families: list[str]) -> None:
    completed = {summary.lane for summary in outcomes}
    for family in families:
        name = lane + "/" + family
        if name in completed:
            continue
        path = Path("test-results") / name / "summary.json"
        outcomes.append(
            load(path)
            if path.exists()
            else Summary(name, ("pytest",), reason="Required family not executed")
        )
    aggregate(lane, outcomes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lane",
        choices=(
            "test",
            "integration",
            "verify",
            "azure-e2e",
            "doctor",
            "report",
            "clean",
            "focused",
            "bicep",
            "worker-registration",
            "smoke",
            "record",
            "host-smoke",
        ),
    )
    args, extra = parser.parse_known_args()
    match args.lane:
        case "doctor":
            return doctor()
        case "report":
            return report(Path("test-results"))
        case "clean":
            clean(Path.cwd())
            return 0
        case "verify":
            return verify().exit_code
        case "integration":
            return integration().exit_code
        case "host-smoke":
            return host_smoke().exit_code
        case "test":
            if extra:
                return pytest_lane("test-focused", ["tests", *extra]).exit_code
            return offline().exit_code
        case "azure-e2e":
            return azure().exit_code
        case "bicep":
            return bicep().exit_code
        case "worker-registration":
            return pytest_lane(
                "worker-registration",
                [
                    "tests/test_worker_registration_guard.py",
                    "-m",
                    "worker_registration",
                    "--no-cov",
                ],
            ).exit_code
        case "smoke":
            return pytest_lane("smoke", ["tests/e2e", "-m", "smoke", "--no-cov", *extra]).exit_code
        case "focused":
            return task(extra[0], [sys.executable, *extra[1:]]).exit_code
        case "record":
            directory = Path("test-results") / extra[0]
            return finish(directory, collect(directory, ["pytest"], int(extra[1]))).exit_code
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
