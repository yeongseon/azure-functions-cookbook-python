# Durable AI Pipeline

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/durable-ai-pipeline/)

Durable Functions sample that orchestrates three AI steps: embedding, vector
search, and answer generation.

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/pipeline/start` - start a durable AI pipeline instance

## Environment Variables

Copy `local.settings.json.example` to `local.settings.json` and fill these in. In Azure, set
them as app settings.

| Setting | Required | Default | Purpose |
| --- | --- | --- | --- |
| `AZURE_OPENAI_ENDPOINT` | For real calls | none | Azure OpenAI resource endpoint used by the embedding and generation activities. |
| `AZURE_OPENAI_KEY` | For real calls | none | API key for the Azure OpenAI resource. |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | No | `gpt-4o-mini` | Deployment name used to generate the final answer. |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | No | `text-embedding-3-small` | Deployment name used to embed the question. |
| `AZURE_OPENAI_API_VERSION` | No | `2024-02-01` | Azure OpenAI REST API version. |
| `AI_SEARCH_ENDPOINT` | For real calls | none | Azure AI Search endpoint used by the vector-search activity. |
| `AI_SEARCH_KEY` | For real calls | none | Admin or query key for the Azure AI Search service. |
| `AI_SEARCH_INDEX` | No | `knowledge-index` | Index searched for matching vectors. |
| `AzureWebJobsStorage` | Yes | `UseDevelopmentStorage=true` | Durable Functions state and runtime storage. Use Azurite locally. |
| `FUNCTIONS_WORKER_RUNTIME` | Yes | `python` | Required by the Functions host. |

Each activity falls back to a deterministic stub when its endpoint or key is unset, so the
orchestration runs end to end offline. Set the Azure OpenAI and AI Search values to exercise the
real services.

Prefer Key Vault references or a managed identity over raw keys in production.
