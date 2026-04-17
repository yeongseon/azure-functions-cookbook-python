# blob_eventgrid_trigger

Blob-triggered Azure Function configured for Event Grid source notifications.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- Blob trigger with `source="EventGrid"`
- Faster event-driven invocation compared with polling-based blob scanning
- Logging blob details for low-latency upload workflows

## Run Locally

```bash
cd examples/blob/blob_eventgrid_trigger
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Blob events for `events/{name}` invoke the function quickly after upload.
- Logs include blob name and size with an Event Grid-specific trigger path.
