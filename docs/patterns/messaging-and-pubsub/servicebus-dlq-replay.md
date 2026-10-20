# Service Bus DLQ Replay

> **Trigger**: Service Bus (DLQ) | **State**: stateless | **Guarantee**: at-least-once | **Difficulty**: intermediate

## Overview
The `examples/messaging-and-pubsub/servicebus_dlq_replay/` recipe inspects dead-letter queue messages,
captures failure context, and replays repaired messages back to the main queue. Use it when operators need
to inspect why messages failed, fix the underlying issue, and safely return those messages to normal processing.

This recipe combines an HTTP-triggered, non-consuming inspect endpoint with an HTTP replay endpoint, both
powered by the Service Bus SDK. Inspection uses `peek_messages`, which never settles (completes or abandons)
a message, so a previewed message remains available to the replay endpoint afterward.

## When to Use
- You need operational visibility into messages that exceeded max delivery attempts.
- You want a controlled replay mechanism after fixing malformed payloads, dependencies, or downstream outages.
- You need to preserve tracing metadata such as `message_id`, `correlation_id`, and dead-letter reason.

## When NOT to Use
- You can automatically recover transient failures through normal retries without operator intervention.
- You need exactly-once side effects and cannot make downstream processing idempotent.
- You want to discard poison messages permanently instead of investigating and replaying them.

## Architecture
```mermaid
flowchart LR
    main[Main Queue] -->|processing fails repeatedly| dlq[Dead-Letter Queue]
    inspect[HTTP Inspect Endpoint] -->|peek, non-consuming| dlq
    inspect --> log[Log failure metadata]
    log --> replay[HTTP Replay Endpoint]
    replay --> send[Replay to main queue]
    send --> main
```

## Behavior
```mermaid
sequenceDiagram
    participant Worker as Main Queue Consumer
    participant Queue as Main Queue
    participant DLQ as Dead-Letter Queue
    participant Inspect as HTTP Inspect Endpoint
    participant Replay as HTTP Replay Endpoint

    Queue->>Worker: Deliver message
    Worker-->>Queue: Processing fails repeatedly
    Queue->>DLQ: Move message to dead-letter queue
    Inspect->>DLQ: Peek messages (non-consuming)
    Inspect->>Inspect: Log body + dead-letter reason
    Inspect->>Replay: Operator reviews logs and invokes replay
    Replay->>DLQ: Receive messages from DLQ
    Replay->>Queue: Send repaired messages back to main queue
    Replay->>DLQ: Complete DLQ copies only after a successful send
```

## Implementation
The example has two entry points:

1. `inspect_dead_letter_queue` is an HTTP-triggered function (`GET /api/servicebus/dlq/inspect`) that uses
   `receiver.peek_messages()` to preview `message_id`, `correlation_id`, `delivery_count`, `dead_letter_reason`,
   and a safe body preview -- without removing anything from the Dead-Letter sub-queue. A DLQ-bound *trigger*
   cannot do this: a trigger handler that returns successfully is auto-completed under the host's default
   `autoCompleteMessages=true`, permanently discarding the message before an operator could replay it.
2. `replay_dead_letter_queue` is an HTTP-triggered function that connects through `azure-servicebus`, reads a
   small DLQ batch, publishes cloned messages back to the main queue, and completes the DLQ copies -- only
   after each send succeeds, so a failed publish leaves its message replayable.

`azure_functions_logging` keeps logs structured so failures and replay decisions are easy to query.

```python
@app.route(route="servicebus/dlq/inspect", methods=["GET"])
def inspect_dead_letter_queue(req: func.HttpRequest) -> func.HttpResponse:
    with client.get_queue_receiver(
        queue_name=QUEUE_NAME,
        sub_queue=ServiceBusSubQueue.DEAD_LETTER,
    ) as receiver:
        for message in receiver.peek_messages(max_message_count=batch_size):
            logger.warning(
                "Dead-lettered Service Bus message detected",
                extra={
                    "message_id": getattr(message, "message_id", None),
                    "dead_letter_reason": getattr(message, "dead_letter_reason", None),
                    "delivery_count": int(getattr(message, "delivery_count", 1)),
                },
            )
```

Replay uses the SDK because output bindings are not a good fit for iterating over and completing DLQ messages.

```python
with client.get_queue_receiver(
    queue_name=QUEUE_NAME,
    sub_queue=ServiceBusSubQueue.DEAD_LETTER,
) as receiver, client.get_queue_sender(queue_name=QUEUE_NAME) as sender:
    messages = receiver.receive_messages(max_message_count=batch_size, max_wait_time=5)
    for message in messages:
        sender.send_messages(_build_replay_message(message))
        receiver.complete_message(message)
```

## Project Structure
```text
examples/messaging-and-pubsub/servicebus_dlq_replay/
|-- function_app.py
|-- host.json
|-- local.settings.json.example
|-- pyproject.toml
`-- README.md
```

## Config
- `ServiceBusConnection`: Service Bus connection string for local development.
- `SERVICEBUS_QUEUE_NAME`: Main queue name. Defaults to `orders`.
- `DLQ_REPLAY_BATCH_SIZE`: Default number of messages to replay per HTTP request.
- `AzureWebJobsStorage`: Storage account used by the Functions host.

## Run Locally
```bash
cd examples/messaging-and-pubsub/servicebus_dlq_replay
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Inspect dead-lettered messages without removing them:

```bash
curl "http://localhost:7071/api/servicebus/dlq/inspect?code=<function-key>&limit=5"
```

Replay a batch:

```bash
curl -X POST "http://localhost:7071/api/servicebus/dlq/replay?code=<function-key>&limit=5"
```

## Expected Output
```text
[Warning] Dead-lettered Service Bus message detected {'message_id': 'ord-42', 'dead_letter_reason': 'MaxDeliveryCountExceeded', 'delivery_count': 10}
[Information] Replayed dead-lettered Service Bus message {'original_message_id': 'ord-42', 'replayed_message_id': 'ord-42-replay-a1b2c3d4'}
```

## Production Considerations
- Idempotency: replayed messages can be delivered again, so consumers must tolerate duplicates.
- Safety: gate replay behind Function or higher auth and consider approval workflows for sensitive queues.
- Throughput: replay in bounded batches to avoid flooding downstream services after an outage.
- Observability: emit dead-letter reason, replay operator, and replay counts to dashboards and alerts.
- Repair policy: fix root causes before replaying or messages will cycle back into the DLQ.

## Related Links
- [Dead-letter queues](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues)
