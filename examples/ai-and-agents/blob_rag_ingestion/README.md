# Blob RAG Ingestion

Event-driven ingestion half of an Azure RAG path: a blob upload becomes chunks, embeddings and
documents in an Azure AI Search index. It fills the gap between
[Blob Event Grid Trigger](../../blob-and-file-triggers/blob_eventgrid_trigger/) (which only logs the
blob) and the query-side recipes
([Embedding Vector Search](../embedding_vector_search/), [RAG Knowledge API](../rag_knowledge_api/),
[LangGraph RAG Agent](../langgraph_rag_agent/)). See the
[end-to-end path](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/azure-rag-path/).

## What It Demonstrates

- Blob trigger with `source=EventGrid` on `rag-documents/{name}` plus an Event Grid trigger for
  `Microsoft.Storage.BlobDeleted`.
- Stable, search-key-safe chunk ids (`<sha256(container/blob)[:32]>-<index>`), merge-or-upload writes,
  and skipping the embedding call for chunks whose text hash is already indexed.
- Update handling: stale chunks of a shortened blob are deleted after the new chunks are written.
- Permanent problems (too large, not UTF-8, too many chunks) are logged and dropped; transient
  errors propagate so the host retries.
- Microsoft Entra ID auth (`DefaultAzureCredential`) for Azure OpenAI and Azure AI Search; no keys.
- Logs carry counts, a hashed source id and the invocation id, never document text or blob names.

## Index fields this recipe writes

| Field | Purpose | Index attributes you must declare |
| --- | --- | --- |
| `id` | chunk key | key |
| `source_id` | groups the chunks of one blob | filterable |
| `source`, `title`, `chunk_index` | metadata | retrievable |
| `content_hash` | per-chunk text hash for skip-if-unchanged | retrievable |
| `content` | chunk text | searchable |
| `content_vector` | embedding | vector field, dimensions = your embedding model, with a vector profile |

Create the index yourself (portal, Bicep or SDK); this recipe does not. The field names match what
[Embedding Vector Search](../embedding_vector_search/) queries.

## Run the tests (offline)

```bash
pip install -e ".[dev]"
pytest
```

The tests use in-memory fakes for the blob, the Event Grid event, the embedding client and the
search client. They need no Azure account, network, Azurite or Functions host.

## Run against Azure (not verified by this repository)

```bash
cp local.settings.json.example local.settings.json   # fill in endpoints
az login                                              # DefaultAzureCredential picks this up
func start
```

Grant the identity **Cognitive Services OpenAI User** on the Azure OpenAI resource and **Search
Index Data Contributor** on the search service. Upload a UTF-8 text or Markdown file to the
`rag-documents` container. Deleting it needs an Event Grid subscription for
`Microsoft.Storage.BlobDeleted` that targets the `remove_deleted_blob` function.

## Not handled

Blob versions and soft delete, binary formats (PDF, Office), event ordering between a delete and a
re-upload of the same name, private networking, and any query-side logic. See the pattern page.
