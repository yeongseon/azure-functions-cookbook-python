from __future__ import annotations

import io
import os
from urllib.parse import urlparse

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp()


def _blob_parts(blob_url: str) -> tuple[str, str]:
    parsed = urlparse(blob_url)
    path_parts = parsed.path.lstrip("/").split("/", 1)
    if len(path_parts) != 2:
        raise ValueError(f"Unexpected blob URL: {blob_url}")
    return path_parts[0], path_parts[1]


def _generate_thumbnail(source_bytes: bytes) -> bytes:
    from PIL import Image

    image = Image.open(io.BytesIO(source_bytes))
    image.thumbnail((320, 320))
    buffer = io.BytesIO()
    image.save(buffer, format=image.format or "PNG")
    return buffer.getvalue()


@app.function_name(name="blob_thumbnail_generator")
@app.event_grid_trigger(arg_name="event")
@with_context
def blob_thumbnail_generator(event: func.EventGridEvent) -> None:
    data = event.get_json()
    blob_url = str(data["url"])
    source_container, blob_name = _blob_parts(blob_url)
    output_container = os.getenv("THUMBNAIL_CONTAINER", "thumbnails")

    from azure.storage.blob import BlobClient

    connection = os.environ["AzureWebJobsStorage"]
    source_blob = BlobClient.from_connection_string(
        connection, container_name=source_container, blob_name=blob_name
    )
    output_blob = BlobClient.from_connection_string(
        connection, container_name=output_container, blob_name=blob_name
    )

    thumbnail_bytes = _generate_thumbnail(source_blob.download_blob().readall())
    output_blob.upload_blob(thumbnail_bytes, overwrite=True)
    logger.info(
        "Generated thumbnail from blob event",
        extra={
            "source_container": source_container,
            "blob_name": blob_name,
            "output_container": output_container,
        },
    )
