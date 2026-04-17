# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false

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


class ReportJobRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    operation: str = Field(default="rebuild-report", min_length=1)
    delay_seconds: int = Field(default=5, ge=0, le=30)


@app.route(route="jobs/reports", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Start a durable report job",
    description="Accepts work, returns 202, and provides the Durable statusQueryGetUri for polling.",
    request_body=ReportJobRequest,
    response={202: dict[str, Any]},
    tags=["async-jobs"],
)
@validate_http(body=ReportJobRequest)
@app.durable_client_input(client_name="client")
async def start_report_job(
    req: func.HttpRequest,
    body: ReportJobRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    payload = body.model_dump()
    instance_id = await client.start_new("report_job_orchestrator", None, payload)

    check_status = client.create_check_status_response(req, instance_id)
    management_payload = json.loads(check_status.get_body().decode("utf-8"))

    logger.info(
        "Accepted durable report job",
        extra={
            "instance_id": instance_id,
            "customer_id": payload["customer_id"],
            "operation": payload["operation"],
        },
    )

    response_payload = {
        "status": "accepted",
        "instanceId": instance_id,
        "statusQueryGetUri": management_payload["statusQueryGetUri"],
        "sendEventPostUri": management_payload.get("sendEventPostUri"),
        "terminatePostUri": management_payload.get("terminatePostUri"),
    }

    return func.HttpResponse(
        body=json.dumps(response_payload),
        status_code=202,
        mimetype="application/json",
        headers=dict(check_status.headers),
    )


@app.orchestration_trigger(context_name="context")
def report_job_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, dict[str, Any]]:
    job_request = context.get_input() or {}
    result = yield context.call_activity("generate_report_activity", job_request)
    return {
        "status": "completed",
        "instanceId": context.instance_id,
        "result": result,
    }


@app.activity_trigger(input_name="job_request")
def generate_report_activity(job_request: dict[str, Any]) -> dict[str, Any]:
    customer_id = str(job_request.get("customer_id", "unknown"))
    operation = str(job_request.get("operation", "rebuild-report"))
    delay_seconds = int(job_request.get("delay_seconds", 5))

    logger.info(
        "Starting report activity",
        extra={
            "customer_id": customer_id,
            "operation": operation,
            "delay_seconds": delay_seconds,
        },
    )

    time.sleep(delay_seconds)

    result = {
        "customerId": customer_id,
        "operation": operation,
        "artifactUrl": f"https://example.invalid/reports/{customer_id}/{operation}.json",
        "processedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    logger.info(
        "Completed report activity", extra={"customer_id": customer_id, "operation": operation}
    )
    return result
