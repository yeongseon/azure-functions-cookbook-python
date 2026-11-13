"""HTTP routes driven with a fake Durable client (no host): 202 start, status, approve, cancel."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import azure.functions as func
import pytest
from durable_fakes import registered_functions

from app.core.limits import APPROVAL_EVENT_NAME, MAX_REQUEST_BYTES

FUNCTIONS = registered_functions()
CTX: Any = SimpleNamespace(invocation_id="inv-1")


class FakeClient:
    def __init__(self, runtime: str | None = "Running", custom: Any = None, output: Any = None):
        self.runtime, self.custom, self.output = runtime, custom, output
        self.started: list[dict[str, Any]] = []
        self.events: list[tuple[str, str, Any]] = []
        self.terminated: list[tuple[str, str]] = []
        self.fail: set[str] = set()

    async def start_new(self, name: str, instance_id: str, client_input: Any) -> str:
        if "start" in self.fail:
            raise RuntimeError("secret connection string")
        self.started.append({"name": name, "id": instance_id, "input": client_input})
        return instance_id

    async def get_status(self, instance_id: str) -> Any:
        runtime = None if self.runtime is None else SimpleNamespace(value=self.runtime)
        return SimpleNamespace(
            runtime_status=runtime, custom_status=self.custom, output=self.output
        )

    async def raise_event(self, instance_id: str, name: str, data: Any) -> None:
        if "raise" in self.fail:
            raise RuntimeError("boom")
        self.events.append((instance_id, name, data))

    async def terminate(self, instance_id: str, reason: str) -> None:
        if "terminate" in self.fail:
            raise RuntimeError("boom")
        self.terminated.append((instance_id, reason))


def call(name: str, client: FakeClient, body: Any = None, run_id: str | None = None) -> Any:
    raw = (
        body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else b""
    )
    req = func.HttpRequest(
        method="POST",
        url="http://localhost/api/x",
        body=raw,
        route_params={"run_id": run_id} if run_id else {},
    )
    handler = FUNCTIONS[name].get_user_function()
    # The durable_client_input decorator only injects the client binding; call the inner coroutine.
    inner = getattr(handler, "__wrapped__", handler)
    needs_ctx = "context" in inner.__code__.co_varnames[: inner.__code__.co_argcount]
    args = (req, client, CTX) if needs_ctx else (req, client)
    response = asyncio.run(inner(*args))
    return response.status_code, json.loads(response.get_body() or b"{}"), response


def test_routes_require_a_function_key_not_anonymous() -> None:
    for name in ("start_run", "get_run", "submit_approval", "cancel_run"):
        binding = next(b for b in FUNCTIONS[name].get_bindings() if b.type == "httpTrigger")
        assert binding.get_dict_repr()["authLevel"] == func.AuthLevel.FUNCTION


def test_start_returns_202_with_urls_and_never_waits_for_the_agent() -> None:
    client = FakeClient()
    status, body, response = call("start_run", client, {"prompt": "hello"})
    assert status == 202
    run_id = body["run_id"]
    assert client.started == [
        {
            "name": "agent_approval_orchestrator",
            "id": run_id,
            "input": {"prompt": "hello", "approval_timeout_seconds": 86400},
        }
    ]
    assert body["status_url"] == f"/api/agent-runs/{run_id}"
    assert body["approval_url"].endswith("/approval") and body["cancel_url"].endswith("/cancel")
    assert response.headers["Location"] == body["status_url"]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"prompt": ""},
        {"prompt": 5},
        {"prompt": "x" * 2001},
        {"prompt": "ok", "approval_timeout_seconds": 5},
        {"prompt": "ok", "approval_timeout_seconds": "60"},
        {"prompt": "ok", "approval_timeout_seconds": 10**9},
        [1],
        b"not json",
        b"x" * (MAX_REQUEST_BYTES + 1),
    ],
)
def test_start_rejects_bad_requests_before_starting_anything(body: Any) -> None:
    client = FakeClient()
    status, payload, _ = call("start_run", client, body)
    assert status == 400 and "error" in payload and client.started == []


def test_start_failure_is_a_generic_502_without_exception_text() -> None:
    client = FakeClient()
    client.fail.add("start")
    status, body, _ = call("start_run", client, {"prompt": "hi"})
    assert status == 502 and "secret" not in json.dumps(body)


@pytest.mark.parametrize(
    ("runtime", "custom", "output", "expected"),
    [
        ("Pending", None, None, {"status": "pending"}),
        ("Running", {"stage": "drafting"}, None, {"status": "running", "stage": "drafting"}),
        (
            "Running",
            {"stage": "awaiting_approval", "draft": "D"},
            None,
            {"status": "awaiting_approval", "draft": "D"},
        ),
        ("Suspended", None, None, {"status": "suspended"}),
        ("Terminated", None, None, {"status": "cancelled"}),
        ("Canceled", None, None, {"status": "cancelled"}),
        (
            "Completed",
            {"stage": "publishing"},
            {"outcome": "timed_out"},
            {"status": "timed_out", "result": {"outcome": "timed_out"}},
        ),
        (
            "Completed",
            None,
            {"outcome": "weird"},
            {"status": "failed", "result": {"outcome": "failed", "error": "unexpected_output"}},
        ),
    ],
)
def test_status_maps_durable_state_to_the_api_vocabulary(
    runtime: str, custom: Any, output: Any, expected: dict[str, Any]
) -> None:
    status, body, _ = call("get_run", FakeClient(runtime, custom, output), run_id="r1")
    assert status == 200 and body == {"run_id": "r1", **expected}


def test_failed_status_hides_durable_failure_text() -> None:
    client = FakeClient("Failed", output="Traceback: key=SECRET")
    status, body, _ = call("get_run", client, run_id="r1")
    assert body["status"] == "failed" and "SECRET" not in json.dumps(body)
    assert body["error"] == {"code": "run_failed", "message": "The run failed."}


def test_unknown_run_is_404_everywhere() -> None:
    for name, payload in (
        ("get_run", None),
        ("submit_approval", {"approved": True}),
        ("cancel_run", None),
    ):
        status, body, _ = call(name, FakeClient(None), payload, run_id="nope")
        assert status == 404 and body["error"] == "run not found"


def test_approval_is_forwarded_only_while_awaiting_it() -> None:
    waiting = FakeClient("Running", {"stage": "awaiting_approval", "draft": "D"})
    status, body, _ = call("submit_approval", waiting, {"approved": True}, run_id="r1")
    assert status == 202 and body["status"] == "decision_sent"
    assert waiting.events == [("r1", APPROVAL_EVENT_NAME, {"approved": True})]

    waiting_no = FakeClient("Running", {"stage": "awaiting_approval"})
    call("submit_approval", waiting_no, {"approved": False}, run_id="r1")
    assert waiting_no.events == [("r1", APPROVAL_EVENT_NAME, {"approved": False})]


@pytest.mark.parametrize(
    ("runtime", "custom"),
    [("Running", {"stage": "drafting"}), ("Completed", None), ("Terminated", None)],
)
def test_approval_outside_the_waiting_stage_is_a_409_and_sends_nothing(
    runtime: str, custom: Any
) -> None:
    client = FakeClient(runtime, custom, {"outcome": "completed"})
    status, _, _ = call("submit_approval", client, {"approved": True}, run_id="r1")
    assert status == 409 and client.events == []


@pytest.mark.parametrize("body", [{}, {"approved": "yes"}, {"approved": 1}, [True], b"nope"])
def test_malformed_decisions_are_rejected(body: Any) -> None:
    client = FakeClient("Running", {"stage": "awaiting_approval"})
    status, _, _ = call("submit_approval", client, body, run_id="r1")
    assert status == 400 and client.events == []


def test_approval_delivery_failure_is_a_generic_502() -> None:
    client = FakeClient("Running", {"stage": "awaiting_approval"})
    client.fail.add("raise")
    status, body, _ = call("submit_approval", client, {"approved": True}, run_id="r1")
    assert status == 502 and "boom" not in json.dumps(body)


def test_cancel_in_flight_run_requests_termination_and_does_not_claim_it_happened() -> None:
    client = FakeClient("Running", {"stage": "drafting"})
    status, body, _ = call("cancel_run", client, run_id="r1")
    assert (status, body["status"]) == (202, "cancel_requested")
    assert client.terminated == [("r1", "cancelled by caller")]


@pytest.mark.parametrize(
    ("runtime", "output", "expected"),
    [
        ("Completed", {"outcome": "completed"}, "completed"),
        ("Terminated", None, "cancelled"),
        ("Failed", None, "failed"),
    ],
)
def test_cancel_of_a_finished_run_reports_its_real_status_and_terminates_nothing(
    runtime: str, output: Any, expected: str
) -> None:
    client = FakeClient(runtime, None, output)
    status, body, _ = call("cancel_run", client, run_id="r1")
    assert (status, body["status"]) == (200, expected) and client.terminated == []


def test_cancel_failure_is_a_generic_502() -> None:
    client = FakeClient("Running")
    client.fail.add("terminate")
    status, body, _ = call("cancel_run", client, run_id="r1")
    assert status == 502 and "boom" not in json.dumps(body)
