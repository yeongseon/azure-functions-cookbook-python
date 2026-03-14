from __future__ import annotations

_seen_ids: set[str] = set()


def is_duplicate(dedupe_id: str) -> bool:
    return dedupe_id in _seen_ids


def mark_processed(dedupe_id: str) -> None:
    _seen_ids.add(dedupe_id)
