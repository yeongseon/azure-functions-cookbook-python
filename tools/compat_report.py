"""Summarize the pre-merge toolkit compatibility run and fail closed on weak evidence.

Reads the JUnit XML written by ``pytest -m compat tests/e2e`` and the pinned dependency set in
``constraints-min.txt``, then writes ``report.json`` and ``report.md`` (tested commit, interpreter,
host tooling, declared versus installed versions, pass/fail/skip counts and skip reasons). The
exit status is non-zero when the run is not trustworthy evidence: no JUnit file, fewer selected
tests than ``--min-tests`` (a zero-selection run included), any failure or error, any skipped
test, or an installed version that differs from its pin.

Nothing here reads a secret. The report records local Core Tools host evidence only.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any
import xml.etree.ElementTree as ET  # noqa: S405 - parses the JUnit file this job just wrote


@dataclass
class Counts:
    tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    skip_reasons: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def parse_junit(path: Path) -> Counts:
    """Count outcomes in a JUnit XML file written by pytest."""
    counts = Counts()
    for case in ET.parse(path).getroot().iter("testcase"):  # noqa: S314 - own CI artifact
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        counts.tests += 1
        skipped = case.find("skipped")
        if skipped is not None:
            counts.skipped += 1
            counts.skip_reasons.append(f"{name}: {skipped.get('message', 'no reason given')}")
        elif case.find("failure") is not None:
            counts.failed += 1
            counts.failures.append(name)
        elif case.find("error") is not None:
            counts.errors += 1
            counts.failures.append(name)
        else:
            counts.passed += 1
    return counts


def parse_pins(path: Path) -> dict[str, str]:
    """Return ``{normalized name: version}`` from ``name==version`` lines."""
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        if not separator:
            raise ValueError(f"{path}: expected `name==version`, got `{raw}`")
        pins[_normalize(name)] = version.strip()
    return pins


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def installed_versions() -> dict[str, str]:
    return {
        _normalize(dist.metadata["Name"]): dist.version
        for dist in metadata.distributions()
        if dist.metadata["Name"]
    }


def compare_pins(pins: Mapping[str, str], installed: Mapping[str, str]) -> list[str]:
    """Describe every pin whose installed version is missing or different."""
    problems = []
    for name, wanted in sorted(pins.items()):
        have = installed.get(name)
        if have != wanted:
            problems.append(f"{name}: pinned {wanted}, installed {have or 'missing'}")
    return problems


def verdict(counts: Counts, min_tests: int, pin_problems: Sequence[str]) -> list[str]:
    """Reasons the run is not acceptable evidence (empty means it passed)."""
    reasons = []
    if counts.tests < min_tests:
        reasons.append(f"selected {counts.tests} test(s); at least {min_tests} required")
    if counts.failed or counts.errors:
        reasons.append(f"{counts.failed} failed and {counts.errors} errored")
    if counts.skipped:
        reasons.append(f"{counts.skipped} skipped; a skipped test is not evidence")
    reasons.extend(f"dependency drift: {problem}" for problem in pin_problems)
    return reasons


def _version_of(command: Sequence[str]) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        return "unavailable"
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [executable, *command[1:]], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    lines = (done.stdout or done.stderr).strip().splitlines()
    return lines[0] if lines else "unavailable"


def build_report(
    counts: Counts,
    pins: Mapping[str, str],
    installed: Mapping[str, str],
    reasons: Sequence[str],
    env: Mapping[str, str],
    tooling: Mapping[str, str],
) -> dict[str, Any]:
    toolkit = {name: version for name, version in installed.items() if name.startswith("azure-")}
    return {
        "result": "failed" if reasons else "passed",
        "reasons": list(reasons),
        "commit": {
            "tested": env.get("GITHUB_SHA", "unknown"),
            "pull_request_head": env.get("PR_HEAD_SHA") or None,
            "event": env.get("GITHUB_EVENT_NAME", "unknown"),
        },
        "counts": {
            "selected": counts.tests,
            "passed": counts.passed,
            "failed": counts.failed,
            "errors": counts.errors,
            "skipped": counts.skipped,
        },
        "failures": counts.failures,
        "skip_reasons": counts.skip_reasons,
        "tooling": dict(tooling),
        "declared_pins": dict(sorted(pins.items())),
        "installed_toolkit_packages": dict(sorted(toolkit.items())),
        "installed_all": dict(sorted(installed.items())),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        f"## Toolkit compatibility (pre-merge): {report['result']}",
        "",
        f"- Tested commit: `{report['commit']['tested']}` "
        f"(PR head `{report['commit']['pull_request_head']}`, event `{report['commit']['event']}`)",
        f"- Selected {counts['selected']}: passed {counts['passed']}, failed {counts['failed']}, "
        f"errors {counts['errors']}, skipped {counts['skipped']}",
    ]
    lines += [f"- Tooling {key}: `{value}`" for key, value in report["tooling"].items()]
    for reason in report["reasons"]:
        lines.append(f"- **Not acceptable:** {reason}")
    if report["skip_reasons"]:
        lines += ["", "Skipped tests and reasons:"] + [
            f"- {item}" for item in report["skip_reasons"]
        ]
    lines += ["", "| Package | Pinned (declared) | Installed |", "| --- | --- | --- |"]
    installed = report["installed_all"]
    lines += [
        f"| {name} | {version} | {installed.get(name, 'missing')} |"
        for name, version in report["declared_pins"].items()
    ]
    lines += [
        "",
        "Local Core Tools host evidence only; it does not exercise Azure deployments, identity or "
        "secrets. Scheduled/post-release `E2E Toolkit Matrix` remains the full toolkit matrix.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--constraints", type=Path, required=True)
    parser.add_argument("--min-tests", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    counts = Counts()
    reasons: list[str] = []
    if args.junit.is_file():
        counts = parse_junit(args.junit)
    else:
        reasons.append(f"no JUnit file at {args.junit}; the compatibility tests did not run")
    pins = parse_pins(args.constraints)
    installed = installed_versions()
    reasons += verdict(counts, args.min_tests, compare_pins(pins, installed))
    tooling = {
        "python": platform.python_version(),
        "core_tools": _version_of(["func", "--version"]),
    }
    report = build_report(counts, pins, installed, reasons, os.environ, tooling)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    (args.out / "report.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(markdown)
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
