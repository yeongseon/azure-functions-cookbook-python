"""Exact, owned exceptions with a maximum ninety-day validity window."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path

from tools.security_report import (
    Check,
    EvidenceError,
    Finding,
    Status,
    identifier,
    integer,
    load,
    mapping,
    sequence,
    text,
)


@dataclass(frozen=True, slots=True)
class ExceptionRule:
    id: str
    package: str
    file: str
    line: int

    def matches(self, finding: Finding) -> bool:
        return (self.id, self.package, self.file, self.line) == (
            finding.id,
            finding.package,
            finding.file,
            finding.line,
        )


def read_rules(path: Path, today: date) -> tuple[ExceptionRule, ...]:
    policy = load(path.read_text())
    if policy["schema_version"] != 1:
        raise EvidenceError("unsupported policy")
    rules: list[ExceptionRule] = []
    for entry in sequence(policy["exceptions"]):
        item = mapping(entry)
        text(item["reason"])
        text(item["owner"])
        added = date.fromisoformat(text(item["added"]))
        expires = date.fromisoformat(text(item["expires"]))
        if not 0 < (expires - added).days <= 90 or not added <= today <= expires:
            raise EvidenceError("expired or invalid exception")
        rule = ExceptionRule(
            identifier(item["id"]),
            identifier(item["package"]) if "package" in item else "",
            identifier(item["file"]) if "file" in item else "",
            integer(item.get("line", 0)),
        )
        if rule in rules or bool(rule.package) == bool(rule.file):
            raise EvidenceError("duplicate or inexact exception")
        if rule.file and not rule.line:
            raise EvidenceError("static exception requires line")
        rules.append(rule)
    return tuple(rules)


def apply_policy(check: Check, path: Path) -> Check:
    try:
        rules = read_rules(path, datetime.now(UTC).date())
    except (OSError, ValueError, KeyError, TypeError):
        return replace(check, status=Status.TOOL_ERROR, message="Invalid exception policy")
    if check.status not in {Status.PASS, Status.FAIL}:
        return check
    applied = tuple(
        f"{finding.id}:{finding.package or finding.file}:{finding.line}"
        for finding in check.findings
        if any(rule.matches(finding) for rule in rules)
    )
    blocking = len(check.findings) - len(applied)
    return replace(
        check,
        status=Status.FAIL if blocking else Status.PASS,
        counts={**check.counts, "blocking": blocking},
        exceptions=applied,
    )
