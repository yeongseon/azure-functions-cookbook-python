"""Blob trigger (polling mode) that validates and processes uploaded blobs."""

from __future__ import annotations

import hashlib
import logging

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)

LARGE_BLOB_BYTES = 10 * 1024 * 1024


@app.blob_trigger(arg_name="myblob", path="uploads/{name}", connection="AzureWebJobsStorage")
def process_uploaded_blob(myblob: func.InputStream) -> None:
    """Process uploaded blobs and log details for monitoring and troubleshooting."""
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
    result = _process_blob(
        blob_name=blob_name, blob_size=blob_size, metadata=blob_metadata, data=blob_bytes
    )
    logger.info("Blob processing completed for %s: %s", blob_name, result)


def _process_blob(
    blob_name: str,
    blob_size: int,
    metadata: dict[str, str],
    data: bytes,
) -> str:
    """Simulate blob processing by calculating a checksum and summary."""
    checksum = hashlib.sha256(data).hexdigest()[:16]
    metadata_keys = sorted(metadata.keys())
    return (
        f"Processed '{blob_name}' ({blob_size} bytes), "
        f"metadata_keys={metadata_keys}, checksum={checksum}"
    )
