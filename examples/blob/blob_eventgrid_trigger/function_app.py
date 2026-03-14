"""Blob trigger using Event Grid notifications instead of storage polling."""

from __future__ import annotations

import logging

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.blob_trigger(
    arg_name="myblob",
    path="events/{name}",
    connection="AzureWebJobsStorage",
    source="EventGrid",
)
def process_blob_eventgrid(myblob: func.InputStream) -> None:
    """Handle blob events with low-latency delivery.

    Event Grid is preferred over polling because notifications are pushed as soon as
    the blob changes, reducing detection latency and storage list/scan overhead.

    Note: this trigger requires Azure Functions Storage extension 5.x or newer and
    an Event Grid subscription for the storage account.
    """
    blob_name = myblob.name
    blob_size = int(myblob.length)
    logger.info("Event Grid blob trigger received %s (%d bytes)", blob_name, blob_size)
    logger.info("Blob processing (Event Grid) complete for %s", blob_name)
