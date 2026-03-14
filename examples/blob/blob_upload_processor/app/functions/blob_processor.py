from __future__ import annotations

import logging

import azure.functions as func

from app.services.blob_service import LARGE_BLOB_BYTES, process_blob

blob_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@blob_blueprint.blob_trigger(
    arg_name="myblob", path="uploads/{name}", connection="AzureWebJobsStorage"
)
def process_uploaded_blob(myblob: func.InputStream) -> None:
    blob_name = myblob.name or "unknown"
    blob_size = int(myblob.length or 0)
    blob_metadata = dict(getattr(myblob, "metadata", {}) or {})

    logger.info("Blob trigger fired for %s (size=%d bytes)", blob_name, blob_size)
    logger.info("Blob metadata: %s", blob_metadata)

    if blob_size == 0:
        logger.warning("Blob %s is empty. Skipping processing.", blob_name)
        return

    if blob_size > LARGE_BLOB_BYTES:
        logger.warning(
            "Blob %s is large (%d bytes). Consider chunked processing.",
            blob_name,
            blob_size,
        )

    blob_bytes = myblob.read()
    result = process_blob(
        blob_name=blob_name, blob_size=blob_size, metadata=blob_metadata, data=blob_bytes
    )
    logger.info("Blob processing completed for %s: %s", blob_name, result)
