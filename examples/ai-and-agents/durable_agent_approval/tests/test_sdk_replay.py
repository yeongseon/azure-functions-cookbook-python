"""Drive the *real* azure-functions-durable orchestrator handle from synthetic history.

No Durable host, storage or network: the SDK's replay engine is a pure function of
(orchestrator, history). Each test feeds the history the host would have recorded so far and checks
the actions the SDK asks the host to perform next. The event shapes below were derived by running
the installed SDK; they are not a statement about what a particular host version emits.

Not covered here: the host's own retry execution (the SDK only forwards the retry options), timer
firing in real time, delivery of events, termination, or storage.
"""

from __future__ import annotations

import json
from typing import Any

from durable_fakes import registered_functions

HANDLE = registered_functions()["agent_approval_orchestrator"].get_user_function()

T0 = "2030-01-01T12:00:00Z"
T1 = "2030-01-01T13:00:00Z"
INPUT = json.dumps({"prompt": "hi", "approval_timeout_seconds": 3600})

STARTED = [
    {"EventType": 12, "EventId": -1, "IsPlayed": False, "Timestamp": T0},
    {
        "EventType": 0,
        "EventId": -1,
        "IsPlayed": False,
        "Timestamp": T0,
        "Name": "agent_approval_orchestrator",
        "Input": INPUT,
        "Version": "",
    },
]


def event(kind: int, **fields: Any) -> dict[str, Any]:
    return {
        "EventType": kind,
        "EventId": fields.pop("EventId", -1),
        "IsPlayed": True,
        "Timestamp": fields.pop("Timestamp", T0),
        **fields,
    }


DRAFTED = [
    event(4, EventId=0, Name="run_agent_draft", Input="{}"),
    event(5, TaskScheduledId=0, Result=json.dumps({"draft": "DRAFT"})),
]
TIMER_CREATED = [event(10, EventId=1, FireAt=T1)]
APPROVED = [event(15, Name="ApprovalDecision", Input=json.dumps({"approved": True}))]
REJECTED = [event(15, Name="ApprovalDecision", Input=json.dumps({"approved": False}))]
TIMER_FIRED = [event(11, TimerId=1, FireAt=T1, Timestamp=T1)]


def replay(*parts: list[dict[str, Any]]) -> dict[str, Any]:
    history = [item for part in parts for item in part]
    context = {
        "history": history,
        "input": INPUT,
        "instanceId": "abc",
        "isReplaying": False,
        "parentInstanceId": None,
    }
    result: dict[str, Any] = json.loads(HANDLE(json.dumps(context)))
    return result


def scheduled(out: dict[str, Any]) -> list[dict[str, Any]]:
    return [action for step in out["actions"] for action in step]


def test_first_episode_schedules_only_the_draft_activity_with_bounded_retries() -> None:
    out = replay(STARTED)
    assert out["isDone"] is False
    assert out["customStatus"] == {"stage": "drafting"}
    (draft,) = scheduled(out)
    assert draft["functionName"] == "run_agent_draft"
    assert json.loads(draft["input"]) == {"run_id": "abc", "prompt": "hi"}
    assert draft["retryOptions"] == {
        "firstRetryIntervalInMilliseconds": 5000,
        "maxNumberOfAttempts": 3,
    }


def test_after_the_draft_it_waits_for_the_event_and_a_timer_with_the_draft_visible() -> None:
    out = replay(STARTED, DRAFTED)
    assert out["isDone"] is False
    assert out["customStatus"] == {"stage": "awaiting_approval", "draft": "DRAFT"}
    wait, timer = scheduled(out)[1:]
    assert wait["externalEventName"] == "ApprovalDecision"
    assert timer["fireAt"].startswith("2030-01-01T13:00:00")  # history time + 3600 s
    assert timer["isCanceled"] is False


def test_approval_cancels_the_timer_and_schedules_only_the_publish_activity() -> None:
    out = replay(STARTED, DRAFTED, TIMER_CREATED, APPROVED)
    actions = scheduled(out)
    assert out["isDone"] is False and out["customStatus"] == {"stage": "publishing"}
    assert [a for a in actions if a.get("isCanceled")]
    publish = actions[-1]
    assert publish["functionName"] == "publish_approved_result"
    assert json.loads(publish["input"]) == {"run_id": "abc", "draft": "DRAFT"}


def test_rejection_finishes_without_scheduling_the_publish_activity() -> None:
    out = replay(STARTED, DRAFTED, TIMER_CREATED, REJECTED)
    assert out["isDone"] is True
    assert out["output"] == {"outcome": "rejected", "run_id": "abc"}
    assert "publish_approved_result" not in json.dumps(out["actions"])


def test_timer_firing_first_finishes_as_timed_out_without_publishing() -> None:
    out = replay(STARTED, DRAFTED, TIMER_CREATED, TIMER_FIRED)
    assert out["isDone"] is True
    assert out["output"] == {"outcome": "timed_out", "run_id": "abc"}
    assert "publish_approved_result" not in json.dumps(out["actions"])


def test_publish_result_completes_the_run_with_the_receipt() -> None:
    publish = [
        event(4, EventId=2, Name="publish_approved_result", Input="{}"),
        event(
            5,
            TaskScheduledId=2,
            Result=json.dumps({"receipt": "r", "chars": 5, "duplicate_delivery": False}),
        ),
    ]
    out = replay(STARTED, DRAFTED, TIMER_CREATED, APPROVED, publish)
    assert out["isDone"] is True
    assert out["output"] == {
        "outcome": "completed",
        "run_id": "abc",
        "receipt": "r",
        "chars": 5,
        "duplicate_delivery": False,
    }


def test_replay_is_repeatable_for_identical_history() -> None:
    history = (STARTED, DRAFTED, TIMER_CREATED, APPROVED)
    assert replay(*history) == replay(*history)
