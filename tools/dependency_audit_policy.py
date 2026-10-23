"""Audit resolved root runtime and generated recipe requirements without dev contamination."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

from tools.recipe_security import ROOT
from tools.security_exceptions import apply_policy
from tools.security_report import (
    Check,
    EvidenceError,
    Finding,
    Status,
    identifier,
    load,
    mapping,
    sequence,
    text,
    write_report,
)


def classify_audit(raw: str, code: int, *, empty_allowed: bool = False) -> Check:
    try:
        data = load(raw)
        dependencies = sequence(data["dependencies"])
        findings: list[Finding] = []
        packages: list[str] = []
        skipped = False
        for entry in dependencies:
            item = mapping(entry)
            packages.append(identifier(item["name"]))
            if "skip_reason" in item:
                skipped = True
                continue
            text(item["version"])
            for advisory in sequence(item["vulns"]):
                vuln = mapping(advisory)
                findings.append(
                    Finding(
                        identifier(vuln["id"]), severity="UNKNOWN", package=identifier(item["name"])
                    )
                )
        status = Status.FAIL if findings else Status.PASS
        if code not in {0, 1} or bool(findings) != (code == 1):
            status = Status.TOOL_ERROR
        elif skipped or (not dependencies and not empty_allowed):
            status = Status.INCOMPLETE
        return Check(
            "dependency-audit",
            status,
            {"packages": len(packages), "findings": len(findings)},
            tuple(findings),
            tuple(sorted(packages)),
        )
    except (ValueError, KeyError, TypeError):
        return Check(
            "dependency-audit", Status.TOOL_ERROR, message="Invalid audit output discarded"
        )


def requirement_scopes(root: Path) -> dict[str, tuple[str, ...]]:
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    scopes = {"root-runtime": tuple(metadata["project"]["dependencies"])}
    from tools.recipe_discovery import recipe_files

    entries = recipe_files(root / "examples", "function_app.py")
    if not entries:
        raise EvidenceError("no runnable requirements discovered")
    for entry in entries:
        if any(part.startswith(".") for part in entry.relative_to(root).parts):
            continue
        project = entry.parent
        data = tomllib.loads((project / "pyproject.toml").read_text())
        dependencies = tuple(sorted(data["project"]["dependencies"], key=str.casefold))
        rendered = "".join(f"{dependency}\n" for dependency in dependencies)
        if (project / "requirements.txt").read_text() != rendered:
            raise EvidenceError("generated requirements drift")
        scopes[project.relative_to(root).as_posix()] = dependencies
    return scopes


def audit_scopes(root: Path, scratch: Path) -> list[Check]:
    checks: list[Check] = []
    try:
        scopes = requirement_scopes(root)
    except (OSError, ValueError, KeyError, TypeError):
        return [
            Check(
                "dependency-inventory",
                Status.INCOMPLETE,
                message="Root or generated example requirements missing/stale",
            )
        ]
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cookbook-audit-", dir=scratch) as temporary:
        directory = Path(temporary)
        auditor = directory / "auditor"
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(auditor)],
                check=True,
                capture_output=True,
                timeout=90,
            )
            python = str(auditor / "bin/python")
            subprocess.run(
                [python, "-m", "pip", "install", "pip-audit==2.10.1"],
                check=True,
                capture_output=True,
                timeout=180,
            )
        except (OSError, subprocess.SubprocessError):
            return [
                Check(
                    "dependency-auditor",
                    Status.TOOL_ERROR,
                    message="Isolated pip-audit installation failed",
                )
            ]
        cache: dict[tuple[str, ...], Check] = {}
        for name, dependencies in scopes.items():
            if dependencies in cache:
                checks.append(replace(cache[dependencies], name=name))
                continue
            requirements = directory / "requirements.txt"
            requirements.write_text("\n".join(dependencies) + "\n")
            try:
                if not dependencies:
                    result = Check(
                        name,
                        Status.PASS,
                        {"packages": 0, "findings": 0},
                        message="Verified root project declares zero runtime dependencies",
                    )
                else:
                    process = subprocess.run(
                        [
                            python,
                            "-m",
                            "pip_audit",
                            "-r",
                            str(requirements),
                            "--format",
                            "json",
                            "--desc",
                            "off",
                            "--progress-spinner",
                            "off",
                            "--timeout",
                            "30",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=360,
                    )
                    result = replace(classify_audit(process.stdout, process.returncode), name=name)
                result = apply_policy(result, root / "security/dependency-exceptions.json")
            except (OSError, subprocess.TimeoutExpired):
                result = Check(
                    name, Status.TOOL_ERROR, message="Dependency resolution/audit failed"
                )
            cache[dependencies] = result
            checks.append(result)
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reporting", action="store_true")
    parser.add_argument("--scratch", type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument("--output", type=Path, default=ROOT / "security-results/dependencies")
    args = parser.parse_args()
    status = write_report(audit_scopes(ROOT, args.scratch), args.output)
    return 0 if args.reporting else status


if __name__ == "__main__":
    raise SystemExit(main())
