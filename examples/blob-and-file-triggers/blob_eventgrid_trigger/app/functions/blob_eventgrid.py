from __future__ import annotations

import logging

import azure.functions as func

from app.services.eventgrid_service import process_blob_event

blob_eventgrid_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@blob_eventgrid_blueprint.blob_trigger(
    arg_name="myblob",
    path="events/{name}",
    connection="AzureWebJobsStorage",
    source=func.BlobSource.EVENT_GRID,
)
def process_blob_eventgrid(myblob: func.InputStream) -> None:
    blob_name = myblob.name or "unknown"
    blob_size = int(myblob.length or 0)
    logger.info("Event Grid blob trigger received %s (%d bytes)", blob_name, blob_size)
    summary = process_blob_event(name=blob_name, size=blob_size)
    logger.info(summary)
