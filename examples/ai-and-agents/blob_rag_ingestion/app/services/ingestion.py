"""Blob-to-index ingestion logic with injected clients.

Nothing here talks to Azure. ``Embedder`` and ``ChunkStore`` are protocols so the same code runs
against Azure OpenAI and Azure AI Search in production and against in-memory fakes in tests.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

# Local bounds chosen for a readable sample; tune them for your model and index.
MAX_BLOB_BYTES = 1_000_000
MAX_CHUNKS_PER_BLOB = 200
CHUNK_CHARS = 1_000
CHUNK_OVERLAP_CHARS = 100
EMBED_BATCH_SIZE = 16


class RejectedDocumentError(ValueError):
    """The blob can never be indexed as-is (too large, not UTF-8, too many chunks).

    Retrying will not help, so the trigger logs and drops it instead of re-raising, which would
    only burn the host's blob retries and land a poison message in ``webjobs-blobtrigger-poison``.
    """


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order."""
        ...


class ChunkStore(Protocol):
    def existing_chunks(self, source_id: str) -> dict[str, str]:
        """Return ``{chunk id: chunk content hash}`` currently indexed for ``source_id``."""
        ...

    def upsert(self, documents: list[dict[str, object]]) -> None:
        """Merge-or-upload ``documents`` by their ``id`` key; raise if any document fails."""
        ...

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete the chunks with these ids."""
        ...


@dataclass(frozen=True)
class IngestOutcome:
    source_id: str
    chunks: int
    embedded: int
    reused: int
    stale_deleted: int


def source_id_for(container: str, blob_name: str) -> str:
    """Stable id for a blob path.

    The hash keeps the id inside Azure AI Search's document-key alphabet (letters, digits, dash,
    underscore, equal sign) whatever characters the blob name contains.
    """
    return hashlib.sha256(f"{container}/{blob_name}".encode()).hexdigest()[:32]


def chunk_id_for(source_id: str, index: int) -> str:
    return f"{source_id}-{index:05d}"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def split_text(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Fixed-window chunking: deterministic, so equal input always yields equal chunk ids."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("size must be positive and 0 <= overlap < size")
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        piece = text[start : start + size].strip()
        if piece:
            chunks.append(piece)
        start += size - overlap
    return chunks


def parse_blob_path(path: str) -> tuple[str, str]:
    """Split a blob trigger name (``container/blob/name.md``) into container and blob name."""
    container, _, blob_name = path.partition("/")
    if not container or not blob_name:
        raise RejectedDocumentError("blob path must look like 'container/blob-name'")
    return container, blob_name


def parse_blob_deleted_subject(event_type: str, subject: str) -> tuple[str, str] | None:
    """Return ``(container, blob name)`` for a ``Microsoft.Storage.BlobDeleted`` event.

    Event Grid documents the subject as ``/blobServices/default/containers/<c>/blobs/<name>``.
    Anything else returns ``None``. The subject is used as-is: this sample has not verified how
    names with spaces or non-ASCII characters are encoded in it, so test that before relying on
    deletes in production.
    """
    prefix = "/blobServices/default/containers/"
    if event_type != "Microsoft.Storage.BlobDeleted" or not subject.startswith(prefix):
        return None
    container, sep, blob_name = subject[len(prefix) :].partition("/blobs/")
    if not sep or not container or not blob_name:
        return None
    return container, blob_name


def ingest_document(
    container: str,
    blob_name: str,
    data: bytes,
    *,
    embedder: Embedder,
    store: ChunkStore,
) -> IngestOutcome:
    """Chunk, embed and index one blob; safe to run again for the same or an updated blob.

    Order matters for failure safety: new chunks are upserted first and stale ones deleted last,
    so an interruption leaves old plus new chunks (never a gap) and a retry converges.
    """
    if len(data) > MAX_BLOB_BYTES:
        raise RejectedDocumentError(f"blob exceeds {MAX_BLOB_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RejectedDocumentError("blob is not UTF-8 text") from exc

    pieces = split_text(text)
    if len(pieces) > MAX_CHUNKS_PER_BLOB:
        raise RejectedDocumentError(f"blob needs more than {MAX_CHUNKS_PER_BLOB} chunks")

    source_id = source_id_for(container, blob_name)
    existing = store.existing_chunks(source_id)
    title = blob_name.rsplit("/", 1)[-1]

    wanted: list[tuple[str, str, str, int]] = []  # (chunk id, text, text hash, index)
    for index, piece in enumerate(pieces):
        wanted.append((chunk_id_for(source_id, index), piece, content_hash(piece), index))

    # A chunk whose id and text hash already match the index is not embedded again.
    to_embed = [item for item in wanted if existing.get(item[0]) != item[2]]
    documents: list[dict[str, object]] = []
    for offset in range(0, len(to_embed), EMBED_BATCH_SIZE):
        batch = to_embed[offset : offset + EMBED_BATCH_SIZE]
        vectors = embedder.embed([item[1] for item in batch])
        if len(vectors) != len(batch):
            raise RuntimeError("embedder returned a different number of vectors than inputs")
        for (chunk_id, piece, piece_hash, index), vector in zip(batch, vectors, strict=True):
            documents.append(
                {
                    "id": chunk_id,
                    "source_id": source_id,
                    "source": f"{container}/{blob_name}",
                    "title": title,
                    "chunk_index": index,
                    "content_hash": piece_hash,
                    "content": piece,
                    "content_vector": vector,
                }
            )
    if documents:
        store.upsert(documents)

    keep = {item[0] for item in wanted}
    stale = sorted(chunk_id for chunk_id in existing if chunk_id not in keep)
    if stale:
        store.delete(stale)

    return IngestOutcome(
        source_id=source_id,
        chunks=len(wanted),
        embedded=len(documents),
        reused=len(wanted) - len(documents),
        stale_deleted=len(stale),
    )


def delete_document(container: str, blob_name: str, *, store: ChunkStore) -> int:
    """Remove every chunk of a deleted blob; returns how many chunks were deleted."""
    source_id = source_id_for(container, blob_name)
    chunk_ids = sorted(store.existing_chunks(source_id))
    if chunk_ids:
        store.delete(chunk_ids)
    return len(chunk_ids)
