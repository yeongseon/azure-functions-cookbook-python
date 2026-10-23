from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_tag_build_depends_on_blocking_dependency_policy() -> None:
    tag = yaml.safe_load((ROOT / ".github/workflows/tag-verification.yml").read_text())
    assert tag["jobs"]["build"]["needs"] == "recipe-dependency-policy"
    reusable = yaml.safe_load((ROOT / ".github/workflows/recipe-release-security.yml").read_text())
    steps = reusable["jobs"]["dependency-policy"]["steps"]
    assert any(step.get("run") == "make security-dependencies" for step in steps)
    assert not any(step.get("continue-on-error") for step in steps)
    assert any(
        step.get("if") == "always()" and "upload-artifact@" in step.get("uses", "")
        for step in steps
    )


def test_security_workflow_retains_pinned_semgrep_and_existing_bandit() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/security.yml").read_text())
    jobs = workflow["jobs"]
    assert any(step.get("run") == "make security" for step in jobs["bandit"]["steps"])
    assert any(
        step.get("uses") == "semgrep/semgrep-action@713efdd345f3035192eaa63f56867b88e63e4e5d"
        for step in jobs["semgrep"]["steps"]
    )
    assert any(
        step.get("run") == "make security-dependencies-report"
        for step in jobs["recipe-dependency-report"]["steps"]
    )


def test_collectors_always_run_and_semgrep_only_tolerates_incomplete() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/security.yml").read_text())
    for job, command in [
        ("semgrep", "make security-semgrep"),
        ("recipe-security", "make security-static"),
    ]:
        collector = next(
            step for step in workflow["jobs"][job]["steps"] if step.get("run") == command
        )
        assert collector["if"] == "always()"
    makefile = (ROOT / "Makefile").read_text()
    assert 'test "$${status:-0}" -eq 3 -o "$${status:-0}" -eq 0' in makefile
    assert "--no-cov" in makefile


def test_ci_coverage_does_not_override_tool_inventory() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci-test.yml").read_text())
    command = next(
        step["run"]
        for step in workflow["jobs"]["test"]["steps"]
        if step.get("name") == "Run tests on the matrix interpreter"
    )
    assert "--cov=src/" not in command
