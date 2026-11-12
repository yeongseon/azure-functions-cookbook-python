"""Read-only audit of the cookbook's tagged recipe snapshots.

This repository releases **versioned recipe/documentation snapshots** (a tag, a GitHub Release and
a ``CHANGELOG.md`` entry written by Release Please). It is *not* a PyPI package, so this audit never
looks at PyPI and never treats a GitHub Release as proof of distribution or of Azure certification.

For every ``vX.Y.Z`` tag it reports, deterministically and without touching the repository:

* ``tag-name``       the tag is plain semver (``vMAJOR.MINOR.PATCH``);
* ``ancestry``       the tag commit is reachable from the audited ref (normally ``origin/main``);
* ``duplicate-commit`` / ``tag-order``  tags map to distinct commits that follow version order;
* ``release-exists`` a published (non-draft) GitHub Release exists for the tag, and no Release
  exists without a tag (checked only when Release data is supplied);
* ``source-version`` / ``changelog-entry``  for tags cut by Release Please, the source
  ``__version__``, ``.release-please-manifest.json`` and ``CHANGELOG.md`` agree with the tag;
* ``recipe-inventory``  ``recipes.json`` at the tag (when present) parses and its size is reported;
* ``verification-level`` which CI definitions existed at the tag (informational, never a claim that
  a recipe was certified on Azure);
* ``head-version`` (checked-out HEAD, so a Release PR is validated before it is merged) the source
  ``__version__``, ``.release-please-manifest.json`` and the newest ``CHANGELOG.md`` entry agree;
* ``recipe-index`` (audited ref) ``scripts/gen_recipe_index.py --check`` and
  ``scripts/gen_recipe_table.py --check`` pass, i.e. the generated index has not drifted;
* ``pending-snapshot`` (informational) whether commits after the newest tag contain user-facing
  Conventional Commit types, i.e. whether a snapshot is expected.

Findings recorded in the exception registry (``.github/release-audit-exceptions.json``) are
reported as ``excepted`` and do not fail the run. An exception is pinned to the tag's commit SHA
and to specific checks, so a moved tag or a *new* kind of defect on the same tag is still reported.

Exit status: 0 = no unexcepted error, 1 = at least one unexcepted error, 2 = the audit itself could
not run (for example the Release data could not be fetched).
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

DEFAULT_SLUG = "yeongseon/azure-functions-cookbook-python"
DEFAULT_EXCEPTIONS = Path(".github/release-audit-exceptions.json")
VERSION_FILE = "src/azure_functions_python_cookbook/__init__.py"
MANIFEST_FILE = ".release-please-manifest.json"
USER_FACING_TYPES = frozenset({"feat", "fix", "perf", "revert"})

CHECKS = frozenset(
    {
        "tag-name",
        "ancestry",
        "duplicate-commit",
        "tag-order",
        "release-exists",
        "release-draft",
        "release-orphan",
        "source-version",
        "changelog-entry",
        "recipe-inventory",
        "recipe-index",
        "head-version",
    }
)

_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_VERSION_RE = re.compile(r"""^__version__\s*=\s*["']([^"']+)["']""", re.MULTILINE)
_CC_RE = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<bang>!)?:")

# Workflow file -> what its presence at a tag says about the checks defined at that time.
_LEVELS: tuple[tuple[str, str], ...] = (
    (".github/workflows/ci-test.yml", "static/unit/generated-artifact checks defined"),
    (".github/workflows/ci-smoke.yml", "recipe import/smoke checks defined"),
    (".github/workflows/e2e-toolkit.yml", "local Functions-host/Azurite integration defined"),
    (".github/workflows/tag-verification.yml", "tag metadata/clean-install gate defined"),
)


class AuditError(RuntimeError):
    """The audit could not be completed (as opposed to completing with findings)."""


@dataclass(frozen=True)
class Finding:
    tag: str
    check: str
    severity: str  # "error" | "info"
    message: str
    link: str = ""
    status: str = ""  # "" | "excepted"
    reason: str = ""


@dataclass(frozen=True)
class ExceptionEntry:
    tag: str
    commit: str
    checks: tuple[str, ...]
    classification: str
    reason: str
    evidence: tuple[str, ...]
    issue: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    tags: list[tuple[str, str]] = field(default_factory=list)  # (tag, commit)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error" and f.status != "excepted"]


def _git(repo: Path, *args: str, check: bool = True) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        if check:
            raise AuditError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return None
    return result.stdout


def _show(repo: Path, rev: str, path: str) -> str | None:
    return _git(repo, "show", f"{rev}:{path}", check=False)


def _tag_key(tag: str) -> tuple[int, int, int]:
    match = _TAG_RE.match(tag)
    assert match is not None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def load_exceptions(path: Path) -> list[ExceptionEntry]:
    """Parse and validate the exception registry; a missing file means no exceptions."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_entries = data["exceptions"]
        entries = [_parse_exception(raw) for raw in raw_entries]
    except (ValueError, KeyError, TypeError) as exc:
        raise AuditError(f"invalid exception registry {path}: {exc}") from exc
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        for check in entry.checks:
            if (entry.tag, check) in seen:
                raise AuditError(f"duplicate exception for {entry.tag} / {check} in {path}")
            seen.add((entry.tag, check))
    return entries


