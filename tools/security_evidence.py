"""Run exact-inventory Bandit and redact scanner evidence before persistence."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tokenize

from tools.recipe_security import ROOT, check_manifest
from tools.security_exceptions import apply_policy
from tools.security_report import (
    Check,
    Finding,
    Status,
    identifier,
    integer,
    load,
    mapping,
    sequence,
    text,
    write_report,
)
from tools.security_structure import check_structure, source_files


def classify_bandit(raw: str, code: int, expected: set[str]) -> Check:
    try:
        data = load(raw)
        metrics = mapping(data["metrics"])
        scanned = {name.removeprefix("./") for name in metrics if name != "_totals"}
        findings: list[Finding] = []
        for entry in sequence(data["results"]):
            item = mapping(entry)
            severity = text(item["issue_severity"])
            if severity not in {"LOW", "MEDIUM", "HIGH", "UNDEFINED"}:
                raise ValueError("invalid severity")
            findings.append(
                Finding(
                    identifier(item["test_id"]),
                    identifier(text(item["filename"]).removeprefix("./")),
                    integer(item["line_number"]),
                    severity,
                )
            )
        status = Status.FAIL if findings else Status.PASS
        if code not in {0, 1} or sequence(data["errors"]) or bool(findings) != (code == 1):
            status = Status.TOOL_ERROR
        elif not expected or scanned != expected or not integer(mapping(metrics["_totals"])["loc"]):
            status = Status.INCOMPLETE
        return Check(
            "bandit",
            status,
            {"expected": len(expected), "scanned": len(scanned), "findings": len(findings)},
            tuple(findings),
            tuple(sorted(scanned)),
        )
    except (ValueError, KeyError, TypeError):
        return Check("bandit", Status.TOOL_ERROR, message="Invalid scanner output discarded")


def run_bandit(root: Path) -> Check:
    paths = {
        path
        for path in source_files(root / "examples", ".py")
        if "tests" not in path.relative_to(root).parts
    }
    paths.update(source_files(root / "scripts", ".py"))
    paths.update(source_files(root / "tools", ".py"))
    expected = {path.relative_to(root).as_posix() for path in paths}
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                *sorted(expected),
                "-q",
                "-f",
                "json",
                "--ignore-nosec",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=240,
        )
        check = apply_policy(
            classify_bandit(process.stdout, process.returncode, expected),
            root / "security/bandit-exceptions.json",
        )
        suppressions: list[Finding] = []
        for path in paths:
            with tokenize.open(path) as stream:
                for token in tokenize.generate_tokens(stream.readline):
                    if token.type == tokenize.COMMENT and "nosec" in token.string:
                        suppressions.append(
                            Finding(
                                "INLINE_NOSEC", path.relative_to(root).as_posix(), token.start[0]
                            )
                        )
        if suppressions:
            suppression_check = apply_policy(
                Check("suppressions", Status.FAIL, findings=tuple(suppressions)),
                root / "security/bandit-exceptions.json",
            )
            if suppression_check.status != Status.PASS:
                check = replace(
                    check, status=Status.INCOMPLETE, findings=check.findings + tuple(suppressions)
                )
        return check
    except (OSError, ValueError, subprocess.TimeoutExpired, tokenize.TokenError):
        return Check("bandit", Status.TOOL_ERROR, message="Bandit execution failed")


def semgrep_evidence(outcome: str) -> Check:
    return Check(
        "semgrep-action",
        Status.TOOL_ERROR if outcome == "failure" else Status.INCOMPLETE,
        message="Pinned action outcome only; exact analyzed inventory unavailable",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("all", "semgrep"))
    parser.add_argument("--outcome", default="")
    parser.add_argument("--output", type=Path, default=ROOT / "security-results/static")
    args = parser.parse_args()
    checks = (
        [semgrep_evidence(args.outcome)]
        if args.check == "semgrep"
        else [check_manifest(ROOT), run_bandit(ROOT), check_structure(ROOT)]
    )
    return write_report(checks, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
