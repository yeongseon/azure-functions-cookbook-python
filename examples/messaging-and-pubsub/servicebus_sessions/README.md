# servicebus_sessions

Azure Functions example showing ordered message processing with Azure Service Bus sessions.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for `AzureWebJobsStorage`
- An Azure Service Bus namespace with a queue named `orders-with-sessions`
- Sessions enabled on that queue

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ServiceBusConnection` | Service Bus connection string for the session-enabled queue | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>` |

Copy `local.settings.json.example` to `local.settings.json` before running locally.

## What It Demonstrates

- `service_bus_queue_trigger` with `is_sessions_enabled=True`
- Accessing `session_id` from `ServiceBusMessage`
- Structured logging with `azure-functions-logging-python`
- Ordered processing within each customer session

## Run Locally

```bash
cd examples/messaging-and-pubsub/servicebus_sessions
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Send related messages to `orders-with-sessions` using the same `session_id`, such as `cust-42`, to verify in-order delivery.

## Example Event

```json
{
  "customer_id": "cust-42",
  "order_id": "ord-1001",
  "step": "payment.authorized",
  "sequence": 1
}
```

## Expected Output

- Logs include `session_id`, `order_id`, `step`, and `sequence` for each received message.
- Messages in the same session are processed in send order.
- Different sessions can be handled as separate ordered streams.
