from __future__ import annotations

import json
import os
from uuid import uuid4

import azure.functions as func

try:
    from pydantic import BaseModel, Field
except ImportError:

    class BaseModel:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, object]:
            return self.__dict__.copy()

    def Field(default: object = None, **_: object) -> object:
        return default


from azure_functions_logging import get_logger, setup_logging, with_context
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class ClaimCheckRequest(BaseModel):
    payload_type: str = Field(..., description="Business message type")
    payload: dict[str, object] = Field(..., description="Large JSON payload stored in Blob")


@app.route(route="claim-check/enqueue", methods=["POST"])
@with_context
@openapi(
    summary="Create claim check",
    tags=["Messaging"],
    route="/api/claim-check/enqueue",
    method="post",
)
@app.queue_output(
    arg_name="claim_queue", queue_name="claim-check-jobs", connection="AzureWebJobsStorage"
)
@validate_http(body=ClaimCheckRequest)
def enqueue_claim_check(
    req: func.HttpRequest,
    body: ClaimCheckRequest,
    claim_queue: func.Out[str], context: func.Context,
) -> func.HttpResponse:
    from azure.storage.blob import BlobClient

    blob_name = f"claim-check/{uuid4()}.json"
    connection = os.environ["AzureWebJobsStorage"]
    container_name = os.getenv("CLAIM_CHECK_CONTAINER", "claim-check-payloads")
    blob_client = BlobClient.from_connection_string(
        connection, container_name=container_name, blob_name=blob_name
    )
    blob_client.upload_blob(json.dumps(body.payload), overwrite=True)

    claim_reference = {
        "claim_id": str(uuid4()),
        "payload_type": body.payload_type,
        "container": container_name,
        "blob_name": blob_name,
    }
    claim_queue.set(json.dumps(claim_reference))
    logger.info("Stored claim-check payload and queued reference", extra=claim_reference)
    return func.HttpResponse(
        body=json.dumps({"status": "accepted", **claim_reference}),
        status_code=202,
        mimetype="application/json",
    )


@app.function_name(name="process_claim_check")
@app.queue_trigger(arg_name="msg", queue_name="claim-check-jobs", connection="AzureWebJobsStorage")
@with_context
def process_claim_check(msg: func.QueueMessage, context: func.Context) -> None:
    from azure.storage.blob import BlobClient

    reference = json.loads(msg.get_body().decode("utf-8"))
    connection = os.environ["AzureWebJobsStorage"]
    blob_client = BlobClient.from_connection_string(
        connection, container_name=reference["container"], blob_name=reference["blob_name"]
    )
    payload = json.loads(blob_client.download_blob().readall())
    logger.info(
        "Processed claim-check payload",
        extra={
            "claim_id": reference["claim_id"],
            "payload_type": reference["payload_type"],
            "payload_keys": sorted(payload.keys()),
        },
    )
