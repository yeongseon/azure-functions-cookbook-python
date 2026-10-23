from pathlib import Path
import xml.etree.ElementTree as ET

import pytest


def junit(directory: Path, outcomes: tuple[str, ...]) -> None:
    suite = ET.Element(
        "testsuite",
        tests=str(len(outcomes)),
        failures=str(outcomes.count("failure")),
        errors="0",
        skipped=str(outcomes.count("skipped")),
    )
    for index, outcome in enumerate(outcomes):
        case = ET.SubElement(suite, "testcase", classname="tests.recipe", name=f"case_{index}")
        if outcome != "passed":
            ET.SubElement(case, outcome)
    ET.ElementTree(suite).write(directory / "junit.xml")


@pytest.mark.parametrize("outcomes", [(), ("skipped",), ("passed", "skipped")])
def test_required_execution_is_incomplete_when_proof_is_missing(
    tmp_path: Path, outcomes: tuple[str, ...]
) -> None:
    # Given: a required suite with zero execution or an unexpected skip.
    from tools.verification_evidence import collect

    junit(tmp_path, outcomes)
    # When: a successful process is classified.
    result = collect(tmp_path, ["pytest"], 0)
    # Then: missing proof cannot pass.
    assert result.status == "INCOMPLETE"
    assert result.exit_code != 0


def test_junit_counters_are_checked_against_cases(tmp_path: Path) -> None:
    # Given: forged successful counters with a failed case.
    from tools.verification_evidence import collect

    (tmp_path / "junit.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase name="broken"><failure/></testcase></testsuite>'
    )
    # When / Then: contradictory evidence is rejected.
    with pytest.raises(ValueError, match="counter"):
        collect(tmp_path, ["pytest"], 0)


def test_success_counts_are_reported_by_family(tmp_path: Path) -> None:
    # Given: actual passing testcases.
    from tools.verification_evidence import collect

    junit(tmp_path, ("passed", "passed"))
    # When: evidence is collected.
    result = collect(tmp_path, ["pytest"], 0)
    # Then: selected and passed are measured, not inferred from exit zero.
    assert result.status == "PASS"
    assert result.families["tests.recipe"].passed == 2
    assert result.selected == 2


def test_secret_canaries_are_redacted_everywhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: secrets in environment, log, command and reason.
    from tools.verification_evidence import Summary, publish, save

    monkeypatch.setenv("PRIVATE_TOKEN", "canary-environment-value")
    canaries = ("canary-environment-value", "canary-password", "canary-key", "canary-query")
    text = (
        f"{canaries[0]} https://user:{canaries[1]}@example.org "
        f"AccountKey={canaries[2]}; https://example.org/?code={canaries[3]}"
    )
    (tmp_path / "runner.log").write_text(text)
    summary_path = tmp_path / "actions.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    # When: all evidence surfaces are saved/published.
    result = save(tmp_path, Summary("canary", (text,), reason=text))
    publish(result)
    # Then: none of the secret values survive.
    for artifact in tmp_path.iterdir():
        assert all(canary not in artifact.read_text() for canary in canaries)


def test_nonzero_process_is_not_hidden_by_successful_junit(tmp_path: Path) -> None:
    from tools.verification_evidence import collect

    # Given: successful cases but a failed test process.
    junit(tmp_path, ("passed",))
    # When / Then: original failure is retained.
    result = collect(tmp_path, ["pytest"], 42)
    assert (result.status, result.exit_code) == ("FAIL", 42)


def test_binary_coverage_is_not_treated_as_text(tmp_path: Path) -> None:
    from tools.verification_evidence import Summary, save

    (tmp_path / ".coverage").write_bytes(b"SQLite format 3\0\xff")
    result = save(tmp_path, Summary("test", ("pytest",)))
    assert result.status == "INCOMPLETE"
