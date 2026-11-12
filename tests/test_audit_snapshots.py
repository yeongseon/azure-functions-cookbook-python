"""Tests for the read-only cookbook snapshot audit (``tools/audit_snapshots.py``)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest

from tools import audit_snapshots as audit_mod
from tools.audit_snapshots import (
    AuditError,
    ExceptionEntry,
    Finding,
    audit,
    fetch_releases,
    load_exceptions,
    load_releases,
    main,
    render_json,
    render_text,
)

SLUG = "owner/repo"


def git(repo: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        "PATH": os.environ["PATH"],
        "HOME": str(repo),
    }
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot_files(repo: Path, version: str, *, changelog: bool = True) -> None:
    """Write the files Release Please keeps in sync for ``version``."""
    write(repo, "src/azure_functions_python_cookbook/__init__.py", f'__version__ = "{version}"\n')
    write(repo, ".release-please-manifest.json", json.dumps({".": version}))
    entry = f"## [{version}](https://example.test) (2026-01-01)\n" if changelog else ""
    write(repo, "CHANGELOG.md", f"# Changelog\n\n{entry}")
    write(repo, "recipes.json", json.dumps([{"slug": "a"}, {"slug": "b"}]))
    write(repo, ".github/workflows/ci-test.yml", "name: t\n")


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    return root


def released(*tags: str, draft: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    return [{"tagName": t, "isDraft": t in draft, "isPrerelease": False} for t in tags]


def run(repo: Path, releases: list[dict[str, Any]] | None, **kwargs: Any) -> Any:
    kwargs.setdefault("exceptions", [])
    kwargs.setdefault("run_generated_checks", False)
    return audit(repo, ref="main", slug=SLUG, releases=releases, **kwargs)


def checks(report: Any) -> set[tuple[str, str]]:
    return {(f.tag, f.check) for f in report.failures}


def make_valid(repo: Path) -> str:
    snapshot_files(repo, "0.5.0")
    sha = commit(repo, "chore(main): release 0.5.0")
    git(repo, "tag", "v0.5.0")
    return sha


def test_valid_snapshot_passes_with_links_and_levels(repo: Path) -> None:
    sha = make_valid(repo)
    report = run(repo, released("v0.5.0"))
    assert report.failures == []
    assert report.tags == [("v0.5.0", sha)]
    infos = {f.check: f.message for f in report.findings if f.severity == "info"}
    assert infos["recipe-inventory"] == "recipes.json lists 2 recipes"
    assert "static/unit/generated-artifact checks defined" in infos["verification-level"]
    text = render_text(report)
    assert "RESULT: PASS" in text
    assert "no recipe is claimed to be certified on Azure" in "\n".join(report.notes)
    assert "PyPI" not in text


def test_output_is_deterministic(repo: Path) -> None:
    make_valid(repo)
    first = render_text(run(repo, released("v0.5.0")))
    second = render_text(run(repo, released("v0.5.0")))
    assert first == second
    assert render_json(run(repo, released("v0.5.0"))) == render_json(run(repo, released("v0.5.0")))


def test_tag_without_release_fails_with_source_links(repo: Path) -> None:
    sha = make_valid(repo)
    report = run(repo, [])
    assert checks(report) == {("v0.5.0", "release-exists")}
    finding = report.failures[0]
    assert f"https://github.com/{SLUG}/releases/tag/v0.5.0" in finding.link
    assert f"https://github.com/{SLUG}/commit/{sha}" in finding.link
    assert "RESULT: FAIL" in render_text(report)


def test_draft_release_and_orphan_release_fail(repo: Path) -> None:
    make_valid(repo)
    report = run(repo, released("v0.5.0", "v9.9.9", draft=("v0.5.0",)))
    assert checks(report) == {("v0.5.0", "release-draft"), ("v9.9.9", "release-orphan")}


def test_release_check_can_be_skipped_and_is_reported(repo: Path) -> None:
    make_valid(repo)
    report = run(repo, None)
    assert report.failures == []
    assert any("not checked" in note for note in report.notes)


def exception_for(tag: str, sha: str, *check: str) -> ExceptionEntry:
    return ExceptionEntry(tag, sha, check, "tag-only-historical", "verified", ("e",), "#492")


def test_exception_matches_tag_commit_and_check_only(repo: Path) -> None:
    sha = make_valid(repo)
    report = run(repo, [], exceptions=[exception_for("v0.5.0", sha, "release-exists")])
    assert report.failures == []
    excepted = [f for f in report.findings if f.status == "excepted"]
    assert [f.check for f in excepted] == ["release-exists"]
    assert "tag-only-historical: verified (#492)" in excepted[0].reason
    assert "EXCEPTED" in render_text(report)


def test_exception_does_not_hide_a_different_defect(repo: Path) -> None:
    sha = make_valid(repo)
    report = run(
        repo,
        released("v0.5.0", draft=("v0.5.0",)),
        exceptions=[exception_for("v0.5.0", sha, "release-exists")],
    )
    assert checks(report) == {("v0.5.0", "release-draft")}
    assert any("stale exception" in n for n in report.notes)


def test_exception_is_void_when_tag_moves(repo: Path) -> None:
    make_valid(repo)
    report = run(repo, [], exceptions=[exception_for("v0.5.0", "a" * 40, "release-exists")])
    assert checks(report) == {("v0.5.0", "release-exists")}
    assert "exception void" in report.failures[0].message


def test_recipe_index_drift_is_reported(repo: Path) -> None:
    make_valid(repo)
    write(
        repo,
        "scripts/gen_recipe_index.py",
        "import sys\nprint('stale', file=sys.stderr)\nsys.exit(1)\n",
    )
    write(repo, "scripts/gen_recipe_table.py", "print('ok')\n")
    commit(repo, "docs: scripts")
    report = run(repo, released("v0.5.0"), run_generated_checks=True)
    assert checks(report) == {("HEAD", "recipe-index")}
    assert "stale" in report.failures[0].message
    assert run(repo, released("v0.5.0"), run_generated_checks=False).failures == []


def test_recipe_index_check_passes_when_scripts_succeed(repo: Path) -> None:
    make_valid(repo)
    write(repo, "scripts/gen_recipe_index.py", "print('ok')\n")
    commit(repo, "docs: scripts")
    assert run(repo, released("v0.5.0"), run_generated_checks=True).failures == []


def test_recipe_index_failure_without_output(repo: Path) -> None:
    make_valid(repo)
    write(repo, "scripts/gen_recipe_index.py", "raise SystemExit(1)\n")
    commit(repo, "docs: scripts")
    report = run(repo, released("v0.5.0"), run_generated_checks=True)
    assert "no output" in report.failures[0].message
    assert checks(report) == {("HEAD", "recipe-index")}


def test_content_only_changes_need_no_snapshot(repo: Path) -> None:
    make_valid(repo)
    commit(repo, "docs(recipe): fix typo")
    commit(repo, "ci: tweak workflow")
    report = run(repo, released("v0.5.0"))
    assert report.failures == []
    assert any("no snapshot is needed" in n for n in report.notes)


@pytest.mark.parametrize("subject", ["feat(recipes): add x", "fix: y", "docs!: breaking"])
def test_user_facing_changes_expect_a_snapshot(repo: Path, subject: str) -> None:
    make_valid(repo)
    commit(repo, subject)
    assert any("a snapshot is expected" in n for n in run(repo, released("v0.5.0")).notes)


def test_breaking_footer_expects_a_snapshot(repo: Path) -> None:
    make_valid(repo)
    commit(repo, "chore: change\n\nBREAKING CHANGE: yes")
    assert any("a snapshot is expected" in n for n in run(repo, released("v0.5.0")).notes)


def test_no_commits_since_tag(repo: Path) -> None:
    make_valid(repo)
    assert any("no snapshot pending" in n for n in run(repo, released("v0.5.0")).notes)


def test_version_manifest_and_changelog_mismatches(repo: Path) -> None:
    snapshot_files(repo, "0.5.0", changelog=False)
    write(repo, "src/azure_functions_python_cookbook/__init__.py", '__version__ = "0.4.0"\n')
    write(repo, ".release-please-manifest.json", json.dumps({".": "0.3.0"}))
    commit(repo, "chore(main): release 0.5.0")
    git(repo, "tag", "v0.5.0")
    report = run(repo, released("v0.5.0"))
    messages = [f.message for f in report.failures]
    assert any("__version__ is 0.4.0" in m for m in messages)
    assert any("records '0.3.0'" in m for m in messages)
    assert ("v0.5.0", "changelog-entry") in checks(report)


def test_missing_version_and_unparseable_manifest(repo: Path) -> None:
    snapshot_files(repo, "0.5.0")
    write(repo, "src/azure_functions_python_cookbook/__init__.py", "x = 1\n")
    write(repo, ".release-please-manifest.json", "[1]")
    commit(repo, "chore: release")
    git(repo, "tag", "v0.5.0")
    report = run(repo, released("v0.5.0"))
    assert any("is none" in f.message for f in report.failures)
    assert any("records None" in f.message for f in report.failures)


def test_pre_release_please_tags_skip_source_checks(repo: Path) -> None:
    write(repo, "README.md", "x")
    commit(repo, "initial")
    git(repo, "tag", "v0.1.0")
    report = run(repo, released("v0.1.0"))
    assert report.failures == []
    level = next(f for f in report.findings if f.check == "verification-level")
    assert "no CI workflow definitions" in level.message


def test_pre_release_please_tag_with_wrong_source_version(repo: Path) -> None:
    write(repo, "src/azure_functions_python_cookbook/__init__.py", '__version__ = "0.1.2"\n')
    commit(repo, "initial")
    git(repo, "tag", "v0.2.0")
    report = run(repo, released("v0.2.0"))
    assert checks(report) == {("v0.2.0", "source-version")}
    assert "__version__ is 0.1.2, expected 0.2.0" in report.failures[0].message


def test_invalid_and_duplicate_recipe_inventory(repo: Path) -> None:
    snapshot_files(repo, "0.1.0")
    write(repo, "recipes.json", json.dumps([{"slug": "a"}, {"slug": "a"}]))
    commit(repo, "one")
    git(repo, "tag", "v0.1.0")
    write(repo, "recipes.json", "not json")
    commit(repo, "two")
    git(repo, "tag", "v0.1.1")
    report = run(repo, released("v0.1.0", "v0.1.1"))
    messages = {(f.tag, f.message) for f in report.failures if f.check == "recipe-inventory"}
    assert ("v0.1.0", "recipes.json has duplicate slugs") in messages
    assert ("v0.1.1", "recipes.json is not a valid recipe list") in messages


def test_duplicate_commit_and_tag_order(repo: Path) -> None:
    write(repo, "a", "1")
    sha = commit(repo, "one")
    git(repo, "tag", "v0.1.0")
    git(repo, "tag", "v0.1.1")
    write(repo, "a", "2")
    commit(repo, "two")
    git(repo, "tag", "v0.2.0")
    write(repo, "a", "3")
    commit(repo, "three")
    git(repo, "tag", "v0.1.3")  # descends from v0.2.0
    report = run(repo, released("v0.1.0", "v0.1.1", "v0.2.0", "v0.1.3"))
    assert checks(report) == {("v0.1.1", "duplicate-commit"), ("v0.1.3", "tag-order")}
    assert report.tags[0][1] == sha


def test_diverging_tags_and_unreachable_tag(repo: Path) -> None:
    write(repo, "a", "1")
    commit(repo, "base")
    git(repo, "checkout", "-b", "side")
    write(repo, "a", "side")
    commit(repo, "side")
    git(repo, "tag", "v0.1.0")
    git(repo, "checkout", "main")
    write(repo, "a", "main")
    commit(repo, "main")
    git(repo, "tag", "v0.2.0")
    report = run(repo, released("v0.1.0", "v0.2.0"))
    assert ("v0.1.0", "ancestry") in checks(report)
    assert any("diverging histories" in f.message for f in report.failures)


def test_non_semver_tag_is_reported(repo: Path) -> None:
    write(repo, "a", "1")
    commit(repo, "one")
    git(repo, "tag", "v1.0")
    assert checks(run(repo, [])) == {("v1.0", "tag-name")}


def test_no_tags_is_a_clean_report(repo: Path) -> None:
    write(repo, "a", "1")
    commit(repo, "one")
    report = run(repo, [])
    assert report.failures == [] and report.tags == []


def test_missing_ref_is_an_audit_error(repo: Path) -> None:
    write(repo, "a", "1")
    commit(repo, "one")
    with pytest.raises(AuditError, match="not found"):
        audit(repo, ref="origin/main", slug=SLUG, releases=None, exceptions=[])


def test_git_failure_raises_audit_error(tmp_path: Path) -> None:
    with pytest.raises(AuditError, match="git rev-parse"):
        audit_mod._git(tmp_path, "rev-parse", "HEAD")


def valid_exception(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "tag": "v0.1.0",
        "commit": "b" * 40,
        "checks": ["release-exists"],
        "classification": "tag-only-historical",
        "reason": "r",
        "evidence": ["e"],
        "issue": "#1",
    }
    entry.update(overrides)
    return entry


def registry(tmp_path: Path, *entries: dict[str, Any]) -> Path:
    path = tmp_path / "exceptions.json"
    path.write_text(json.dumps({"exceptions": list(entries)}), encoding="utf-8")
    return path


def test_load_exceptions_accepts_valid_and_missing(tmp_path: Path) -> None:
    assert load_exceptions(tmp_path / "absent.json") == []
    (entry,) = load_exceptions(registry(tmp_path, valid_exception()))
    assert entry.tag == "v0.1.0" and entry.checks == ("release-exists",)


@pytest.mark.parametrize(
    "bad",
    [
        {"tag": "main"},
        {"commit": "abc"},
        {"checks": []},
        {"checks": ["nope"]},
        {"reason": ""},
        {"evidence": []},
        {"evidence": [1]},
    ],
)
def test_load_exceptions_rejects_invalid_entries(tmp_path: Path, bad: dict[str, Any]) -> None:
    with pytest.raises(AuditError, match="invalid exception registry"):
        load_exceptions(registry(tmp_path, valid_exception(**bad)))


def test_load_exceptions_rejects_missing_keys_bad_json_and_duplicates(tmp_path: Path) -> None:
    entry = valid_exception()
    del entry["issue"]
    with pytest.raises(AuditError):
        load_exceptions(registry(tmp_path, entry))
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    with pytest.raises(AuditError):
        load_exceptions(broken)
    with pytest.raises(AuditError, match="duplicate exception"):
        load_exceptions(registry(tmp_path, valid_exception(), valid_exception(commit="c" * 40)))


def test_repository_exception_registry_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    entries = load_exceptions(root / ".github" / "release-audit-exceptions.json")
    assert {e.tag for e in entries} == {"v0.1.0", "v0.1.1", "v0.1.3", "v0.2.0"}


def test_load_releases(tmp_path: Path) -> None:
    path = tmp_path / "r.json"
    path.write_text(json.dumps(released("v1.0.0")), encoding="utf-8")
    assert load_releases(path)[0]["tagName"] == "v1.0.0"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(AuditError, match="JSON array"):
        load_releases(path)
    with pytest.raises(AuditError, match="cannot read"):
        load_releases(tmp_path / "missing.json")


def test_fetch_releases_uses_read_only_gh_list(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(released("v1.0.0")), "")

    monkeypatch.setattr(subprocess, "run", fake)
    assert fetch_releases(SLUG)[0]["tagName"] == "v1.0.0"
    assert calls[0][:3] == ["gh", "release", "list"]
    assert not {"create", "edit", "delete"} & set(calls[0])


def test_fetch_releases_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda args, **_: subprocess.CompletedProcess(args, 1, "", "boom")
    )
    with pytest.raises(AuditError, match="boom"):
        fetch_releases(SLUG)

    def missing(*_: Any, **__: Any) -> None:
        raise FileNotFoundError("gh")

    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(AuditError, match="cannot run gh"):
        fetch_releases(SLUG)


def test_main_exit_codes_and_formats(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sha = make_valid(repo)
    rel = tmp_path / "rel.json"
    rel.write_text(json.dumps(released("v0.5.0")), encoding="utf-8")
    base = ["--repo", str(repo), "--ref", "main", "--skip-generated", "--releases-json", str(rel)]
    assert main(base) == 0
    assert "RESULT: PASS" in capsys.readouterr().out
    assert main([*base, "--format", "markdown"]) == 0
    assert capsys.readouterr().out.startswith("## Cookbook snapshot audit")
    assert main([*base, "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == "pass"

    rel.write_text("[]", encoding="utf-8")
    assert main(base) == 1
    assert "release-exists" in capsys.readouterr().out
    assert (
        main(
            [
                *base,
                "--exceptions",
                str(
                    registry(
                        tmp_path,
                        valid_exception(tag="v0.5.0", commit=sha, checks=["release-exists"]),
                    )
                ),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["--repo", str(repo), "--ref", "main", "--skip-releases", "--skip-generated"]) == 0
    assert main(["--repo", str(repo), "--ref", "nope", "--skip-releases"]) == 2
    assert "audit could not run" in capsys.readouterr().err
    assert main([*base, "--exceptions", str(tmp_path / "x.json")]) == 1


def test_main_fetches_releases_through_gh(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    make_valid(repo)
    monkeypatch.setattr(audit_mod, "fetch_releases", lambda slug: released("v0.5.0"))
    assert main(["--repo", str(repo), "--ref", "main", "--skip-generated"]) == 0
    capsys.readouterr()


def test_finding_defaults() -> None:
    finding = Finding("v1.0.0", "ancestry", "error", "m")
    assert finding.status == "" and finding.link == ""


def test_head_version_consistency_is_checked_before_release(repo: Path) -> None:
    make_valid(repo)
    assert run(repo, released("v0.5.0")).failures == []
    snapshot_files(repo, "0.6.0", changelog=False)
    write(repo, "src/azure_functions_python_cookbook/__init__.py", '__version__ = "0.5.0"\n')
    commit(repo, "chore(main): release 0.6.0")
    report = run(repo, released("v0.5.0"))
    messages = [f.message for f in report.failures if f.check == "head-version"]
    assert any("declares 0.5.0 but" in m and "records 0.6.0" in m for m in messages)
    assert any("newest CHANGELOG.md entry is none, expected 0.6.0" in m for m in messages)


def test_head_version_handles_unparseable_manifest_and_stale_changelog(repo: Path) -> None:
    snapshot_files(repo, "0.5.0")
    write(repo, ".release-please-manifest.json", "[1]")
    write(repo, "CHANGELOG.md", "## [0.4.0] x\n")
    commit(repo, "chore: x")
    messages = [f.message for f in run(repo, []).failures if f.check == "head-version"]
    assert any("records unparseable" in m for m in messages)
    assert any("newest CHANGELOG.md entry is 0.4.0, expected unparseable" in m for m in messages)


def test_exceptions_for_unchecked_areas_are_not_reported_stale(repo: Path) -> None:
    sha = make_valid(repo)
    report = run(repo, None, exceptions=[exception_for("v0.5.0", sha, "release-exists")])
    assert not any("stale exception" in n for n in report.notes)
