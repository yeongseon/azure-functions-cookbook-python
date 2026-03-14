from __future__ import annotations

from app.services.blob_service import process_blob


def test_process_blob_returns_checksum_summary() -> None:
    result = process_blob(
        blob_name="uploads/sample.txt",
        blob_size=3,
        metadata={"source": "unit-test"},
        data=b"abc",
    )
    assert result == (
        "Processed 'uploads/sample.txt' (3 bytes), "
        "metadata_keys=['source'], checksum=ba7816bf8f01cfea"
    )
