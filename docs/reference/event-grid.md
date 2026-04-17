# Event Grid Trigger and Output Binding

Event Grid is designed for push-based event routing with low publish latency and built-in retries. It fits resource notifications, custom domain events, and fan-out workflows where producers should not poll or manage consumer state directly.

## Trigger

Use `@app.event_grid_trigger(...)` to receive Event Grid events.

Key parameters: `arg_name` and the configured subscription endpoint. The function receives an `EventGridEvent` payload.

```python
import azure.functions as func

app = func.FunctionApp()

@app.event_grid_trigger(arg_name="event")
def event_grid_example(event: func.EventGridEvent) -> None:
    print(event.event_type)
    print(event.get_json())
```

## Input Binding

Event Grid pairs well with lookup bindings when the event only contains an identifier or blob URL.

```python
import azure.functions as func

app = func.FunctionApp()

@app.event_grid_trigger(arg_name="event")
@app.blob_input(arg_name="artifact", path="incoming/{name}", connection="AzureWebJobsStorage")
def hydrate_event(event: func.EventGridEvent, artifact: bytes) -> None:
    print(len(artifact))
```

## Output Binding

Use the Event Grid output binding to republish a normalized domain event.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="normalized-events", connection="AzureWebJobsStorage")
@app.event_grid_output(
    arg_name="event_out",
    topic_endpoint_uri="EventGridTopicUri",
    topic_key_setting="EventGridTopicKey",
)
def publish_event(msg: func.QueueMessage, event_out: func.Out[str]) -> None:
    event_out.set(json.dumps({
        "id": msg.id,
        "subject": "orders/created",
        "eventType": "Contoso.OrderCreated",
        "dataVersion": "1.0",
        "data": {"body": msg.get_body().decode("utf-8")}
    }))
```

## Configuration

Most Event Grid behavior is configured on the subscription, not in `host.json`:

```json
{
  "version": "2.0"
}
```

`local.settings.json` commonly includes `EventGridTopicUri`, `EventGridTopicKey`, plus any storage or database settings used by lookup/output bindings.

## Scaling Behavior

Event Grid pushes HTTPS deliveries to the function endpoint and retries with exponential backoff when the endpoint fails. Scale-out is driven by incoming request rate rather than queue depth. Events are independent, so ordering is not guaranteed across deliveries or retries.

## Common Pitfalls

- Validation handshake failures usually come from endpoint auth or routing issues, not from your event-handling code.
- Event Grid can redeliver events, so downstream writes must be idempotent.
- The event often carries metadata, not the full resource payload; plan to rehydrate from storage or another service.

## Related Patterns

- [Blob Event Grid Trigger](../patterns/blob-and-file-triggers/blob-eventgrid-trigger.md)
- [Webhook GitHub](../patterns/apis-and-ingress/webhook-github.md)
- [Output Binding vs SDK](../patterns/runtime-and-ops/output-binding-vs-sdk.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-grid-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-grid-output?pivots=programming-language-python&tabs=python-v2
