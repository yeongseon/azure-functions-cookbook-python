from __future__ import annotations


def process_blob_event(name: str, size: int) -> str:
    return f"Blob processing (Event Grid) complete for {name} ({size} bytes)"
