"""Orchestrator behaviour driven by a fake context: approval, rejection, timeout, failures."""

from __future__ import annotations

import ast
import inspect
import random
import textwrap
import time
import uuid
from datetime import timedelta
from typing import Any

import pytest
from durable_fakes import FakeContext, Scenario, drive, registered_functions

from app.core.limits import (
    DEFAULT_APPROVAL_TIMEOUT_SECONDS,
    DRAFT_MAX_ATTEMPTS,
    DRAFT_RETRY_INTERVAL_MS,
    MAX_APPROVAL_TIMEOUT_SECONDS,
    MIN_APPROVAL_TIMEOUT_SECONDS,
)

FUNCTIONS = registered_functions()
# The registered function is the SDK handle; the generator under test is its orchestrator_function.
orchestrator = FUNCTIONS["agent_approval_orchestrator"].get_user_function().orchestrator_function
REQUEST = {"prompt": "hello", "approval_timeout_seconds": 3600}


def run(scenario: Scenario, request: Any = REQUEST, *, replaying: bool = False) -> tuple[Any, Any]:
    ctx = FakeContext(request, replaying=replaying)
    return drive(orchestrator(ctx), scenario), ctx


def activity_names(ctx: FakeContext) -> list[str]:
    return [c[1] for c in ctx.calls if c[0].startswith("activity")]


def test_registered_as_one_orchestrator_two_activities_and_four_routes() -> None:
    triggers = {n: [b.type for b in f.get_bindings()] for n, f in FUNCTIONS.items()}
    assert "orchestrationTrigger" in triggers["agent_approval_orchestrator"]
    assert "activityTrigger" in triggers["run_agent_draft"]
    assert "activityTrigger" in triggers["publish_approved_result"]
    routes = [n for n, t in triggers.items() if "httpTrigger" in t]
    assert sorted(routes) == ["cancel_run", "get_run", "start_run", "submit_approval"]


def test_approved_run_drafts_then_publishes_with_a_cancelled_timer() -> None:
    result, ctx = run(Scenario())
    assert result == {
        "outcome": "completed",
        "run_id": "run-123",
        "receipt": "r1",
        "chars": 5,
    }
    assert activity_names(ctx) == ["run_agent_draft", "publish_approved_result"]
    assert ctx.timers[0].cancelled is True
    assert ctx.statuses[0] == {"stage": "drafting"}
    assert ctx.statuses[1] == {"stage": "awaiting_approval", "draft": "DRAFT"}
    assert ctx.statuses[2] == {"stage": "publishing"}
    publish = [c for c in ctx.calls if c[1:2] == ("publish_approved_result",)][0]
    assert publish[2] == {"run_id": "run-123", "draft": "DRAFT"}


def test_draft_activity_is_retried_under_a_bounded_policy() -> None:
    _, ctx = run(Scenario())
    call = ctx.calls[0]
    assert call[:2] == ("activity_retry", "run_agent_draft")
    assert call[2] == {"run_id": "run-123", "prompt": "hello"}
    assert call[3:] == (DRAFT_RETRY_INTERVAL_MS, DRAFT_MAX_ATTEMPTS)
    assert DRAFT_MAX_ATTEMPTS <= 3


def test_timeout_wins_never_publishes_and_reports_timed_out() -> None:
    result, ctx = run(Scenario(race=("timeout",)))
    assert result == {"outcome": "timed_out", "run_id": "run-123"}
    assert "publish_approved_result" not in activity_names(ctx)
    assert ctx.timers[0].cancelled is False


@pytest.mark.parametrize(
    "payload",
    [{"approved": False}, {}, None, "true", {"approved": "true"}, {"approved": 1}, ["approved"]],
)
def test_anything_but_an_explicit_true_is_a_rejection(payload: Any) -> None:
    result, ctx = run(Scenario(race=("approval", payload)))
    assert result == {"outcome": "rejected", "run_id": "run-123"}
    assert "publish_approved_result" not in activity_names(ctx)


def test_draft_failure_is_an_explicit_failed_outcome_without_waiting_for_approval() -> None:
    result, ctx = run(Scenario(draft=RuntimeError("agent_draft_failed")))
    assert result == {"outcome": "failed", "run_id": "run-123", "stage": "draft"}
    assert ctx.timers == [] and ctx.events == []


def test_publish_failure_reports_that_the_effect_is_unknown() -> None:
    result, _ = run(Scenario(publish=RuntimeError("publish_failed")))
    assert result == {
        "outcome": "failed",
        "run_id": "run-123",
        "stage": "publish",
        "effect_unknown": True,
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (3600, 3600),
        (1, MIN_APPROVAL_TIMEOUT_SECONDS),
        (10**9, MAX_APPROVAL_TIMEOUT_SECONDS),
        (None, DEFAULT_APPROVAL_TIMEOUT_SECONDS),
        ("3600", DEFAULT_APPROVAL_TIMEOUT_SECONDS),
        (True, DEFAULT_APPROVAL_TIMEOUT_SECONDS),
    ],
)
def test_timer_deadline_is_context_time_plus_a_clamped_timeout(raw: Any, expected: int) -> None:
    _, ctx = run(Scenario(race=("timeout",)), {"prompt": "p", "approval_timeout_seconds": raw})
    (timer_call,) = [c for c in ctx.calls if c[0] == "timer"]
    assert timer_call[1] == FakeContext.current_utc_datetime + timedelta(seconds=expected)


def test_approval_cap_stays_below_the_documented_six_day_python_timer_limit() -> None:
    assert MAX_APPROVAL_TIMEOUT_SECONDS < 6 * 24 * 60 * 60


def test_missing_input_does_not_crash_the_orchestrator() -> None:
    result, ctx = run(Scenario(), request=None)
    assert result["outcome"] == "completed"
    assert ctx.calls[0][2]["prompt"] == ""


# --- replay / determinism --------------------------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    [
        Scenario(),
        Scenario(race=("timeout",)),
        Scenario(race=("approval", {"approved": False})),
        Scenario(draft=RuntimeError("x")),
    ],
)
def test_replaying_the_same_history_schedules_the_same_calls(scenario: Scenario) -> None:
    first_result, first = run(scenario)
    second_result, second = run(scenario, replaying=True)
    assert first_result == second_result
    assert first.calls == second.calls and first.statuses == second.statuses


def test_orchestrator_makes_no_clock_random_or_uuid_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: Any, **__: Any) -> Any:
        raise AssertionError("non-deterministic call inside the orchestrator")

    for module, name in [(time, "time"), (time, "sleep"), (random, "random"), (uuid, "uuid4")]:
        monkeypatch.setattr(module, name, boom)
    result, _ = run(Scenario())
    assert result["outcome"] == "completed"


def test_orchestrator_references_no_model_graph_network_clock_or_random_names() -> None:
    """Static guard: look at the identifiers the orchestrator uses, not at its docstring."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(orchestrator)))
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    forbidden = {
        "run_agent", "get_model", "build_graph", "build_model", "get_sink", "publish_approved",
        "openai", "requests", "urllib", "httpx", "os", "environ", "getenv", "open", "print",
        "now", "utcnow", "today", "time", "sleep", "uuid", "uuid4", "random", "datetime",
    }  # fmt: skip
    assert used & forbidden == set()


def test_replaying_orchestrator_does_not_log(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    run(Scenario(race=("timeout",)), replaying=True)
    assert caplog.text == ""
    run(Scenario(race=("timeout",)), replaying=False)
    assert "Approval timed out run_id=run-123" in caplog.text
