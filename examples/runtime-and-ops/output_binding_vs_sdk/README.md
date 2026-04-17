# output_binding_vs_sdk

This recipe compares two ways to send the same queue message:

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- `enqueue_via_binding` uses `@app.queue_output`
- `enqueue_via_sdk` uses `azure.storage.queue.QueueClient`

Both endpoints accept `POST` JSON with an optional `task` field and enqueue to `work-items`.

## Why compare these patterns?

- output binding: less code, declarative, easier for straightforward scenarios
- SDK client: full API surface, advanced features, explicit runtime behavior

## Run locally

```bash
cd examples/recipes/output_binding_vs_sdk
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Try both

```bash
curl -X POST http://localhost:7071/api/enqueue/binding -H "Content-Type: application/json" \
  -d '{"task":"process-report"}'
curl -X POST http://localhost:7071/api/enqueue/sdk -H "Content-Type: application/json" \
  -d '{"task":"process-report"}'
```
