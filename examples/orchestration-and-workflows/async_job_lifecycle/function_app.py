# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false, reportAny=false, reportExplicitAny=false

from __future__ import annotations

from collections.abc import Generator
import json
import logging
import time
from typing import Any

import azure.durable_functions as df
import azure.functions as func
from azure_functions_logging import setup_logging
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = logging.getLogger(__name__)

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TERMINAL_STATUSES = {"Completed", "Failed", "Terminated"}
LIFECYCLE_STATE_MAP = {
    "Pending": "pending",
    "Running": "running",
    "Completed": "completed",
    "Failed": "failed",
    "Terminated": "cancelled",
}


class JobCreateRequest(BaseModel):
    job_type: str = Field(..., min_length=1, description="Logical job type")
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    duration_seconds: int = Field(default=10, ge=0, le=300, description="Simulated work duration")
    should_fail: bool = Field(default=False, description="Force the activity to fail")


class CancelJobQuery(BaseModel):
    reason: str = Field(
        default="Cancelled by client request",
        min_length=1,
        max_length=200,
        description="Reason recorded in orchestration history",
    )


class JobAcceptedResponse(BaseModel):
    status: str
    instanceId: str
    statusQueryGetUri: str
    terminatePostUri: str | None = None
    purgeHistoryDeleteUri: str | None = None
    sendEventPostUri: str | None = None


class JobStatusResponse(BaseModel):
    instanceId: str
    runtimeStatus: str
    lifecycleState: str
    createdTime: str | None = None
    lastUpdatedTime: str | None = None
    customStatus: dict[str, Any] | None = None
    output: Any | None = None


class OperationResponse(BaseModel):
    status: str
    instanceId: str
    message: str
    reason: str | None = None


def _json_response(
    payload: dict[str, Any],
    *,
    status_code: int,
    headers: dict[str, str] | None = None,
) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
        headers=headers,
    )


def _to_json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _runtime_status_name(status: Any) -> str:
    return str(getattr(status, "runtime_status", "Unknown"))


def _project_job_status(status: Any, instance_id: str) -> dict[str, Any]:
    runtime_status = _runtime_status_name(status)
    return {
        "instanceId": getattr(status, "instance_id", instance_id),
        "runtimeStatus": runtime_status,
        "lifecycleState": LIFECYCLE_STATE_MAP.get(runtime_status, "unknown"),
        "createdTime": _to_json_value(getattr(status, "created_time", None)),
        "lastUpdatedTime": _to_json_value(getattr(status, "last_updated_time", None)),
        "customStatus": getattr(status, "custom_status", None),
        "output": getattr(status, "output", None),
    }


