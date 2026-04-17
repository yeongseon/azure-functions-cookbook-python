from __future__ import annotations


def process_queue_message(body: str) -> str:
    return f"Received queue message through StorageConnection: {body}"
