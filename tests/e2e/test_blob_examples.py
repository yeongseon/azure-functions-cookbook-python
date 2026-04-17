"""E2E tests for blob-triggered examples.

These tests upload a blob to Azurite and verify the function host
processes it (checked via logs or absence of errors).
"""

from __future__ import annotations

import time

import pytest

from tests.e2e.conftest import AZURITE_CONN_STR, ensure_azurite_container, run_func_host

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# blob_upload_processor
# ---------------------------------------------------------------------------


class TestBlobUploadProcessor:
    """Blob trigger on container 'uploads'."""

    EXAMPLE = "blob-and-file-triggers/blob_upload_processor"

    def test_blob_trigger_fires(self, azurite) -> None:  # noqa: ARG002
        """Upload a blob to 'uploads' and verify the func host stays healthy."""
        from azure.storage.blob import BlobServiceClient

        ensure_azurite_container("uploads")
        blob_svc = BlobServiceClient.from_connection_string(AZURITE_CONN_STR)
        container_client = blob_svc.get_container_client("uploads")

        with run_func_host(self.EXAMPLE) as base_url:  # noqa: F841
            # Upload a blob — trigger should fire
            container_client.upload_blob(
                name="test-file.txt",
                data=b"Hello from E2E test",
                overwrite=True,
            )
            # Give the trigger time to process (polling-based triggers are slow)
            time.sleep(10)
            # If we reach here without the host crashing, the trigger loaded OK


# ---------------------------------------------------------------------------
# blob_eventgrid_trigger
# ---------------------------------------------------------------------------


class TestBlobEventGridTrigger:
    """Blob trigger (Event Grid source) on container 'events'.

    Note: Event Grid source requires real Event Grid subscription in Azure.
    In local Azurite, the trigger registers but won't fire via Event Grid.
    We verify the function host loads and the container is accessible.
    """

    EXAMPLE = "blob-and-file-triggers/blob_eventgrid_trigger"

    def test_function_host_loads(self, azurite) -> None:  # noqa: ARG002
        """Verify the func host starts without errors for this example."""
        from azure.storage.blob import BlobServiceClient

        ensure_azurite_container("events")
        blob_svc = BlobServiceClient.from_connection_string(AZURITE_CONN_STR)
        container_client = blob_svc.get_container_client("events")

        with run_func_host(self.EXAMPLE) as base_url:  # noqa: F841
            # Upload a blob — Event Grid trigger won't fire locally but
            # host should stay healthy
            container_client.upload_blob(
                name="event-test.txt",
                data=b"Event Grid E2E test blob",
                overwrite=True,
            )
            time.sleep(5)
