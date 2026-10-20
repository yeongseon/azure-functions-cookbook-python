"""Regression coverage for #371: call the Durable status response builder synchronously.

``DurableOrchestrationClient.create_check_status_response`` is a synchronous
SDK method that returns ``func.HttpResponse`` immediately; only
``start_new`` is asynchronous. Awaiting the synchronous method raised
``TypeError: object HttpResponse can't be used in 'await' expression`` after
an orchestration had already been started, so a caller saw a failed starter
even though the reminder was scheduled.

Exercises the real ``start_reminder`` handler with real SDK binding metadata;
only ``start_new`` is mocked. ``create_check_status_response`` is left
intact so an ``AsyncMock`` can't hide the contract mismatch.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import azure.durable_functions as df
import azure.functions as func

from tests._isolation import load_example_module

EXAMPLE_PATH = "scheduled-and-background/durable_timer_reminder"


def _context(name: str = "start_reminder") -> func.Context:
    return SimpleNamespace(  # type: ignore[return-value]
        invocation_id="offline-test",
        function_name=name,
        trace_context=SimpleNamespace(trace_parent=None, trace_state=None),
    )


def _start_request() -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="https://example.invalid/api/reminders/start",
        headers={"Content-Type": "application/json"},
        body=json.dumps(
            {"recipient": "reminders@example.invalid", "subject": "Demo", "delay_days": 7}
        ).encode(),
    )


def _client_binding() -> str:
    return json.dumps(
        {
            "taskHubName": "Review",
            "creationUrls": {},
            "managementUrls": {
                "id": "instance-1",
                "statusQueryGetUri": "https://example.invalid/instances/instance-1",
            },
        }
    )


def test_start_reminder_returns_202_after_exactly_one_orchestration_start() -> None:
    module = load_example_module(EXAMPLE_PATH)
    handler = module.start_reminder.build().get_user_function()

    with patch.object(
        df.DurableOrchestrationClient, "start_new", new=AsyncMock(return_value="instance-1")
    ) as start_new:
        response = asyncio.run(
            handler(req=_start_request(), client=_client_binding(), context=_context())
        )

    assert start_new.await_count == 1
    assert response.status_code == 202
    assert response.headers.get("Location")

    payload = json.loads(response.get_body())
    assert payload["instance_id"] == "instance-1"
    assert payload["status_query_get_uri"] == response.headers["Location"]


def test_create_check_status_response_is_synchronous_on_the_real_sdk() -> None:
    # Locks in the SDK contract this bug violated: asserting it stays
    # synchronous makes a future SDK change that breaks this assumption
    # fail loudly here, instead of silently reintroducing #371.
    import inspect

    assert not inspect.iscoroutinefunction(
        df.DurableOrchestrationClient.create_check_status_response
    )
