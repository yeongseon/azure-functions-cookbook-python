# Output Binding vs SDK

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/runtime-and-ops/output-binding-vs-sdk/)

This recipe compares two ways to send the same queue message:

## Prerequisites

- Python 3.11+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- `enqueue_via_binding` uses `@app.queue_output`
- `enqueue_via_sdk` uses `azure.storage.queue.QueueClient`

Both endpoints accept `POST` JSON with an optional `task` field and enqueue to `work-items`.

## Wire encoding

Both producers write the same base64-encoded message text, matching the Azure
Functions Queue binding's default `messageEncoding` (`base64`, see
[host.json reference](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-queue#host-json)):

- `enqueue_via_binding` uses `@app.queue_output`, which base64-encodes the
  message text under the host's default `messageEncoding`.
- `enqueue_via_sdk` constructs `QueueClient` with an explicit
  `TextBase64EncodePolicy()`, so its raw JSON payload is base64-encoded the
  same way before being sent.

A queue consumer configured for the host's default `messageEncoding` can
decode either producer's message to the same original JSON.

## Why compare these patterns?

- output binding: less code, declarative, easier for straightforward scenarios
- SDK client: full API surface, advanced features, explicit runtime behavior

## Run locally

```bash
cd examples/runtime-and-ops/output_binding_vs_sdk
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
