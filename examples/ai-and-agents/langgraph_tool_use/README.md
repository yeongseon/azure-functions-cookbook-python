# Langgraph Tool Use

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/)

Tool-use LangGraph agent with azure-functions-langgraph, routing between a reasoning node and callable tools.

## Run

```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoints

- `POST /api/agent/tool` — invoke the tool-use agent. JSON body: `{"message": "12 * 3", "thread_id": "optional"}`. The reasoning node routes to a `calculator` tool (for `+`, `-`, `*`), a `time` tool (when the message mentions "time"), or echoes otherwise. Response: `{"response": ..., "tool_used": ..., "thread_id": ...}`.
