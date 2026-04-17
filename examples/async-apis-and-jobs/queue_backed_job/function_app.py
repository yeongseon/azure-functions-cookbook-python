# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from pydantic import BaseModel, Field

try:
    from azure_functions_logging import setup_logging
except ImportError:

    def setup_logging(*args: Any, **kwargs: Any) -> None:
        _ = (args, kwargs)
        return None


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(*args: Any, **kwargs: Any):
        _ = (args, kwargs)

        def decorator(fn: Any) -> Any:
            return fn

        return decorator


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(*args: Any, **kwargs: Any):
        _ = (args, kwargs)

        def decorator(fn: Any) -> Any:
            return fn

        return decorator


_ = setup_logging(format="json")
logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "job-requests")
STATUS_CONTAINER = os.getenv("JOB_STATUS_CONTAINER", "job-status")


class JobSubmissionRequest(BaseModel):
    job_type: str = Field(..., min_length=1, description="Logical job type")
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    payload: dict[str, Any] = Field(default_factory=dict, description="Job-specific payload")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _blob_service_client() -> BlobServiceClient:
    connection_string = os.environ["AzureWebJobsStorage"]
    return BlobServiceClient.from_connection_string(connection_string)


def _write_job_status(job_id: str, status_payload: dict[str, Any]) -> None:
    blob_client = _blob_service_client().get_blob_client(
        container=STATUS_CONTAINER,
        blob=f"{job_id}.json",
    )
    blob_client.upload_blob(json.dumps(status_payload), overwrite=True)


def _read_job_status(job_id: str) -> dict[str, Any] | None:
    blob_client = _blob_service_client().get_blob_client(
        container=STATUS_CONTAINER,
        blob=f"{job_id}.json",
    )
    if not blob_client.exists():
        return None
    return json.loads(blob_client.download_blob().readall())


def _json_response(payload: dict[str, Any], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="jobs", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Submit a queue-backed job",
    description="Validates input, stores an accepted job record, and enqueues work for background processing.",
    request_body=JobSubmissionRequest,
    response={202: dict[str, Any]},
    tags=["async-jobs"],
)
@validate_http(body=JobSubmissionRequest)
@app.queue_output(
    arg_name="job_message",
    queue_name=QUEUE_NAME,
    connection="AzureWebJobsStorage",
)
def submit_job(
    req: func.HttpRequest,
    body: JobSubmissionRequest,
    job_message: func.Out[str],
) -> func.HttpResponse:
    job_id = str(uuid4())
    submitted_at = _utc_now()
    submission = body.model_dump()
    status_url = f"{req.url.rstrip('/')}/{job_id}"

    accepted_status = {
        "job_id": job_id,
        "status": "accepted",
        "job_type": submission["job_type"],
        "customer_id": submission["customer_id"],
        "submitted_at": submitted_at,
        "updated_at": submitted_at,
        "status_url": status_url,
    }
    _write_job_status(job_id, accepted_status)

    queue_payload = {
        "job_id": job_id,
        "submitted_at": submitted_at,
        **submission,
    }
    job_message.set(json.dumps(queue_payload))

    logger.info(
        "Accepted queue-backed job",
        extra={
            "job_id": job_id,
            "job_type": submission["job_type"],
            "customer_id": submission["customer_id"],
            "queue_name": QUEUE_NAME,
        },
    )

    return _json_response(
        {
            "status": "accepted",
            "job_id": job_id,
            "status_url": status_url,
            "queue": QUEUE_NAME,
        },
        status_code=202,
    )


@app.route(route="jobs/{job_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Get queue-backed job status",
    description="Returns the latest stored status for a submitted job.",
    response={200: dict[str, Any], 404: dict[str, Any]},
    tags=["async-jobs"],
)
def get_job_status(req: func.HttpRequest) -> func.HttpResponse:
    job_id = req.route_params.get("job_id", "")
    status_payload = _read_job_status(job_id)
    if status_payload is None:
        return _json_response({"error": "Job not found.", "job_id": job_id}, status_code=404)
    return _json_response(status_payload, status_code=200)


@app.queue_trigger(
    arg_name="msg",
    queue_name=QUEUE_NAME,
    connection="AzureWebJobsStorage",
)
def process_job(msg: func.QueueMessage) -> None:
    job = json.loads(msg.get_body().decode("utf-8"))
    job_id = str(job["job_id"])
    started_at = _utc_now()

    logger.info(
        "Starting queue-backed job",
        extra={
            "job_id": job_id,
            "job_type": job.get("job_type"),
            "customer_id": job.get("customer_id"),
        },
    )

    _write_job_status(
        job_id,
        {
            "job_id": job_id,
            "status": "running",
            "job_type": job.get("job_type"),
            "customer_id": job.get("customer_id"),
            "submitted_at": job.get("submitted_at"),
            "started_at": started_at,
            "updated_at": started_at,
        },
    )

    completed_at = _utc_now()
    result = {
        "artifactUrl": f"https://example.invalid/jobs/{job_id}.json",
        "summary": f"Processed {job.get('job_type', 'job')} for {job.get('customer_id', 'unknown')}",
    }

    _write_job_status(
        job_id,
        {
            "job_id": job_id,
            "status": "completed",
            "job_type": job.get("job_type"),
            "customer_id": job.get("customer_id"),
            "submitted_at": job.get("submitted_at"),
            "started_at": started_at,
            "completed_at": completed_at,
            "updated_at": completed_at,
            "result": result,
        },
    )

    logger.info(
        "Completed queue-backed job",
        extra={
            "job_id": job_id,
            "job_type": job.get("job_type"),
            "customer_id": job.get("customer_id"),
        },
    )
