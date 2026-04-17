# servicebus_worker

Service Bus queue-triggered Azure Function for reliable background work consumption.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- An Azure Service Bus namespace with a queue named `tasks`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ServiceBusConnection` | Service Bus connection string | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- Service Bus queue trigger bound to `tasks`
- Message parsing with `correlation_id` and `delivery_count` logging
- Processing helper function and dead-letter handling guidance

## Run Locally

```bash
cd examples/servicebus/servicebus_worker
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Each message logs correlation and delivery metadata, then processing status.
- Invalid JSON payloads are logged as errors and can be investigated for DLQ handling.
