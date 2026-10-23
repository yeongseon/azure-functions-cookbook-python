import pytest


@pytest.fixture(autouse=True)
def isolate_job_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
