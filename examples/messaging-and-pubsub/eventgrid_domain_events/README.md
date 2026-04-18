# eventgrid_domain_events

HTTP-triggered Azure Function that publishes custom order domain events to an Event Grid custom topic, plus an Event
Grid-triggered subscriber that logs the resulting events.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- An Event Grid custom topic endpoint and access key
- Optional but recommended: an Event Grid subscription that routes the custom topic to `handle_order_domain_event`

## What It Demonstrates

- `@app.route(...)` + `@app.event_grid_output(...)` in the Python v2 programming model
- Publishing custom `OrderPlaced` and `OrderShipped` events to an Event Grid custom topic
- `@app.event_grid_trigger(...)` subscriber handling the same domain event contract
- Logging-focused integration behavior without extra storage or state dependencies

## Run Locally

```bash
cd examples/messaging-and-pubsub/eventgrid_domain_events
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Publish an `OrderPlaced` event:

```bash
curl -X POST "http://localhost:7071/api/orders/events" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"OrderPlaced","order_id":"ORD-1001","customer_id":"C-42","amount":149.99,"currency":"USD"}'
```

Publish an `OrderShipped` event:

```bash
curl -X POST "http://localhost:7071/api/orders/events" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"OrderShipped","order_id":"ORD-1001","customer_id":"C-42","tracking_number":"1Z999AA10123456784","carrier":"UPS"}'
```

To simulate the subscriber locally, post a sample Event Grid payload to the webhook endpoint:

```bash
curl -X POST "http://localhost:7071/runtime/webhooks/EventGrid?functionName=handle_order_domain_event" \
  -H "Content-Type: application/json" \
  -d '[{"id":"evt-1001","topic":"demo","subject":"/orders/ORD-1001","eventType":"Contoso.Orders.OrderPlaced","eventTime":"2026-01-01T00:00:00Z","data":{"orderId":"ORD-1001","customerId":"C-42","amount":149.99,"currency":"USD","status":"OrderPlaced"},"dataVersion":"1.0","metadataVersion":"1"}]'
```

## Expected Output

- The HTTP endpoint returns `202 Accepted` with the published custom event type and subject.
- The publisher logs `Accepted order domain event publication` with the order identifier.
- The subscriber logs `Handled order domain event` when Event Grid delivers the event.
