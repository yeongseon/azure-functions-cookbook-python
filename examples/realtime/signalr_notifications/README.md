# signalr_notifications

Azure Functions app with a SignalR negotiate endpoint and an Event Grid-triggered notification publisher.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- Azure SignalR Service connection string
- Optional Event Grid-compatible sample payloads for local webhook testing

## What It Demonstrates

- HTTP negotiate endpoint using the SignalR connection info input binding
- Event Grid trigger using the SignalR output binding to push hub messages
- Structured logging with `azure-functions-logging` and local fallbacks
- A simple `notificationReceived` contract for connected clients

## Run Locally

```bash
cd examples/realtime/signalr_notifications
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

Negotiate a client connection:

```bash
curl -X POST "http://localhost:7071/api/signalr/negotiate"
```

Publish a notification with an Event Grid webhook payload:

```bash
curl -X POST "http://localhost:7071/runtime/webhooks/EventGrid?functionName=publish_notification" \
  -H "Content-Type: application/json" \
  -d '[{"id":"evt-1001","topic":"demo","subject":"/orders/1001","eventType":"Contoso.Orders.OrderReady","eventTime":"2026-01-01T00:00:00Z","data":{"message":"Order 1001 is ready for pickup","orderId":"1001","status":"ready"},"dataVersion":"1.0","metadataVersion":"1"}]'
```

## Expected Output

- `POST /api/signalr/negotiate` returns SignalR connection metadata JSON.
- `publish_notification` logs the event ID, type, subject, hub, and target method.
- Connected clients on the `notifications` hub receive `notificationReceived` with the event payload.

Example client payload:

```json
{
  "eventId": "evt-1001",
  "eventType": "Contoso.Orders.OrderReady",
  "subject": "/orders/1001",
  "message": "Order 1001 is ready for pickup",
  "data": {
    "message": "Order 1001 is ready for pickup",
    "orderId": "1001",
    "status": "ready"
  }
}
```
