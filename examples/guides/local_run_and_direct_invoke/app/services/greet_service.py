"""Service layer for greeting operations."""

from __future__ import annotations

import json
from typing import Any


def extract_name(
    params: dict[str, str],
    body: bytes,
    content_type: str,
) -> str | None:
    """Extract 'name' from query params or JSON body."""
    name = params.get("name")
    if name:
        return name

    if "application/json" in content_type:
        try:
            payload: dict[str, Any] = json.loads(body)
            return str(payload.get("name", "")).strip() or None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    return None


def build_greeting(name: str) -> dict[str, str]:
    """Build a greeting payload.

    Args:
        name: The name to greet.

    Returns:
        Dict with greeting message.
    """
    return {"greeting": f"Hello, {name}!"}
