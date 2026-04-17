# Queue Storage Trigger and Output Binding

Queue Storage is the simplest built-in background work primitive in Azure Functions. It is best for decoupling HTTP ingress from asynchronous processing when you need cheap at-least-once delivery and do not require ordering or rich broker features.

## Trigger

Use `@app.queue_trigger(...)` to process a queue message.

Key parameters: `queue_name`, `connection`, and `arg_name`.

```python
import azure.functions as func

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="incoming-jobs", connection="AzureWebJobsStorage")
def queue_example(msg: func.QueueMessage) -> None:
    print(msg.get_body().decode("utf-8"))
```

## Input Binding

Queue-triggered handlers often enrich a message with a Blob or SQL lookup.

```python
import azure.functions as func

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="images", connection="AzureWebJobsStorage")
@app.blob_input(arg_name="blob_data", path="uploads/{queueTrigger}", connection="AzureWebJobsStorage")
def queue_with_blob(msg: func.QueueMessage, blob_data: bytes) -> None:
    print(f"bytes={len(blob_data)}")
```

## Output Binding

Use a queue output binding to chain work to another queue.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="incoming-jobs", connection="AzureWebJobsStorage")
@app.queue_output(arg_name="out_msg", queue_name="processed-jobs", connection="AzureWebJobsStorage")
def queue_fanout(msg: func.QueueMessage, out_msg: func.Out[str]) -> None:
    out_msg.set(json.dumps({"source": msg.id, "status": "done"}))
```

## Configuration

Queue polling and concurrency live under `extensions.queues` in `host.json`:

```json
{
  "version": "2.0",
  "extensions": {
    "queues": {
      "batchSize": 16,
      "newBatchThreshold": 8,
      "maxDequeueCount": 5,
      "visibilityTimeout": "00:00:30"
    }
  }
}
```

`local.settings.json` almost always includes `AzureWebJobsStorage`; identity-based storage connections can replace raw connection strings in deployed environments.

## Scaling Behavior

The scale controller looks at queue depth and message age, then adds instances as backlog grows. Each instance polls in batches and hides messages during processing with the visibility timeout. If processing fails or exceeds visibility, the message can reappear and be retried on the same or another instance.

## Common Pitfalls

- Queue Storage is not FIFO once retries, invisibility timeouts, and multiple workers are involved.
- If processing takes longer than `visibilityTimeout`, duplicate work can happen unless the handler is idempotent.
- Poison messages move only after `maxDequeueCount`; watch the poison queue instead of assuming failures disappear.

## Related Patterns

- [Queue Consumer](../patterns/messaging-and-pubsub/queue-consumer.md)
- [Queue Producer](../patterns/messaging-and-pubsub/queue-producer.md)
- [Retry and Idempotency](../patterns/reliability/retry-and-idempotency.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-queue-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-queue-output?pivots=programming-language-python&tabs=python-v2
