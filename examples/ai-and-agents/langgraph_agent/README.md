# LangGraph Agent

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/ai-and-agents/langgraph-agent/)

Demonstrates `azure-functions-langgraph-python` adapter with `azure-functions-logging-python`,
`azure-functions-validation-python`, and `azure-functions-openapi-python`.

## Run

```bash
pip install -e ".[dev]"
cp local.settings.sample.json local.settings.json
func start
```

## Endpoints

- `POST /api/agent/invoke` — invoke the LangGraph agent (JSON body: `{"message": "...", "thread_id": "..."}`)
