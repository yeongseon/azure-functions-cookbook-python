# Service Bus Trigger and Output Bindings

Service Bus is the richer messaging option for Azure Functions when you need dead-lettering, sessions, duplicate detection, topics, or transactions at the broker layer. It is the usual choice for business workflows that outgrow Queue Storage.

## Trigger

Use `@app.service_bus_queue_trigger(...)` for queues or `@app.service_bus_topic_trigger(...)` for topic subscriptions.

Key parameters: `queue_name` or `topic_name` + `subscription_name`, `connection`, `is_sessions_enabled`, and optional `cardinality`.

```python
import azure.functions as func

app = func.FunctionApp()

@app.service_bus_queue_trigger(
    arg_name="message",
    queue_name="orders",
    connection="ServiceBusConnection",
    is_sessions_enabled=False,
)
def service_bus_queue_example(message: func.ServiceBusMessage) -> None:
    print(message.get_body().decode("utf-8"))
```

Topic example:

```python
@app.service_bus_topic_trigger(
    arg_name="message",
    topic_name="sales",
    subscription_name="billing",
    connection="ServiceBusConnection",
)
def service_bus_topic_example(message: func.ServiceBusMessage) -> None:
    print(message.metadata)
```

## Input Binding

Service Bus handlers often join the brokered message with external state.

```python
import azure.functions as func

app = func.FunctionApp()

@app.service_bus_queue_trigger(arg_name="message", queue_name="orders", connection="ServiceBusConnection")
@app.cosmos_db_input(
    arg_name="order_doc",
    database_name="appdb",
    container_name="orders",
    id="{messageId}",
    partition_key="{messageId}",
    connection="CosmosDBConnection",
)
def hydrate_order(message: func.ServiceBusMessage, order_doc: str) -> None:
    print(order_doc)
```

## Output Binding

Use queue or topic outputs for follow-up workflows.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.service_bus_queue_trigger(arg_name="message", queue_name="orders", connection="ServiceBusConnection")
@app.service_bus_topic_output(
    arg_name="out_msg",
    topic_name="order-events",
    connection="ServiceBusConnection",
)
def publish_order_event(message: func.ServiceBusMessage, out_msg: func.Out[str]) -> None:
    out_msg.set(json.dumps({"messageId": message.message_id, "status": "processed"}))
```

## Configuration

Tune concurrency and settlement in `host.json`:

```json
{
  "version": "2.0",
  "extensions": {
    "serviceBus": {
      "prefetchCount": 32,
      "messageHandlerOptions": {
        "autoCompleteMessages": true,
        "maxConcurrentCalls": 16,
        "maxAutoLockRenewalDuration": "00:05:00"
      }
    }
  }
}
```

`local.settings.json` commonly includes `ServiceBusConnection` and any secondary connection names used by other bindings. Managed identity-based connections are preferred in Azure.

## Scaling Behavior

Scale-out is driven by active message count and age. Each instance processes messages under peek-lock semantics, so failures or lock expiry can cause redelivery. Ordering is best-effort for plain queues and much stronger when sessions are enabled, because one session is processed in order by one consumer at a time.

## Common Pitfalls

- Long processing without lock renewal can trigger duplicate delivery when the lock expires.
- Sessions change concurrency behavior; throughput drops if a few hot sessions dominate the backlog.
- Queue and topic decorators are different; using the wrong one usually looks like a configuration issue, not a code error.

## Related Patterns

- [Service Bus Worker](../patterns/messaging-and-pubsub/servicebus-worker.md)
- [Managed Identity Service Bus](../patterns/security-and-tenancy/managed-identity-servicebus.md)
- [Retry and Idempotency](../patterns/reliability/retry-and-idempotency.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-service-bus-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-service-bus-output?pivots=programming-language-python&tabs=python-v2
