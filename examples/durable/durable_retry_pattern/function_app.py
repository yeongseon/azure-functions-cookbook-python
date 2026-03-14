"""Durable Functions retry pattern with RetryOptions."""

from __future__ import annotations

import random
from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-retry",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_retry(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("retry_orchestrator", None, {"input": "demo"})
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def retry_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, str]:
    input_data = context.get_input() or {"input": "default"}
    retry_opts = df.RetryOptions(
        first_retry_interval_in_milliseconds=5000,
        max_number_of_attempts=3,
    )
    result = yield context.call_activity_with_retry(
        "flaky_activity",
        retry_opts,
        input_data,
    )
    return result


@bp.activity_trigger(input_name="payload")
def flaky_activity(payload: dict[str, str]) -> str:
    failure_roll = random.random()
    if failure_roll < 0.6:
        raise RuntimeError("Transient activity failure. Please retry.")
    return f"Succeeded with payload: {payload['input']}"


app.register_functions(bp)
