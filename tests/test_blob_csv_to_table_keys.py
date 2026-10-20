"""Regression tests for #373: blob-to-table PartitionKey construction must
preserve distinct blob identities instead of colliding on a naive
``/`` -> ``-`` replace.

No Azure services are contacted: ``BlobClient``/``TableServiceClient`` are
patched with in-process fakes, matching the issue's own offline
reproduction methodology.
"""

from __future__ import annotations

from datetime import UTC, datetime
import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import azure.functions as func

from tests._isolation import load_example_module

EXAMPLE_PATH = "blob-and-file-triggers/blob_csv_to_table"


def _invocation_context(name: str = "review") -> SimpleNamespace:
    return SimpleNamespace(
        invocation_id="offline-review",
        function_name=name,
        trace_context=SimpleNamespace(trace_parent=None, trace_state=None),
    )


class _FakeTable:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}

    def upsert_entity(self, *, entity: dict[str, Any]) -> None:
        self.rows[(entity["PartitionKey"], entity["RowKey"])] = dict(entity)


def _run_handler_for_blobs(blobs: dict[str, bytes]) -> _FakeTable:
    from azure.data.tables import TableServiceClient
    from azure.storage.blob import BlobClient

    module = load_example_module(EXAMPLE_PATH)
    handler = module.blob_csv_to_table.build().get_user_function()
    table = _FakeTable()
    service = SimpleNamespace(get_table_client=lambda name: table)

    def blob_factory(connection: str, *, container_name: str, blob_name: str) -> SimpleNamespace:
        assert container_name == "uploads"
        data = blobs[blob_name]
        return SimpleNamespace(download_blob=lambda: SimpleNamespace(readall=lambda: data))

    with (
        patch.dict(os.environ, {"AzureWebJobsStorage": "offline-fake"}),
        patch.object(BlobClient, "from_connection_string", side_effect=blob_factory),
        patch.object(TableServiceClient, "from_connection_string", return_value=service),
    ):
        for index, name in enumerate(blobs):
            event = func.EventGridEvent(
                id=str(index),
                data={"url": f"https://review.blob.core.windows.net/uploads/{name}"},
                topic="review",
                subject=f"/uploads/{name}",
                event_type="Microsoft.Storage.BlobCreated",
                event_time=datetime(2026, 1, 1, tzinfo=UTC),
                data_version="1.0",
            )
            handler(event=event, context=_invocation_context("blob_csv_to_table"))

    return table


def test_nested_and_flat_blob_names_do_not_collide() -> None:
    """``reports/2026.csv`` and ``reports-2026.csv`` both naively map to
    ``reports-2026.csv`` under a '/' -> '-' replace. They must produce
    distinct PartitionKeys and both rows must survive (#373)."""
    table = _run_handler_for_blobs(
        {
            "reports/2026.csv": b"name,value\nalpha,1\n",
            "reports-2026.csv": b"name,value\nbeta,2\n",
        }
    )

    assert len(table.rows) == 2
    names = {row["name"] for row in table.rows.values()}
    assert names == {"alpha", "beta"}


def test_repeated_delivery_of_same_blob_stays_idempotent() -> None:
    """Redelivering the same unchanged blob must still upsert to the same
    (PartitionKey, RowKey) pair, not create a duplicate row."""
    from azure.data.tables import TableServiceClient
    from azure.storage.blob import BlobClient

    module = load_example_module(EXAMPLE_PATH)
    handler = module.blob_csv_to_table.build().get_user_function()
    table = _FakeTable()
    service = SimpleNamespace(get_table_client=lambda name: table)
    data = b"name,value\nalpha,1\n"

    def blob_factory(connection: str, *, container_name: str, blob_name: str) -> SimpleNamespace:
        return SimpleNamespace(download_blob=lambda: SimpleNamespace(readall=lambda: data))

    with (
        patch.dict(os.environ, {"AzureWebJobsStorage": "offline-fake"}),
        patch.object(BlobClient, "from_connection_string", side_effect=blob_factory),
        patch.object(TableServiceClient, "from_connection_string", return_value=service),
    ):
        for _ in range(2):
            event = func.EventGridEvent(
                id="redelivery",
                data={"url": "https://review.blob.core.windows.net/uploads/reports/2026.csv"},
                topic="review",
                subject="/uploads/reports/2026.csv",
                event_type="Microsoft.Storage.BlobCreated",
                event_time=datetime(2026, 1, 1, tzinfo=UTC),
                data_version="1.0",
            )
            handler(event=event, context=_invocation_context("blob_csv_to_table"))

    assert len(table.rows) == 1


def test_nested_path_partition_key_has_no_forbidden_characters() -> None:
    """Azure Table Storage forbids '/', '\\\\', '#', '?' in PartitionKey;
    the percent-encoded key for a nested blob path must contain none of
    them."""
    table = _run_handler_for_blobs({"reports/2026.csv": b"name,value\nalpha,1\n"})

    (partition_key, _row_key), _row = next(iter(table.rows.items()))
    for forbidden in ("/", "\\", "#", "?"):
        assert forbidden not in partition_key
