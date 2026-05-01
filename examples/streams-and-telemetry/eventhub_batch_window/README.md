# Event Hub Batch Window

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/streams-and-telemetry/eventhub-batch-window/)

Event Hub-triggered Azure Function that processes a batch window and logs aggregate telemetry totals.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- An Azure Event Hub namespace with a hub named `telemetry`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `EventHubConnection` | Event Hub connection string with EntityPath | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>;EntityPath=telemetry` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- Event Hub trigger configured with batch cardinality
- Windowed aggregation of count and numeric values
- Logging a single summary result per invocation window

## Run Locally

```bash
cd examples/streams-and-telemetry/eventhub_batch_window
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Logs include the batch size and observed partition keys.
- Logs include one aggregated window summary with count, total, and per-metric totals.
