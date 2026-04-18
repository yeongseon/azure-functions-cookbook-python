# Embedding Vector Search Example

HTTP-triggered sample that creates Azure OpenAI embeddings and uses them to run
a vector query against Azure AI Search.

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/search` - return ranked vector matches for a query
