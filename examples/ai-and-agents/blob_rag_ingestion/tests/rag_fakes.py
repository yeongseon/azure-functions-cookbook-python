"""Offline fakes: no Azure, no network, no Functions host."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


class FakeEmbedder:
    """Deterministic 4-dimension vectors derived from the text; records every call."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[b / 255 for b in hashlib.sha256(t.encode()).digest()[:4]] for t in texts]


@dataclass
class FakeStore:
    """In-memory index keyed by chunk id; mirrors merge-or-upload and delete semantics."""

    docs: dict[str, dict[str, object]] = field(default_factory=dict)
    upsert_calls: int = 0
    delete_calls: int = 0

    def existing_chunks(self, source_id: str) -> dict[str, str]:
        return {
            key: str(doc["content_hash"])
            for key, doc in self.docs.items()
            if doc["source_id"] == source_id
        }

    def upsert(self, documents: list[dict[str, object]]) -> None:
        self.upsert_calls += 1
        for doc in documents:
            self.docs[str(doc["id"])] = {**self.docs.get(str(doc["id"]), {}), **doc}

    def delete(self, chunk_ids: list[str]) -> None:
        self.delete_calls += 1
        for chunk_id in chunk_ids:
            self.docs.pop(chunk_id, None)
