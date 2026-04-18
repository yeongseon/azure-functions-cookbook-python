# Durable AI Pipeline Example

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
