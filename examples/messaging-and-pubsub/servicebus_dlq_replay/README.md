# Service Bus DLQ Replay

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/messaging-and-pubsub/servicebus-dlq-replay/)

Replay dead-lettered Service Bus queue messages back to the main queue after inspection and remediation.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)
- An Azure Service Bus namespace with a queue named `orders` or your configured `SERVICEBUS_QUEUE_NAME`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ServiceBusConnection` | Service Bus connection string | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>` |
| `SERVICEBUS_QUEUE_NAME` | Main queue name to monitor and replay into | `orders` |
| `DLQ_REPLAY_BATCH_SIZE` | Default replay batch size for the HTTP endpoint | `10` |

Copy `local.settings.json.example` to `local.settings.json` and update the values.

## What It Demonstrates

- Service Bus dead-letter queue trigger bound to `orders/$DeadLetterQueue`
- Structured logging for dead-letter reason, delivery count, and message metadata
- HTTP-triggered replay flow using the Azure Service Bus SDK

## Run Locally

```bash
cd examples/messaging-and-pubsub/servicebus_dlq_replay
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Replay Messages

```bash
curl -X POST "http://localhost:7071/api/servicebus/dlq/replay?code=<function-key>&limit=5"
```

## Expected Output

- DLQ messages are logged with `dead_letter_reason`, `delivery_count`, and `message_id`.
- `POST /api/servicebus/dlq/replay` returns the number of replayed messages and their new replay message IDs.
