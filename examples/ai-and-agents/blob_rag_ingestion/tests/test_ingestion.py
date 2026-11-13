from __future__ import annotations

import re

import pytest
from rag_fakes import FakeEmbedder, FakeStore

from app.services import ingestion
from app.services.ingestion import (
    RejectedDocumentError,
    chunk_id_for,
    delete_document,
    ingest_document,
    parse_blob_deleted_subject,
    parse_blob_path,
    source_id_for,
    split_text,
)

KEY_ALPHABET = re.compile(r"[A-Za-z0-9_\-=]{1,1024}")


def _text(paragraphs: int) -> bytes:
    return " ".join(f"sentence-{n}" for n in range(paragraphs * 60)).encode()


def test_ids_are_stable_and_valid_search_keys() -> None:
    odd_name = "folder/résumé #1 (final).md"
    first = chunk_id_for(source_id_for("rag-documents", odd_name), 3)
    assert first == chunk_id_for(source_id_for("rag-documents", odd_name), 3)
    assert KEY_ALPHABET.fullmatch(first)
    assert source_id_for("c1", "x.md") != source_id_for("c2", "x.md")


def test_split_text_is_deterministic_with_overlap() -> None:
    text = "abcdefghij" * 30
    chunks = split_text(text, size=100, overlap=20)
    assert chunks == split_text(text, size=100, overlap=20)
    assert chunks[0][-20:] == chunks[1][:20]
    assert split_text("   ") == []


def test_split_text_rejects_bad_window() -> None:
    with pytest.raises(ValueError):
        split_text("x", size=10, overlap=10)
    with pytest.raises(ValueError):
        split_text("x", size=0, overlap=0)


def test_ingest_indexes_every_chunk_with_vectors_and_metadata() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    outcome = ingest_document(
        "rag-documents", "guides/a.md", _text(3), embedder=embedder, store=store
    )
    assert outcome.chunks == len(store.docs) > 1
    assert outcome.embedded == outcome.chunks and outcome.reused == 0
    doc = store.docs[chunk_id_for(outcome.source_id, 0)]
    assert doc["title"] == "a.md"
    assert doc["source"] == "rag-documents/guides/a.md"
    assert len(doc["content_vector"]) == 4  # type: ignore[arg-type]
    assert set(doc) == {
        "id",
        "source_id",
        "source",
        "title",
        "chunk_index",
        "content_hash",
        "content",
        "content_vector",
    }


def test_reprocessing_same_blob_is_idempotent_and_skips_embedding() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    data = _text(3)
    first = ingest_document("c", "a.md", data, embedder=embedder, store=store)
    snapshot = {k: dict(v) for k, v in store.docs.items()}
    embed_calls = len(embedder.calls)

    second = ingest_document("c", "a.md", data, embedder=embedder, store=store)

    assert store.docs == snapshot
    assert len(embedder.calls) == embed_calls  # nothing re-embedded
    assert (second.embedded, second.reused, second.stale_deleted) == (0, first.chunks, 0)
    assert store.upsert_calls == 1  # the second run had nothing to write


def test_update_reembeds_only_changed_chunks_and_removes_stale_ones() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    long_version = _text(4)
    first = ingest_document("c", "a.md", long_version, embedder=embedder, store=store)
    assert first.chunks > 2

    short_version = long_version[: len(long_version) // 3]
    second = ingest_document("c", "a.md", short_version, embedder=embedder, store=store)

    assert second.stale_deleted == first.chunks - second.chunks > 0
    assert len(store.docs) == second.chunks
    assert second.embedded <= 1  # only the truncated tail chunk differs


def test_other_sources_are_never_touched() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    ingest_document("c", "keep.md", _text(2), embedder=embedder, store=store)
    kept = dict(store.docs)
    ingest_document("c", "other.md", _text(2), embedder=embedder, store=store)
    delete_document("c", "other.md", store=store)
    assert store.docs == kept


def test_delete_document_removes_all_chunks_and_is_repeatable() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    outcome = ingest_document("c", "a.md", _text(2), embedder=embedder, store=store)
    assert delete_document("c", "a.md", store=store) == outcome.chunks
    assert store.docs == {}
    assert delete_document("c", "a.md", store=store) == 0  # duplicate delete event is harmless
    assert store.delete_calls == 1


def test_empty_blob_removes_previous_chunks() -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    ingest_document("c", "a.md", _text(2), embedder=embedder, store=store)
    outcome = ingest_document("c", "a.md", b"  \n", embedder=embedder, store=store)
    assert outcome.chunks == 0 and store.docs == {}


def test_embeddings_are_batched(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "EMBED_BATCH_SIZE", 2)
    store, embedder = FakeStore(), FakeEmbedder()
    outcome = ingest_document("c", "a.md", _text(3), embedder=embedder, store=store)
    assert all(len(call) <= 2 for call in embedder.calls)
    assert sum(len(call) for call in embedder.calls) == outcome.chunks


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"x" * (ingestion.MAX_BLOB_BYTES + 1), "exceeds"),
        (b"\xff\xfe\x00bad", "UTF-8"),
    ],
)
def test_permanent_problems_are_rejected_before_any_client_call(data: bytes, message: str) -> None:
    store, embedder = FakeStore(), FakeEmbedder()
    with pytest.raises(RejectedDocumentError, match=message):
        ingest_document("c", "a.md", data, embedder=embedder, store=store)
    assert embedder.calls == [] and store.upsert_calls == 0


def test_too_many_chunks_is_rejected_without_partial_indexing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingestion, "MAX_CHUNKS_PER_BLOB", 2)
    store, embedder = FakeStore(), FakeEmbedder()
    with pytest.raises(RejectedDocumentError, match="more than 2 chunks"):
        ingest_document("c", "a.md", _text(3), embedder=embedder, store=store)
    assert store.docs == {} and embedder.calls == []


def test_embedder_failure_propagates_and_leaves_index_unchanged() -> None:
    class Boom(FakeEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            raise TimeoutError("transient")

    store = FakeStore()
    with pytest.raises(TimeoutError):
        ingest_document("c", "a.md", _text(2), embedder=Boom(), store=store)
    assert store.docs == {}


def test_wrong_vector_count_is_an_error() -> None:
    class Short(FakeEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            return []

    with pytest.raises(RuntimeError, match="different number"):
        ingest_document("c", "a.md", _text(1), embedder=Short(), store=FakeStore())


def test_retry_after_partial_failure_converges() -> None:
    """If the stale-delete step fails, a rerun finishes the job without duplicating chunks."""

    class FlakyStore(FakeStore):
        fail_delete = True

        def delete(self, chunk_ids: list[str]) -> None:
            if self.fail_delete:
                raise ConnectionError("transient")
            super().delete(chunk_ids)

    store, embedder = FlakyStore(), FakeEmbedder()
    long_version = _text(4)
    ingest_document("c", "a.md", long_version, embedder=embedder, store=store)
    short_version = long_version[: len(long_version) // 3]
    with pytest.raises(ConnectionError):
        ingest_document("c", "a.md", short_version, embedder=embedder, store=store)
    store.fail_delete = False
    outcome = ingest_document("c", "a.md", short_version, embedder=embedder, store=store)
    assert len(store.docs) == outcome.chunks


def test_parse_blob_path() -> None:
    assert parse_blob_path("rag-documents/a/b.md") == ("rag-documents", "a/b.md")
    for bad in ("", "no-slash", "/x", "c/"):
        with pytest.raises(RejectedDocumentError):
            parse_blob_path(bad)


def test_parse_blob_deleted_subject() -> None:
    subject = "/blobServices/default/containers/rag-documents/blobs/a/b.md"
    assert parse_blob_deleted_subject("Microsoft.Storage.BlobDeleted", subject) == (
        "rag-documents",
        "a/b.md",
    )
    assert parse_blob_deleted_subject("Microsoft.Storage.BlobCreated", subject) is None
    assert parse_blob_deleted_subject("Microsoft.Storage.BlobDeleted", "/other") is None
    assert (
        parse_blob_deleted_subject(
            "Microsoft.Storage.BlobDeleted", "/blobServices/default/containers/c/blobs/"
        )
        is None
    )
