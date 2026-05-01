# Durable AI Pipeline

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/ai-and-agents/durable-ai-pipeline/)

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
