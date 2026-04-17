from __future__ import annotations

import hashlib

LARGE_BLOB_BYTES = 10 * 1024 * 1024


def process_blob(
    blob_name: str,
    blob_size: int,
    metadata: dict[str, str],
    data: bytes,
) -> str:
    checksum = hashlib.sha256(data).hexdigest()[:16]
    metadata_keys = sorted(metadata.keys())
    return (
        f"Processed '{blob_name}' ({blob_size} bytes), "
        f"metadata_keys={metadata_keys}, checksum={checksum}"
    )
