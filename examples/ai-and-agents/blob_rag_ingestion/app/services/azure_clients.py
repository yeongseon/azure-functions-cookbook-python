"""Adapters that put Azure OpenAI and Azure AI Search behind the ingestion protocols.

The adapters take already-built SDK clients so tests can pass fakes. ``build_services`` is the only
place that creates real clients, with Microsoft Entra ID (``DefaultAzureCredential``) and no keys.
Unit tests never call it, so the live wiring is not verified by this recipe's test suite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.settings import Settings
from app.services.ingestion import ChunkStore, Embedder


class OpenAIEmbedder:
    def __init__(self, client: Any, deployment: str) -> None:
        self._client = client
        self._deployment = deployment

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._deployment, input=texts)
        # Sort by the response index rather than trusting list order.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


class SearchChunkStore:
    def __init__(self, client: Any) -> None:
        self._client = client

    def existing_chunks(self, source_id: str) -> dict[str, str]:
        # ``source_id`` is a hex digest produced by this recipe, never caller text, so it is safe
        # to embed in the OData filter. The index must declare the field filterable.
        results = self._client.search(
            search_text="*",
            filter=f"source_id eq '{source_id}'",
            select=["id", "content_hash"],
        )
        return {str(row["id"]): str(row["content_hash"]) for row in results}

    def upsert(self, documents: list[dict[str, object]]) -> None:
        self._raise_on_failures(self._client.merge_or_upload_documents(documents))

    def delete(self, chunk_ids: list[str]) -> None:
        self._raise_on_failures(self._client.delete_documents([{"id": item} for item in chunk_ids]))

    @staticmethod
    def _raise_on_failures(results: Any) -> None:
        # Per-document failures are reported in the result list, not raised by the SDK call.
        failed = [item.key for item in results if not item.succeeded]
        if failed:
            raise RuntimeError(f"Azure AI Search rejected {len(failed)} document(s)")


@dataclass(frozen=True)
class Services:
    embedder: Embedder
    store: ChunkStore


def build_services(settings: Settings | None = None) -> Services:
    """Create live clients. Imports are local so unit tests need no Azure SDK installed."""
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from azure.search.documents import SearchClient
    from openai import OpenAI

    settings = settings or Settings.from_env()
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
    openai_client = OpenAI(
        base_url=f"{settings.openai_endpoint}/openai/v1/",
        api_key=token_provider,
        timeout=30.0,
        max_retries=2,
    )
    search_client = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index,
        credential=credential,
    )
    return Services(
        embedder=OpenAIEmbedder(openai_client, settings.embedding_deployment),
        store=SearchChunkStore(search_client),
    )
