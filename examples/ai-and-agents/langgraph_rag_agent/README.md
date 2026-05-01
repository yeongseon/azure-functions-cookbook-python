# LangGraph RAG Agent

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/ai-and-agents/langgraph-rag-agent/)

This example shows how to combine:

- `azure-functions-langgraph-python` for LangGraph hosting
- `azure-functions-validation-python` for typed request handling
- `azure-functions-openapi-python` for API metadata
- `azure-functions-logging-python` for structured logs

The sample exposes a stateful `POST /api/chat` endpoint. Each request includes a
user message and optional `thread_id`. The agent decides whether to call the
knowledge search tool or answer directly.

## Files

- `function_app.py` - LangGraph definition, knowledge tool, and HTTP routes
- `pyproject.toml` - Python dependencies
- `host.json` - Azure Functions host settings
- `local.settings.json.example` - local environment template

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoints

- `POST /api/chat` - invoke the stateful RAG agent
- `GET /api/chat/state/{thread_id}` - inspect the in-memory thread state

## Example Request

```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search the onboarding runbook for password reset steps.",
    "thread_id": "support-42",
    "top_k": 2
  }'
```

## Example Response

```json
{
  "thread_id": "support-42",
  "route": "knowledge_search",
  "answer": "I searched the knowledge base before responding. Relevant guidance: Reset the password from the Helpdesk portal, then reissue MFA if the account is still locked. Temporary passwords expire after 24 hours and must be changed at first sign-in.",
  "citations": [
    {
      "title": "Onboarding Runbook",
      "snippet": "Reset the password from the Helpdesk portal, then reissue MFA if the account is still locked.",
      "source": "mock://onboarding-runbook"
    },
    {
      "title": "Access Policy FAQ",
      "snippet": "Temporary passwords expire after 24 hours and must be changed at first sign-in.",
      "source": "mock://access-policy-faq"
    }
  ],
  "history_length": 2
}
```

## Notes

- If the toolkit packages are unavailable, the sample falls back to local stubs so the file remains readable and compilable.
- Knowledge retrieval uses a mock client when Azure AI Search is not configured, returning sample citations to keep the integration path obvious.
- Replace the heuristic route logic with an LLM-backed planner when you wire real AI endpoints.

## Learn More

- Azure Functions Python developer guide: https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python
- Azure Functions HTTP trigger reference: https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger
