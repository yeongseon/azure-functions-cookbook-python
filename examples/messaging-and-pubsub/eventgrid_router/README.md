# Event Grid Event Router

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/messaging-and-pubsub/eventgrid-event-router/)

Event Grid-triggered Azure Function that routes events to different handlers using event type and subject filters.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- An Event Grid publisher or sample payloads posted to the local Event Grid webhook

## What It Demonstrates

- `@app.event_grid_trigger(...)` in the Python v2 programming model
- Structured logging with `azure-functions-logging-python` and local fallbacks
- Route selection for `Microsoft.Storage.BlobCreated` and custom `Contoso.Items.ItemArchived` events
- Fallback handling for unmatched events

## Run Locally

```bash
cd examples/messaging-and-pubsub/eventgrid_router
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Send a sample blob-created event:

```bash
curl -X POST "http://localhost:7071/runtime/webhooks/EventGrid?functionName=route_events" \
  -H "Content-Type: application/json" \
  -d '[{"id":"1","topic":"demo","subject":"/blobServices/default/containers/inbound-blobs/blobs/report.csv","eventType":"Microsoft.Storage.BlobCreated","eventTime":"2026-01-01T00:00:00Z","data":{"url":"https://example.blob.core.windows.net/inbound-blobs/report.csv","api":"PutBlob"},"dataVersion":"1.0","metadataVersion":"1"}]'
```

## Expected Output

- Blob-created events are logged with `route_key=blob_created` and blob details.
- Premium custom archive events are logged with `route_key=premium_item_archived`.
- Unknown events fall through to the warning-based fallback handler.
