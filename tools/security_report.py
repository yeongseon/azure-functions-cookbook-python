"""Redacted evidence contracts adapted from the reviewed sibling security tooling."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import json
import os
from pathlib import Path
import re
from typing import TypeAlias, assert_never

JSON: TypeAlias = "None | bool | int | float | str | list[JSON] | dict[str, JSON]"


class EvidenceError(ValueError):
    """Malformed scanner output; never includes raw external data."""


def mapping(value: JSON) -> dict[str, JSON]:
    if not isinstance(value, dict):
        raise EvidenceError("expected object")
    return value


def sequence(value: JSON) -> list[JSON]:
    if not isinstance(value, list):
        raise EvidenceError("expected array")
    return value


def text(value: JSON) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError("expected nonempty text")
    return value


def integer(value: JSON) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceError("expected nonnegative integer")
    return value


def load(raw: str) -> dict[str, JSON]:
    parsed: JSON = json.loads(raw)
    return mapping(parsed)


def identifier(value: JSON) -> str:
    candidate = text(value)
    if not re.fullmatch(r"[A-Za-z0-9_.:/@+{}-]{1,240}", candidate):
        raise EvidenceError("unsafe identifier")
    if candidate.startswith(("/", "http:", "https:")) or ".." in candidate:
        raise EvidenceError("unsafe path")
    return candidate


class Status(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    TOOL_ERROR = "TOOL_ERROR"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True, slots=True)
class Finding:
    id: str
    file: str = ""
    line: int = 0
    severity: str = "UNKNOWN"
    package: str = ""


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: Status
    counts: dict[str, int] = field(default_factory=dict)
    findings: tuple[Finding, ...] = ()
    inventory: tuple[str, ...] = ()
    exceptions: tuple[str, ...] = ()
    message: str = ""

    @property
    def returncode(self) -> int:
        match self.status:
            case Status.PASS:
                return 0
            case Status.FAIL:
                return 1
            case Status.TOOL_ERROR:
                return 2
            case Status.INCOMPLETE:
                return 3
            case unreachable:
                assert_never(unreachable)


def write_report(checks: list[Check], output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps({"schema_version": 1, "checks": [asdict(c) for c in checks]}, indent=2) + "\n"
    )
    lines = [
        "## Recipe security evidence",
        "",
        "| Check | Outcome | Counts |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {json.dumps(check.counts)} |")
        print(f"{check.name}: {check.status} {json.dumps(check.counts)} {check.message}")
    summary = "\n".join(lines) + "\n"
    (output / "summary.md").write_text(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
            stream.write(summary)
    return max((check.returncode for check in checks), default=3)
