"""Regression coverage for #361: normalize Durable runtime status enum values.

``OrchestrationRuntimeStatus.Completed`` stringifies to
``"OrchestrationRuntimeStatus.Completed"``, not the documented ``"Completed"``
this recipe's lifecycle map and terminal-state checks key on. Exercises the
registered HTTP handlers directly with real ``DurableOrchestrationStatus``
instances; only the Durable client's network methods are mocked.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import json
from unittest.mock import AsyncMock, patch

import azure.durable_functions as df
from azure.durable_functions.models.DurableOrchestrationStatus import DurableOrchestrationStatus
import azure.functions as func
import pytest

from tests._isolation import load_example_module

EXAMPLE_PATH = "orchestration-and-workflows/async_job_lifecycle"
_CLIENT_BINDING = json.dumps({"taskHubName": "offline", "creationUrls": {}, "managementUrls": {}})


HandlerMap = dict[str, Callable[..., Awaitable[func.HttpResponse]]]


@pytest.fixture
def handlers() -> HandlerMap:
    module = load_example_module(EXAMPLE_PATH)
    return {f.get_function_name(): f.get_user_function() for f in module.app.get_functions()}


def _request(method: str, suffix: str = "") -> func.HttpRequest:
    return func.HttpRequest(
        method,
        "http://localhost/api/jobs/job-1" + suffix,
        headers={},
        params={},
        route_params={"instance_id": "job-1"},
        body=b"",
    )


LIFECYCLE_BY_RUNTIME_STATUS = {
    df.OrchestrationRuntimeStatus.Pending: "pending",
    df.OrchestrationRuntimeStatus.Running: "running",
    df.OrchestrationRuntimeStatus.Completed: "completed",
    df.OrchestrationRuntimeStatus.Failed: "failed",
    df.OrchestrationRuntimeStatus.Terminated: "cancelled",
}

TERMINAL_RUNTIME_STATUSES = (
    df.OrchestrationRuntimeStatus.Completed,
    df.OrchestrationRuntimeStatus.Failed,
    df.OrchestrationRuntimeStatus.Terminated,
)


def _sdk_status(runtime_status: df.OrchestrationRuntimeStatus) -> DurableOrchestrationStatus:
    return DurableOrchestrationStatus(instanceId="job-1", runtimeStatus=runtime_status)


@pytest.mark.parametrize("runtime_status,expected_lifecycle", LIFECYCLE_BY_RUNTIME_STATUS.items())
def test_status_projects_correct_lifecycle_for_every_runtime_status(
    handlers: HandlerMap, runtime_status: df.OrchestrationRuntimeStatus, expected_lifecycle: str
) -> None:
    sdk_status = _sdk_status(runtime_status)

    async def _run() -> func.HttpResponse:
        with patch.object(
            df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=sdk_status)
        ):
            return await handlers["get_job_status"](req=_request("GET"), client=_CLIENT_BINDING)

    response = asyncio.run(_run())

    assert response.status_code == 200
    payload = json.loads(response.get_body())
    assert payload["runtimeStatus"] == runtime_status.value
    assert payload["lifecycleState"] == expected_lifecycle


@pytest.mark.parametrize("runtime_status", TERMINAL_RUNTIME_STATUSES)
def test_cancel_rejects_terminal_instances_without_calling_terminate(
    handlers: HandlerMap, runtime_status: df.OrchestrationRuntimeStatus
) -> None:
    sdk_status = _sdk_status(runtime_status)
    terminate = AsyncMock()

    async def _run() -> func.HttpResponse:
        with (
            patch.object(
                df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=sdk_status)
            ),
            patch.object(df.DurableOrchestrationClient, "terminate", new=terminate),
        ):
            return await handlers["cancel_job"](req=_request("DELETE"), client=_CLIENT_BINDING)

    response = asyncio.run(_run())

    assert response.status_code == 409
    terminate.assert_not_awaited()


def test_cancel_accepts_running_instance_and_calls_terminate(handlers: HandlerMap) -> None:
    sdk_status = _sdk_status(df.OrchestrationRuntimeStatus.Running)
    terminate = AsyncMock()

    async def _run() -> func.HttpResponse:
        with (
            patch.object(
                df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=sdk_status)
            ),
            patch.object(df.DurableOrchestrationClient, "terminate", new=terminate),
        ):
            return await handlers["cancel_job"](req=_request("DELETE"), client=_CLIENT_BINDING)

    response = asyncio.run(_run())

    assert response.status_code == 202
    terminate.assert_awaited_once()


@pytest.mark.parametrize("runtime_status", TERMINAL_RUNTIME_STATUSES)
def test_purge_accepts_terminal_instances_and_calls_purge_exactly_once(
    handlers: HandlerMap, runtime_status: df.OrchestrationRuntimeStatus
) -> None:
    sdk_status = _sdk_status(runtime_status)
    purge = AsyncMock()

    async def _run() -> func.HttpResponse:
        with (
            patch.object(
                df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=sdk_status)
            ),
            patch.object(df.DurableOrchestrationClient, "purge_instance_history", new=purge),
        ):
            return await handlers["purge_job_history"](
                req=_request("DELETE", "/history"), client=_CLIENT_BINDING
            )

    response = asyncio.run(_run())

    assert response.status_code == 202
    purge.assert_awaited_once()


def test_purge_rejects_nonterminal_instance(handlers: HandlerMap) -> None:
    sdk_status = _sdk_status(df.OrchestrationRuntimeStatus.Running)
    purge = AsyncMock()

    async def _run() -> func.HttpResponse:
        with (
            patch.object(
                df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=sdk_status)
            ),
            patch.object(df.DurableOrchestrationClient, "purge_instance_history", new=purge),
        ):
            return await handlers["purge_job_history"](
                req=_request("DELETE", "/history"), client=_CLIENT_BINDING
            )

    response = asyncio.run(_run())

    assert response.status_code == 409
    purge.assert_not_awaited()


def test_missing_instance_returns_404_for_all_three_operations(handlers: HandlerMap) -> None:
    async def _run() -> tuple[func.HttpResponse, func.HttpResponse, func.HttpResponse]:
        with patch.object(
            df.DurableOrchestrationClient, "get_status", new=AsyncMock(return_value=None)
        ):
            status_response = await handlers["get_job_status"](
                req=_request("GET"), client=_CLIENT_BINDING
            )
            cancel_response = await handlers["cancel_job"](
                req=_request("DELETE"), client=_CLIENT_BINDING
            )
            purge_response = await handlers["purge_job_history"](
                req=_request("DELETE", "/history"), client=_CLIENT_BINDING
            )
        return status_response, cancel_response, purge_response

    status_response, cancel_response, purge_response = asyncio.run(_run())

    assert status_response.status_code == 404
    assert cancel_response.status_code == 404
    assert purge_response.status_code == 404
