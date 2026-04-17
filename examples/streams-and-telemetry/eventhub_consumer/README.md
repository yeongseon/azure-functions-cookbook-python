# eventhub_consumer

Event Hub-triggered Azure Function for near real-time telemetry stream processing.

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

- Event Hub trigger bound to `telemetry`
- Reading event body plus partition key, sequence number, and offset
- Telemetry helper function for stream transformation and logging

## Run Locally

```bash
cd examples/eventhub/eventhub_consumer
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Logs include stream metadata (`partition_key`, `sequence_number`, `offset`).
- Telemetry payloads are processed and logged with a normalized status message.
