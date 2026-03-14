"""Durable Functions determinism-safe orchestrator patterns."""

from __future__ import annotations

from typing import Any, Generator

import azure.durable_functions as df
import azure.functions as func

app = func.FunctionApp()
bp = df.Blueprint()


@bp.route(
    route="start-determinism",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@bp.durable_client_input(client_name="client")
async def start_determinism_demo(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = await client.start_new("determinism_orchestrator")
    return client.create_check_status_response(req, instance_id)


@bp.orchestration_trigger(context_name="context")
def determinism_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, dict[str, str]]:
    # WRONG: datetime.now() changes between replays and breaks deterministic state.
    # RIGHT: current_utc_datetime replays with the same value for this workflow point.
    safe_timestamp = context.current_utc_datetime.isoformat()

    # WRONG: uuid.uuid4() is random and generates different values on replay.
    # RIGHT: new_guid() is replay-safe and deterministic for orchestrators.
    safe_identifier = str(context.new_guid())

    # WRONG: direct network/disk I/O inside orchestrator causes non-deterministic replays.
    # RIGHT: delegate I/O to an activity so orchestration remains deterministic.
    io_result = yield context.call_activity("fetch_data_activity", "resource-1")

    return {
        "timestamp": safe_timestamp,
        "operation_id": safe_identifier,
        "data": io_result,
    }


@bp.activity_trigger(input_name="payload")
def fetch_data_activity(payload: str) -> str:
    return f"I/O completed for {payload}"


app.register_functions(bp)
