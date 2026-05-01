# Service Bus Topic Fan-out

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/messaging-and-pubsub/servicebus-topic-fanout/)

Azure Functions example showing Service Bus topic fan-out with three independent subscription handlers.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for `AzureWebJobsStorage`
- An Azure Service Bus namespace with topic `orders`
- Subscriptions named `email`, `inventory`, and `analytics`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ServiceBusConnection` | Service Bus connection string for the `orders` topic | `Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<name>;SharedAccessKey=<key>` |

Copy `local.settings.json.example` to `local.settings.json` before running locally.

## What It Demonstrates

- Multiple `service_bus_topic_trigger` functions bound to one topic
- Fan-out delivery into `email`, `inventory`, and `analytics` subscriptions
- Structured logging with `azure-functions-logging-python`

## Run Locally

```bash
cd examples/messaging-and-pubsub/servicebus_topic_fanout
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Publish a JSON message to topic `orders` and confirm each subscription receives a copy.

## Example Event

```json
{
  "order_id": "ord-1001",
  "customer_id": "cust-77",
  "customer_email": "buyer@example.com",
  "event_type": "order.created",
  "total_amount": 149.95,
  "items": [
    {"sku": "SKU-001", "quantity": 1},
    {"sku": "SKU-002", "quantity": 2}
  ]
}
```

## Expected Output

- `order_email_handler` logs confirmation delivery metadata for the `email` subscription.
- `order_inventory_handler` logs SKU reservation metadata for the `inventory` subscription.
- `order_analytics_handler` logs reporting metadata for the `analytics` subscription.