@app.route(route="jobs", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Create a durable async job",
    description="Starts a Durable Functions orchestration and returns built-in HTTP management URLs.",
    request_body=JobCreateRequest,
    response={202: JobAcceptedResponse},
    tags=["async-jobs"],
)
@validate_http(body=JobCreateRequest, response_model=JobAcceptedResponse)
@app.durable_client_input(client_name="client")
async def create_job(
    req: func.HttpRequest,
    body: JobCreateRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    payload = body.model_dump()
    instance_id = await client.start_new("async_job_orchestrator", None, payload)

    check_status = client.create_check_status_response(req, instance_id)
    management_payload = json.loads(check_status.get_body().decode("utf-8"))

    logger.info(
        "Accepted async job",
        extra={
            "instance_id": instance_id,
            "job_type": payload["job_type"],
            "customer_id": payload["customer_id"],
        },
    )

    return _json_response(
        {
            "status": "accepted",
            "instanceId": instance_id,
            "statusQueryGetUri": management_payload["statusQueryGetUri"],
            "terminatePostUri": management_payload.get("terminatePostUri"),
            "purgeHistoryDeleteUri": management_payload.get("purgeHistoryDeleteUri"),
            "sendEventPostUri": management_payload.get("sendEventPostUri"),
        },
        status_code=202,
        headers=dict(check_status.headers),
    )


@app.route(route="jobs/{instance_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Get async job status",
    description="Returns the current Durable runtime state projected into a job lifecycle view.",
    response={200: JobStatusResponse, 404: dict[str, str]},
    tags=["async-jobs"],
)
@app.durable_client_input(client_name="client")
async def get_job_status(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = req.route_params["instance_id"]
    status = await client.get_status(instance_id)
    if status is None:
        return _json_response(
            {"error": "Job instance not found.", "instanceId": instance_id},
            status_code=404,
        )

    payload = _project_job_status(status, instance_id)
    logger.info(
        "Fetched async job status",
        extra={
            "instance_id": instance_id,
            "runtime_status": payload["runtimeStatus"],
            "lifecycle_state": payload["lifecycleState"],
        },
    )
    return _json_response(payload, status_code=200)


@app.route(route="jobs/{instance_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Cancel an async job",
    description="Requests cancellation by terminating the durable orchestration instance.",
    response={202: OperationResponse, 404: dict[str, str], 409: dict[str, str]},
    tags=["async-jobs"],
)
@validate_http(query=CancelJobQuery, response_model=OperationResponse)
@app.durable_client_input(client_name="client")
async def cancel_job(
    req: func.HttpRequest,
    query: CancelJobQuery,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = req.route_params["instance_id"]
    status = await client.get_status(instance_id)
    if status is None:
        return _json_response(
            {"error": "Job instance not found.", "instanceId": instance_id},
            status_code=404,
        )

    runtime_status = _runtime_status_name(status)
    if runtime_status in TERMINAL_STATUSES:
        return _json_response(
            {
                "error": "Job is already terminal and cannot be cancelled.",
                "instanceId": instance_id,
                "runtimeStatus": runtime_status,
            },
            status_code=409,
        )

    await client.terminate(instance_id, query.reason)
    logger.info(
        "Cancellation requested for async job",
        extra={"instance_id": instance_id, "reason": query.reason},
    )
    return _json_response(
        {
            "status": "cancellation-requested",
            "instanceId": instance_id,
            "message": "Termination has been queued. Poll status until lifecycleState becomes cancelled.",
            "reason": query.reason,
        },
        status_code=202,
    )


@app.route(
    route="jobs/{instance_id}/history",
    methods=["DELETE"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@openapi(
    summary="Purge async job history",
    description="Purges Durable Functions history for a completed, failed, or cancelled job instance.",
    response={202: OperationResponse, 404: dict[str, str], 409: dict[str, str]},
    tags=["async-jobs"],
)
@app.durable_client_input(client_name="client")
async def purge_job_history(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    instance_id = req.route_params["instance_id"]
    status = await client.get_status(instance_id)
    if status is None:
        return _json_response(
            {"error": "Job instance not found or already purged.", "instanceId": instance_id},
            status_code=404,
        )

    runtime_status = _runtime_status_name(status)
    if runtime_status not in TERMINAL_STATUSES:
        return _json_response(
            {
                "error": "Only terminal jobs can be purged.",
                "instanceId": instance_id,
                "runtimeStatus": runtime_status,
            },
            status_code=409,
        )

    await client.purge_instance_history(instance_id)
    logger.info(
        "Purge requested for async job history",
        extra={"instance_id": instance_id, "runtime_status": runtime_status},
    )
    return _json_response(
        {
            "status": "purge-requested",
            "instanceId": instance_id,
            "message": "Durable instance history purge has been requested.",
            "reason": None,
        },
        status_code=202,
    )


@app.orchestration_trigger(context_name="context")
def async_job_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, dict[str, Any]]:
    payload = context.get_input() or {}
    context.set_custom_status(
        {
            "state": "running",
            "jobType": payload.get("job_type"),
            "customerId": payload.get("customer_id"),
        }
    )
    result = yield context.call_activity("run_async_job_activity", payload)
    return {
        "status": "completed",
        "instanceId": context.instance_id,
        "result": result,
    }


@app.activity_trigger(input_name="job_request")
def run_async_job_activity(job_request: dict[str, Any]) -> dict[str, Any]:
    job_type = str(job_request.get("job_type", "unknown-job"))
    customer_id = str(job_request.get("customer_id", "unknown-customer"))
    duration_seconds = int(job_request.get("duration_seconds", 10))
    should_fail = bool(job_request.get("should_fail", False))

    logger.info(
        "Running async job activity",
        extra={
            "job_type": job_type,
            "customer_id": customer_id,
            "duration_seconds": duration_seconds,
            "should_fail": should_fail,
        },
    )
    time.sleep(duration_seconds)

    if should_fail:
        logger.error(
            "Async job activity failed by request",
            extra={"job_type": job_type, "customer_id": customer_id},
        )
        raise ValueError("Job failed because should_fail=true was provided.")

    result = {
        "jobType": job_type,
        "customerId": customer_id,
        "artifactUrl": f"https://example.invalid/jobs/{customer_id}/{job_type}.json",
        "durationSeconds": duration_seconds,
    }
    logger.info(
        "Completed async job activity",
        extra={"job_type": job_type, "customer_id": customer_id},
    )
    return result