def _parse_exception(raw: dict[str, Any]) -> ExceptionEntry:
    tag, commit = raw["tag"], raw["commit"]
    if not isinstance(tag, str) or not _TAG_RE.match(tag):
        raise ValueError(f"bad tag {tag!r}")
    if not isinstance(commit, str) or not _SHA_RE.match(commit):
        raise ValueError(f"{tag}: commit must be a full 40-hex SHA")
    checks = raw["checks"]
    if not isinstance(checks, list) or not checks:
        raise ValueError(f"{tag}: checks must be a non-empty list")
    unknown = sorted(set(checks) - CHECKS)
    if unknown:
        raise ValueError(f"{tag}: unknown checks {unknown}")
    for key in ("classification", "reason", "issue"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ValueError(f"{tag}: {key} must be a non-empty string")
    evidence = raw["evidence"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(isinstance(e, str) for e in evidence)
    ):
        raise ValueError(f"{tag}: evidence must be a non-empty list of strings")
    return ExceptionEntry(
        tag=tag,
        commit=commit,
        checks=tuple(checks),
        classification=raw["classification"],
        reason=raw["reason"],
        evidence=tuple(evidence),
        issue=raw["issue"],
    )


def load_releases(path: Path) -> list[dict[str, Any]]:
    """Load Release data from a JSON file (``gh release list --json ...`` shape)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AuditError(f"cannot read releases file {path}: {exc}") from exc
    if not isinstance(data, list):
        raise AuditError(f"releases file {path} must contain a JSON array")
    return data


def fetch_releases(slug: str) -> list[dict[str, Any]]:
    """Fetch GitHub Release metadata read-only through the GitHub CLI."""
    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "list",
                "--repo",
                slug,
                "--limit",
                "1000",
                "--json",
                "tagName,isDraft,isPrerelease",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise AuditError(f"cannot run gh to list releases: {exc}") from exc
    if result.returncode != 0:
        raise AuditError(f"gh release list failed: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    return data


def _links(slug: str, tag: str, commit: str, previous: str | None) -> str:
    base = f"https://github.com/{slug}"
    parts = [f"tag {base}/releases/tag/{tag}", f"commit {base}/commit/{commit}"]
    if previous:
        parts.append(f"compare {base}/compare/{previous}...{tag}")
    return "; ".join(parts)


def audit(
    repo: Path,
    *,
    ref: str,
    slug: str,
    releases: Sequence[dict[str, Any]] | None,
    exceptions: Sequence[ExceptionEntry],
    run_generated_checks: bool = True,
) -> Report:
    """Run every check and return a deterministic :class:`Report` (no repository writes)."""
    report = Report()
    if _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False) is None:
        raise AuditError(f"ref {ref!r} not found; fetch it (and tags) before auditing")
    raw_tags = (_git(repo, "tag", "--list", "v*") or "").split()
    semver_tags = sorted((t for t in raw_tags if _TAG_RE.match(t)), key=_tag_key)
    findings = report.findings

    for tag in sorted(set(raw_tags) - set(semver_tags)):
        findings.append(
            Finding(tag, "tag-name", "error", "tag is not plain vMAJOR.MINOR.PATCH semver")
        )

    commits: dict[str, str] = {}
    for tag in semver_tags:
        out = _git(repo, "rev-parse", f"{tag}^{{commit}}", check=False)
        commits[tag] = (out or "").strip()
        report.tags.append((tag, commits[tag]))

    release_by_tag = {r["tagName"]: r for r in releases} if releases is not None else None

    previous: str | None = None
    for tag in semver_tags:
        commit = commits[tag]
        link = _links(slug, tag, commit, previous)
        if _git(repo, "merge-base", "--is-ancestor", commit, ref, check=False) is None:
            findings.append(
                Finding(tag, "ancestry", "error", f"tag commit is not reachable from {ref}", link)
            )
        _check_neighbours(repo, findings, semver_tags, commits, tag, link)
        if release_by_tag is not None:
            _check_release(findings, release_by_tag.get(tag), tag, link)
        _check_source(repo, findings, tag, commit, link)
        _check_inventory(repo, findings, tag, commit, link)
        previous = tag

    if release_by_tag is not None:
        for tag in sorted(set(release_by_tag) - set(semver_tags) - set(raw_tags)):
            findings.append(
                Finding(tag, "release-orphan", "error", "GitHub Release has no matching tag")
            )
    else:
        report.notes.append("GitHub Release existence was not checked (no Release data supplied).")

    for tag in semver_tags:
        findings.append(_verification_finding(repo, tag, commits[tag]))

    _check_head_version(repo, findings)
    if run_generated_checks:
        _check_generated(repo, findings)
    _pending_snapshot(repo, report, ref, semver_tags[-1] if semver_tags else None)
    report.notes.append(
        "Verification levels list the CI definitions present at each tag. They do not show "
        "that every run passed, and no recipe is claimed to be certified on Azure."
    )
    skipped: set[str] = set()
    if releases is None:
        skipped |= {"release-exists", "release-draft", "release-orphan"}
    if not run_generated_checks:
        skipped.add("recipe-index")
    _apply_exceptions(report, exceptions, commits, skipped)
    previous = None
    link_for: dict[str, str] = {}
    for tag in semver_tags:
        link_for[tag] = _links(slug, tag, commits[tag], previous)
        previous = tag
    report.findings = sorted(
        (replace(f, link=link_for.get(f.tag, f.link)) for f in report.findings),
        key=lambda f: (_sort_tag(f.tag), f.check, f.message),
    )
    return report


def _sort_tag(tag: str) -> tuple[int, tuple[int, int, int], str]:
    return (0, _tag_key(tag), tag) if _TAG_RE.match(tag) else (1, (0, 0, 0), tag)


def _check_neighbours(
    repo: Path,
    findings: list[Finding],
    tags: Sequence[str],
    commits: dict[str, str],
    tag: str,
    link: str,
) -> None:
    index = tags.index(tag)
    if index + 1 >= len(tags):
        return
    nxt = tags[index + 1]
    this_commit, next_commit = commits[tag], commits[nxt]
    if this_commit == next_commit:
        findings.append(
            Finding(
                nxt,
                "duplicate-commit",
                "error",
                f"{nxt} and {tag} resolve to the same commit {this_commit[:12]}",
                link,
            )
        )
    elif _git(repo, "merge-base", "--is-ancestor", this_commit, next_commit, check=False) is None:
        relation = (
            f"{tag}'s commit descends from {nxt}'s commit"
            if _git(repo, "merge-base", "--is-ancestor", next_commit, this_commit, check=False)
            is not None
            else f"{tag} and {nxt} are on diverging histories"
        )
        findings.append(
            Finding(tag, "tag-order", "error", f"tags are out of version order: {relation}", link)
        )


def _check_release(
    findings: list[Finding], release: dict[str, Any] | None, tag: str, link: str
) -> None:
    if release is None:
        findings.append(
            Finding(tag, "release-exists", "error", "tag has no GitHub Release entry", link)
        )
    elif release.get("isDraft"):
        findings.append(
            Finding(
                tag, "release-draft", "error", "GitHub Release exists but is still a draft", link
            )
        )


def _check_source(repo: Path, findings: list[Finding], tag: str, commit: str, link: str) -> None:
    version = tag[1:]
    source = _show(repo, commit, VERSION_FILE)
    if source is not None:
        match = _VERSION_RE.search(source)
        if match is None or match.group(1) != version:
            found = match.group(1) if match else "none"
            findings.append(
                Finding(
                    tag,
                    "source-version",
                    "error",
                    f"{VERSION_FILE} __version__ is {found}, expected {version}",
                    link,
                )
            )
    manifest_text = _show(repo, commit, MANIFEST_FILE)
    if manifest_text is None:
        return  # Not cut by Release Please: manifest and CHANGELOG checks do not apply.
    try:
        manifest = json.loads(manifest_text).get(".")
    except (ValueError, AttributeError):
        manifest = None
    if manifest != version:
        findings.append(
            Finding(
                tag,
                "source-version",
                "error",
                f"{MANIFEST_FILE} records {manifest!r}, expected {version}",
                link,
            )
        )
    changelog = _show(repo, commit, "CHANGELOG.md") or ""
    if not re.search(rf"^## \[{re.escape(version)}\]", changelog, re.MULTILINE):
        findings.append(
            Finding(tag, "changelog-entry", "error", f"CHANGELOG.md has no {version} entry", link)
        )


def _check_head_version(repo: Path, findings: list[Finding]) -> None:
    """Verify HEAD's version sources agree (this is what a Release PR changes)."""
    manifest_text = _show(repo, "HEAD", MANIFEST_FILE)
    if manifest_text is None:
        return
    try:
        manifest = str(json.loads(manifest_text).get("."))
    except (ValueError, AttributeError):
        manifest = "unparseable"
    match = _VERSION_RE.search(_show(repo, "HEAD", VERSION_FILE) or "")
    source = match.group(1) if match else "none"
    if source != manifest:
        findings.append(
            Finding(
                "HEAD",
                "head-version",
                "error",
                f"{VERSION_FILE} declares {source} but {MANIFEST_FILE} records {manifest}",
            )
        )
    changelog = _show(repo, "HEAD", "CHANGELOG.md") or ""
    first = re.search(r"^## \[([^\]]+)\]", changelog, re.MULTILINE)
    if first is None or first.group(1) != manifest:
        newest = first.group(1) if first else "none"
        findings.append(
            Finding(
                "HEAD",
                "head-version",
                "error",
                f"newest CHANGELOG.md entry is {newest}, expected {manifest}",
            )
        )


def _check_inventory(repo: Path, findings: list[Finding], tag: str, commit: str, link: str) -> None:
    text = _show(repo, commit, "recipes.json")
    if text is None:
        return
    try:
        recipes = json.loads(text)
        count = len(recipes)
        slugs = [r["slug"] for r in recipes]
    except (ValueError, TypeError, KeyError):
        findings.append(
            Finding(
                tag, "recipe-inventory", "error", "recipes.json is not a valid recipe list", link
            )
        )
        return
    if len(set(slugs)) != count:
        findings.append(
            Finding(tag, "recipe-inventory", "error", "recipes.json has duplicate slugs", link)
        )
    else:
        findings.append(
            Finding(tag, "recipe-inventory", "info", f"recipes.json lists {count} recipes", link)
        )


def _verification_finding(repo: Path, tag: str, commit: str) -> Finding:
    levels = [label for path, label in _LEVELS if _show(repo, commit, path) is not None]
    text = "; ".join(levels) if levels else "no CI workflow definitions found at this tag"
    return Finding(tag, "verification-level", "info", text)


def _check_generated(repo: Path, findings: list[Finding]) -> None:
    for script in ("scripts/gen_recipe_index.py", "scripts/gen_recipe_table.py"):
        path = repo / script
        if not path.exists():
            continue
        result = subprocess.run(
            [sys.executable, str(path), "--check"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()
            findings.append(
                Finding(
                    "HEAD",
                    "recipe-index",
                    "error",
                    f"{script} --check failed: {detail[-1] if detail else 'no output'}",
                )
            )


def _pending_snapshot(repo: Path, report: Report, ref: str, latest: str | None) -> None:
    if latest is None:
        return
    out = _git(repo, "log", "--format=%s%x1f%b%x1e", f"{latest}..{ref}", check=False) or ""
    user_facing: list[str] = []
    total = 0
    for chunk in filter(None, (c.strip("\n") for c in out.split("\x1e"))):
        subject, _, body = chunk.partition("\x1f")
        total += 1
        match = _CC_RE.match(subject)
        breaking = bool(match and match.group("bang")) or "BREAKING CHANGE:" in body
        if breaking or (match and match.group("type") in USER_FACING_TYPES):
            user_facing.append(subject)
    if not total:
        report.notes.append(f"No commits since {latest}: no snapshot pending.")
    elif user_facing:
        report.notes.append(
            f"{len(user_facing)} user-facing commit(s) since {latest}: a snapshot is expected "
            "(Release Please owns the Release PR)."
        )
    else:
        report.notes.append(
            f"{total} commit(s) since {latest}, none user-facing (docs/ci/chore/test/...): "
            "no snapshot is needed."
        )


def _apply_exceptions(
    report: Report,
    exceptions: Sequence[ExceptionEntry],
    commits: dict[str, str],
    skipped: set[str],
) -> None:
    by_key = {(e.tag, c): e for e in exceptions for c in e.checks}
    used: set[tuple[str, str]] = set()
    result: list[Finding] = []
    for finding in report.findings:
        entry = by_key.get((finding.tag, finding.check))
        if finding.severity != "error" or entry is None:
            result.append(finding)
        elif entry.commit != commits.get(finding.tag):
            actual = commits.get(finding.tag, "")[:12]
            result.append(
                Finding(
                    finding.tag,
                    finding.check,
                    "error",
                    f"{finding.message} (exception pinned to {entry.commit[:12]} but the tag now "
                    f"resolves to {actual or 'nothing'}; exception void)",
                    finding.link,
                )
            )
        else:
            used.add((finding.tag, finding.check))
            result.append(
                Finding(
                    finding.tag,
                    finding.check,
                    "error",
                    finding.message,
                    finding.link,
                    status="excepted",
                    reason=f"{entry.classification}: {entry.reason} ({entry.issue})",
                )
            )
    report.findings = result
    for (tag, check), entry in sorted(
        by_key.items(), key=lambda kv: (_sort_tag(kv[0][0]), kv[0][1])
    ):
        if (tag, check) not in used and check not in skipped:
            report.notes.append(
                f"stale exception: {tag} / {check} no longer matches a finding "
                f"({entry.issue}); remove it from the registry."
            )


def render_text(report: Report, *, markdown: bool = False) -> str:
    lines: list[str] = []
    lines.append(
        f"Audited {len(report.tags)} snapshot tag(s); {len(report.failures)} unexcepted failure(s)."
    )
    for tag, commit in report.tags:
        lines.append(f"- {tag} -> {commit[:12]}")
    lines.append("")
    for f in report.findings:
        label = "EXCEPTED" if f.status == "excepted" else f.severity.upper()
        lines.append(f"[{label}] {f.tag} {f.check}: {f.message}")
        if f.reason:
            lines.append(f"    exception: {f.reason}")
        if f.link and (f.severity == "error"):
            lines.append(f"    source: {f.link}")
    lines.append("")
    lines += [f"note: {n}" for n in report.notes]
    lines.append("RESULT: " + ("FAIL" if report.failures else "PASS"))
    body = "\n".join(lines) + "\n"
    if markdown:
        return "## Cookbook snapshot audit\n\n```text\n" + body + "```\n"
    return body


def render_json(report: Report) -> str:
    payload = {
        "tags": [{"tag": t, "commit": c} for t, c in report.tags],
        "findings": [
            {
                "tag": f.tag,
                "check": f.check,
                "severity": f.severity,
                "message": f.message,
                "status": f.status or "open",
                "reason": f.reason,
                "link": f.link,
            }
            for f in report.findings
        ],
        "notes": report.notes,
        "result": "fail" if report.failures else "pass",
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of cookbook snapshot tags.")
    parser.add_argument("--repo", type=Path, default=Path("."), help="repository to audit")
    parser.add_argument("--ref", default="origin/main", help="ref the tags must be reachable from")
    parser.add_argument("--slug", default=DEFAULT_SLUG, help="GitHub owner/name for source links")
    parser.add_argument("--exceptions", type=Path, default=None, help="exception registry JSON")
    parser.add_argument("--releases-json", type=Path, help="Release data instead of querying gh")
    parser.add_argument(
        "--skip-releases", action="store_true", help="do not check GitHub Release existence"
    )
    parser.add_argument("--skip-generated", action="store_true", help="skip recipe index checks")
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        registry = args.exceptions or (args.repo / DEFAULT_EXCEPTIONS)
        exceptions = load_exceptions(registry)
        releases: list[dict[str, Any]] | None
        if args.skip_releases:
            releases = None
        elif args.releases_json:
            releases = load_releases(args.releases_json)
        else:
            releases = fetch_releases(args.slug)
        report = audit(
            args.repo,
            ref=args.ref,
            slug=args.slug,
            releases=releases,
            exceptions=exceptions,
            run_generated_checks=not args.skip_generated,
        )
    except AuditError as exc:
        print(f"audit could not run: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(
        render_json(report)
        if args.format == "json"
        else render_text(report, markdown=args.format == "markdown")
    )
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
