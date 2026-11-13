"""Triggers: Blob (Event Grid source) indexes a blob; an Event Grid trigger removes its chunks."""

from __future__ import annotations

import logging
from functools import lru_cache

import azure.functions as func

from app.services.azure_clients import Services, build_services
from app.services.ingestion import (
    MAX_BLOB_BYTES,
    RejectedDocumentError,
    delete_document,
    ingest_document,
    parse_blob_deleted_subject,
    parse_blob_path,
    source_id_for,
)

rag_ingestion_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_services() -> Services:
    """Build the live clients once per worker; tests replace this function."""
    return build_services()


@rag_ingestion_blueprint.blob_trigger(
    arg_name="blob",
    path="rag-documents/{name}",
    connection="AzureWebJobsStorage",
    source=func.BlobSource.EVENT_GRID,
)
def index_blob(blob: func.InputStream, context: func.Context) -> None:
    """Index one uploaded or overwritten blob.

    The Event Grid-sourced trigger can still deliver the same blob more than once, so indexing is
    idempotent by construction (stable chunk ids, merge-or-upload). Only blob and chunk counts are
    logged, never document text.
    """
    invocation = context.invocation_id
    try:
        container, blob_name = parse_blob_path(blob.name or "")
        # Read one byte past the limit so an oversized blob is detected without loading all of it.
        data = blob.read(MAX_BLOB_BYTES + 1)
        services = get_services()
        outcome = ingest_document(
            container, blob_name, data, embedder=services.embedder, store=services.store
        )
    except RejectedDocumentError as exc:
        logger.warning("Rejected blob (invocation=%s): %s", invocation, exc)
        return
    logger.info(
        "Indexed blob source=%s chunks=%d embedded=%d reused=%d stale_deleted=%d invocation=%s",
        outcome.source_id,
        outcome.chunks,
        outcome.embedded,
        outcome.reused,
        outcome.stale_deleted,
        invocation,
    )


@rag_ingestion_blueprint.event_grid_trigger(arg_name="event")
def remove_deleted_blob(event: func.EventGridEvent, context: func.Context) -> None:
    """Delete the chunks of a blob after a ``Microsoft.Storage.BlobDeleted`` event.

    Ordering is not handled: Event Grid may deliver events out of order, so a delete that arrives
    after a re-upload of the same name would remove the fresh chunks. See the pattern page.
    """
    parsed = parse_blob_deleted_subject(event.event_type, event.subject or "")
    if parsed is None:
        logger.info("Ignored event type=%s invocation=%s", event.event_type, context.invocation_id)
        return
    container, blob_name = parsed
    deleted = delete_document(container, blob_name, store=get_services().store)
    logger.info(
        "Removed chunks source=%s deleted=%d invocation=%s",
        source_id_for(container, blob_name),
        deleted,
        context.invocation_id,
    )
