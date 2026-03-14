from __future__ import annotations

from typing import Any


def process_change(change: dict[str, Any]) -> str:
    """Simulate downstream handling for one changed document."""
    document_id = str(change.get("id", "unknown-id"))
    category = str(change.get("category", "uncategorized"))
    return f"id={document_id} category={category} status=synced"
