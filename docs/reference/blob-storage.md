# Blob Storage Trigger, Input, and Output Bindings

Blob Storage bindings are useful for file-centric workflows such as ingest, transform, and archive. Blob triggers can run through classic polling or via Event Grid-backed source modes, which changes latency and scale behavior significantly.

## Trigger

Use `@app.blob_trigger(...)` for blob-created or blob-updated events.

Key parameters: `path`, `connection`, `arg_name`, and optional `source` for Event Grid-backed processing.

```python
import azure.functions as func

app = func.FunctionApp()

@app.blob_trigger(arg_name="blob", path="incoming/{name}", connection="AzureWebJobsStorage")
def blob_example(blob: func.InputStream) -> None:
    print(f"name={blob.name} length={blob.length}")
```

For lower-latency accounts that support it, set `source="EventGrid"` to use Event Grid notifications instead of container polling.

## Input Binding

Blob input bindings are common for HTTP, queue, and timer handlers that need file contents by path.

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="artifacts/{name}", methods=["GET"])
@app.blob_input(arg_name="artifact", path="incoming/{name}", connection="AzureWebJobsStorage")
def get_artifact(req: func.HttpRequest, artifact: bytes) -> func.HttpResponse:
    return func.HttpResponse(body=artifact, mimetype="application/octet-stream")
```

## Output Binding

Use blob output when the function produces a new file artifact.

```python
import azure.functions as func

app = func.FunctionApp()

@app.blob_trigger(arg_name="blob", path="incoming/{name}", connection="AzureWebJobsStorage")
@app.blob_output(arg_name="output_blob", path="processed/{name}", connection="AzureWebJobsStorage")
def normalize_blob(blob: func.InputStream, output_blob: func.Out[bytes]) -> None:
    output_blob.set(blob.read().upper())
```

## Configuration

Blob polling behavior is controlled in `host.json` for classic blob triggers:

```json
{
  "version": "2.0",
  "extensions": {
    "blobs": {
      "maxDegreeOfParallelism": 4,
      "poisonBlobThreshold": 5
    }
  }
}
```

`local.settings.json` usually needs `AzureWebJobsStorage` or another named storage connection. Event Grid-backed blob triggers also require the storage account to publish blob events.

## Scaling Behavior

Polling-based blob triggers scan containers and leases, so latency is usually higher than queues. Event Grid-backed blob triggers reduce detection delay and scale more like Event Grid subscriptions. Either way, each invocation processes one blob, and duplicate processing is possible if retries occur before downstream writes are idempotent.

## Common Pitfalls

- Blob triggers do not give you strong once-only semantics; write outputs to deterministic paths or include idempotency checks.
- Large blobs should be streamed from `InputStream`; reading everything into memory can spike worker RAM.
- Polling-based blob triggers are not near-real-time and can surprise teams expecting instant execution.

## Related Patterns

- [Blob Upload Processor](../patterns/blob-and-file-triggers/blob-upload-processor.md)
- [Blob Event Grid Trigger](../patterns/blob-and-file-triggers/blob-eventgrid-trigger.md)
- [Managed Identity Storage](../patterns/security-and-tenancy/managed-identity-storage.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-blob-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-blob-output?pivots=programming-language-python&tabs=python-v2
