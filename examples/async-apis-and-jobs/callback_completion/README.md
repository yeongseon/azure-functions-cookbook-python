# Callback Completion

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/async-apis-and-jobs/callback-completion/)

HTTP + Queue example that accepts work at `/api/tasks` and sends an HTTP callback when background processing finishes.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or an Azure Storage account
- A webhook endpoint to receive callbacks, such as [webhook.site](https://webhook.site)

## What It Demonstrates

- HTTP-triggered task submission at `/api/tasks`
- Request validation with `@validate_http`
- Structured logging with `azure-functions-logging-python`
- Queue-triggered background processing
- HTTP `POST` callback delivery to the caller's `callback_url`

## Run Locally

```bash
cd examples/async-apis-and-jobs/callback_completion
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Request

```bash
curl -X POST "http://localhost:7071/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"task_name":"generate-report","callback_url":"https://webhook.site/your-id"}'
```

Expected immediate response:

```json
{
  "status": "accepted",
  "task_id": "<task-id>",
  "callback_pending": true
}
```

The queue worker later posts a callback body like:

```json
{
  "status": "completed",
  "task_id": "<task-id>",
  "result": {
    "taskName": "generate-report",
    "artifactUrl": "https://example.invalid/results/<task-id>.json",
    "processedAt": "2026-04-17T00:00:00Z"
  },
  "completed_at": "2026-04-17T00:00:03Z"
}
```

## Notes

- If the callback endpoint returns an error or is unreachable, the queue-triggered function raises and Azure Functions retries the message.
- Consumers should treat callback delivery as at-least-once and deduplicate by `task_id`.
