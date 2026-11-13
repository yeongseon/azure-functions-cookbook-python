"""Trigger handlers driven directly with fake blob/event objects (no Functions host)."""

from __future__ import annotations

import io
import logging
from types import SimpleNamespace
from typing import Any

import pytest
from rag_fakes import FakeEmbedder, FakeStore

from app.functions import ingest
from app.services import ingestion
from app.services.azure_clients import Services
from app.services.ingestion import chunk_id_for, source_id_for
from function_app import app

SECRET = "TOP-SECRET-DOCUMENT-BODY"


class FakeBlob(io.BytesIO):
    def __init__(self, name: str | None, data: bytes) -> None:
        super().__init__(data)
        self.name = name


@pytest.fixture
def services(monkeypatch: pytest.MonkeyPatch) -> Services:
    fake = Services(embedder=FakeEmbedder(), store=FakeStore())
    monkeypatch.setattr(ingest, "get_services", lambda: fake)
    return fake


CONTEXT: Any = SimpleNamespace(invocation_id="inv-42")


# ``get_functions()`` validates names and cannot be called twice on one app, so call it once.
FUNCTIONS = {f.get_function_name(): f for f in app.get_functions()}


def _user_function(name: str) -> Any:
    return FUNCTIONS[name].get_user_function()


def test_registered_triggers_and_blob_source() -> None:
    functions = FUNCTIONS
    assert set(functions) == {"index_blob", "remove_deleted_blob"}
    blob_binding = next(
        b for b in functions["index_blob"].get_bindings() if b.type == "blobTrigger"
    )
    blob_json = blob_binding.get_dict_repr()
    assert blob_json["source"] == "EventGrid"
    assert blob_json["path"] == "rag-documents/{name}"
    assert any(
        b.type == "eventGridTrigger" for b in functions["remove_deleted_blob"].get_bindings()
    )


def test_index_blob_indexes_and_logs_counts_not_content(
    services: Services, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    body = f"{SECRET} " + "word " * 600
    _user_function("index_blob")(FakeBlob("rag-documents/notes/a.md", body.encode()), CONTEXT)

    store: FakeStore = services.store  # type: ignore[assignment]
    sid = source_id_for("rag-documents", "notes/a.md")
    assert chunk_id_for(sid, 0) in store.docs
    assert "inv-42" in caplog.text and sid in caplog.text
    assert SECRET not in caplog.text and "notes/a.md" not in caplog.text


def test_index_blob_drops_permanent_failures_instead_of_raising(
    services: Services, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    handler = _user_function("index_blob")
    handler(FakeBlob("rag-documents/bin.dat", b"\xff\xfe\xfa"), CONTEXT)
    handler(FakeBlob(None, b"text"), CONTEXT)
    assert services.store.docs == {}  # type: ignore[attr-defined]
    assert caplog.text.count("Rejected blob") == 2


def test_index_blob_reads_at_most_limit_plus_one_byte(services: Services) -> None:
    reads: list[int] = []

    class Spy(FakeBlob):
        def read(self, size: int | None = -1) -> bytes:
            reads.append(size if size is not None else -1)
            return super().read(size)

    _user_function("index_blob")(Spy("rag-documents/a.md", b"hello world"), CONTEXT)
    assert reads == [ingestion.MAX_BLOB_BYTES + 1]


def test_index_blob_lets_transient_errors_propagate_for_host_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Boom(FakeEmbedder):
        def embed(self, texts: list[str]) -> list[list[float]]:
            raise TimeoutError("transient")

    monkeypatch.setattr(ingest, "get_services", lambda: Services(Boom(), FakeStore()))
    with pytest.raises(TimeoutError):
        _user_function("index_blob")(FakeBlob("rag-documents/a.md", b"text"), CONTEXT)


def _event(event_type: str, subject: str | None) -> Any:
    return SimpleNamespace(event_type=event_type, subject=subject)


def test_deleted_event_removes_chunks(services: Services, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    _user_function("index_blob")(FakeBlob("rag-documents/a.md", b"hello " * 300), CONTEXT)
    assert services.store.docs  # type: ignore[attr-defined]
    subject = "/blobServices/default/containers/rag-documents/blobs/a.md"
    _user_function("remove_deleted_blob")(_event("Microsoft.Storage.BlobDeleted", subject), CONTEXT)
    assert services.store.docs == {}  # type: ignore[attr-defined]
    assert "deleted=" in caplog.text


def test_other_events_are_ignored(services: Services) -> None:
    handler = _user_function("remove_deleted_blob")
    handler(
        _event("Microsoft.Storage.BlobCreated", "/blobServices/default/containers/c/blobs/x"),
        CONTEXT,
    )
    handler(_event("Microsoft.Storage.BlobDeleted", None), CONTEXT)
    assert services.store.docs == {}  # type: ignore[attr-defined]


def test_get_services_builds_once(monkeypatch: pytest.MonkeyPatch) -> None:
    built: list[int] = []
    sentinel = Services(FakeEmbedder(), FakeStore())
    monkeypatch.setattr(ingest, "build_services", lambda: (built.append(1), sentinel)[1])
    ingest.get_services.cache_clear()
    assert ingest.get_services() is ingest.get_services() is sentinel
    assert built == [1]
    ingest.get_services.cache_clear()
