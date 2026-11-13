"""Adapters tested against fake SDK clients; the live ``build_services`` is not exercised."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.core.settings import Settings
from app.services.azure_clients import OpenAIEmbedder, SearchChunkStore


class FakeOpenAI:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.embeddings = SimpleNamespace(create=self._create)

    def _create(self, *, model: str, input: list[str]) -> Any:
        self.calls.append({"model": model, "input": input})
        data = [
            SimpleNamespace(index=i, embedding=(float(i), 0.5)) for i in reversed(range(len(input)))
        ]
        return SimpleNamespace(data=data)  # deliberately out of order


class FakeSearch:
    def __init__(self, fail_keys: tuple[str, ...] = ()) -> None:
        self.rows = [
            {"id": "s-00000", "content_hash": "h0"},
            {"id": "s-00001", "content_hash": "h1"},
        ]
        self.fail_keys = fail_keys
        self.seen: dict[str, Any] = {}

    def search(self, **kwargs: Any) -> list[dict[str, str]]:
        self.seen = kwargs
        return self.rows

    def _results(self, docs: list[dict[str, Any]]) -> list[Any]:
        return [SimpleNamespace(key=d["id"], succeeded=d["id"] not in self.fail_keys) for d in docs]

    def merge_or_upload_documents(self, docs: list[dict[str, Any]]) -> list[Any]:
        return self._results(docs)

    def delete_documents(self, docs: list[dict[str, Any]]) -> list[Any]:
        return self._results(docs)


def test_embedder_restores_input_order_and_uses_deployment_name() -> None:
    client = FakeOpenAI()
    vectors = OpenAIEmbedder(client, "my-embeddings").embed(["a", "b", "c"])
    assert vectors == [[0.0, 0.5], [1.0, 0.5], [2.0, 0.5]]
    assert client.calls == [{"model": "my-embeddings", "input": ["a", "b", "c"]}]


def test_store_filters_by_source_and_maps_rows() -> None:
    search = FakeSearch()
    assert SearchChunkStore(search).existing_chunks("abc123") == {"s-00000": "h0", "s-00001": "h1"}
    assert search.seen["filter"] == "source_id eq 'abc123'"
    assert search.seen["select"] == ["id", "content_hash"]


def test_store_raises_when_any_document_fails() -> None:
    store = SearchChunkStore(FakeSearch(fail_keys=("x",)))
    store.upsert([{"id": "ok"}])
    store.delete(["ok"])
    with pytest.raises(RuntimeError, match="1 document"):
        store.upsert([{"id": "x"}, {"id": "ok"}])
    with pytest.raises(RuntimeError, match="1 document"):
        store.delete(["x"])


def test_settings_require_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("AZURE_OPENAI_ENDPOINT", "AI_SEARCH_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_ENDPOINT, AI_SEARCH_ENDPOINT"):
        Settings.from_env()
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://oai.example/")
    monkeypatch.setenv("AI_SEARCH_ENDPOINT", "https://search.example")
    settings = Settings.from_env()
    assert settings.openai_endpoint == "https://oai.example"
    assert settings.embedding_deployment == "text-embedding-3-small"
    assert settings.search_index == "knowledge-index"


def test_build_services_constructs_clients_without_network() -> None:
    from app.services.azure_clients import build_services

    services = build_services(
        Settings(
            openai_endpoint="https://oai.example",
            embedding_deployment="emb",
            search_endpoint="https://search.example",
            search_index="idx",
        )
    )
    assert isinstance(services.embedder, OpenAIEmbedder)
    assert isinstance(services.store, SearchChunkStore)
