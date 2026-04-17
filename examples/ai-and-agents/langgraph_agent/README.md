# LangGraph Agent Example

Demonstrates `azure-functions-langgraph` adapter with `azure-functions-logging`,
`azure-functions-validation`, and `azure-functions-openapi`.

## Run

```bash
pip install -r requirements.txt
cp local.settings.sample.json local.settings.json
func start
```

## Endpoints

- `POST /api/agent/invoke` — invoke the LangGraph agent (JSON body: `{"message": "...", "thread_id": "..."}`)
