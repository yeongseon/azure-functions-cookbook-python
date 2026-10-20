"""Regression coverage for #372: decode blob URL paths before constructing
storage clients.

Both blob_csv_to_table and blob_thumbnail_generator extracted a blob name
from urlparse(...).path and passed that still-percent-encoded name into
BlobClient.from_connection_string, which encodes it a second time. For a
real SDK-generated URL whose logical blob name is "Q1 report.csv", this
constructed a request URL ending in "Q1%2520report.csv" instead of
"Q1%20report.csv", addressing a different blob than the one Event Grid
reported.

Constructs only real azure.storage.blob.BlobClient objects to build and
verify URLs; no storage account or network I/O is involved.
"""

from __future__ import annotations

from azure.storage.blob import BlobClient

from tests._isolation import load_example_module

CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;AccountName=review;"
    "AccountKey=ZHVtbXk=;EndpointSuffix=core.windows.net"
)

SOURCE_NAMES = ("plain.csv", "Q1 report.csv", "percent%name.csv", "nested/path/report.csv")

RECIPES = (
    "blob-and-file-triggers/blob_csv_to_table",
    "blob-and-file-triggers/blob_thumbnail_generator",
)


def test_blob_parts_recovers_the_original_logical_blob_name() -> None:
    for recipe in RECIPES:
        module = load_example_module(recipe)
        for source_name in SOURCE_NAMES:
            original = BlobClient.from_connection_string(
                CONNECTION_STRING, container_name="uploads", blob_name=source_name
            )

            container, blob_name = module._blob_parts(original.url)
            reconstructed = BlobClient.from_connection_string(
                CONNECTION_STRING, container_name=container, blob_name=blob_name
            )

            assert blob_name == source_name
            assert reconstructed.url == original.url
            assert reconstructed.blob_name == source_name


def test_reconstructed_url_matches_sdk_from_blob_url_control() -> None:
    for recipe in RECIPES:
        module = load_example_module(recipe)
        for source_name in SOURCE_NAMES:
            original = BlobClient.from_connection_string(
                CONNECTION_STRING, container_name="uploads", blob_name=source_name
            )
            control = BlobClient.from_blob_url(original.url)

            _container, blob_name = module._blob_parts(original.url)

            assert blob_name == control.blob_name
