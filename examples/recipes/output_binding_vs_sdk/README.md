# output_binding_vs_sdk

This recipe compares two ways to send the same queue message:

- `enqueue_via_binding` uses `@app.queue_output`
- `enqueue_via_sdk` uses `azure.storage.queue.QueueClient`

Both endpoints accept `POST` JSON with an optional `task` field and enqueue to `work-items`.

## Why compare these patterns?

- output binding: less code, declarative, easier for straightforward scenarios
- SDK client: full API surface, advanced features, explicit runtime behavior

## Run locally

```bash
pip install -r requirements.txt
func start
```

## Try both

```bash
curl -X POST http://localhost:7071/api/enqueue/binding -H "Content-Type: application/json" \
  -d '{"task":"process-report"}'
curl -X POST http://localhost:7071/api/enqueue/sdk -H "Content-Type: application/json" \
  -d '{"task":"process-report"}'
```
