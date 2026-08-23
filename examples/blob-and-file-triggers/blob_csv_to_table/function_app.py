from __future__ import annotations

import csv
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
    parts = parsed.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Unexpected blob URL: {blob_url}")
    return parts[0], parts[1]


@app.function_name(name="blob_csv_to_table")
@app.event_grid_trigger(arg_name="event")
@with_context
def blob_csv_to_table(event: func.EventGridEvent, context: func.Context) -> None:
    data = event.get_json()
    container, blob_name = _blob_parts(str(data["url"]))

    from azure.data.tables import TableServiceClient
    from azure.storage.blob import BlobClient

    connection = os.environ["AzureWebJobsStorage"]
    table_name = os.getenv("CSV_TABLE_NAME", "CsvRows")
    blob_client = BlobClient.from_connection_string(
        connection, container_name=container, blob_name=blob_name
    )
    table_client = TableServiceClient.from_connection_string(connection).get_table_client(
        table_name
    )
    csv_text = blob_client.download_blob().readall().decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_text))

    processed = 0
    for index, row in enumerate(reader, start=1):
        entity = {"PartitionKey": blob_name.replace("/", "-"), "RowKey": str(index), **row}
        table_client.upsert_entity(entity=entity)
        processed += 1

    logger.info(
        "Loaded CSV blob into Table Storage",
        extra={"blob_name": blob_name, "table_name": table_name, "processed": processed},
    )
