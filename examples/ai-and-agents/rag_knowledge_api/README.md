# RAG Knowledge API Example

Demonstrates a minimal RAG API built with `azure-functions-knowledge-python`,
`azure-functions-validation-python`, `azure-functions-openapi-python`, and
`azure-functions-logging-python`.

## Endpoints
- `POST /api/ask` — retrieve knowledge chunks and generate a grounded answer
- `POST /api/ingest` — add documents to the knowledge base
- `GET /api/healthz` — lightweight health check

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

If `azure-functions-knowledge-python` is not installed yet, the sample falls back to an
in-memory stub so you can still inspect the endpoint shape locally.

## Example Requests

Ask a question:

```bash
curl -X POST http://localhost:7071/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Azure Functions?",
    "top_k": 3
  }'
```

Ingest documents:

```bash
curl -X POST http://localhost:7071/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "Azure Functions scaling",
        "content": "Azure Functions automatically scales out based on demand.",
        "source": "docs/functions-scaling.md"
      }
    ]
  }'
```

## Notes
- Keep auth level anonymous only for local development.
- Replace local API keys with managed identity or Key Vault in production.
- Tune retrieval settings such as index schema, chunk size, and `top_k` for your corpus.
