# File Processing Pipeline

> **Trigger**: Blob (Event Grid) | **State**: stateless | **Guarantee**: at-least-once | **Difficulty**: intermediate

## Overview
The `examples/data-and-pipelines/file_processing_pipeline/` sample shows a multi-stage blob processing
pipeline where an uploaded CSV or JSON file triggers validation, transformation, and persistence to a
database. The function uses Event Grid-backed blob notifications for low-latency activation,
`azure-functions-logging-python` for structured telemetry, and `azure-functions-db-python` to write the processed
result to a downstream table.

This recipe is a strong fit for ingestion workflows where files arrive asynchronously and need a clear,
repeatable pipeline before they become queryable application data.

## When to Use
- You ingest CSV or JSON files into a storage container and need automated processing.
- You want lightweight, stateless stage execution inside a single Azure Function invocation.
- You need structured logs plus a normalized database record for each successfully processed file.
- Your downstream writes can be made replay-safe for at-least-once delivery.

## When NOT to Use
- Processing requires human approval or long-running orchestration between stages.
- Files are too large for single-invocation parsing and should be chunked or fan-out processed.
- The downstream database cannot tolerate duplicate writes or replay without idempotency keys.
- You need synchronous client feedback before persistence completes.

## Architecture
```mermaid
flowchart LR
    upload[Upload CSV / JSON file] --> blob[Blob Storage container]
    blob --> trigger[Blob Trigger<br/>source=Event Grid]
    trigger --> validate[Validate schema and values]
    validate --> transform[Transform into normalized records]
    transform --> persist[Persist with azure-functions-db-python]
    persist --> db[(Application DB)]
    trigger -. telemetry .-> logging[azure-functions-logging-python]
```

## Behavior
```mermaid
sequenceDiagram
    participant U as Uploader
    participant B as Blob Storage
    participant F as file_processing_pipeline
    participant D as Database

    U->>B: Upload CSV / JSON file
    B->>F: Fire Event Grid-backed blob trigger
    F->>F: Read payload and detect file type
    F->>F: Validate required fields and value types
    F->>F: Transform rows into normalized output
    F->>D: Persist processed summary and rows
    F-->>B: Invocation completes
```

## Implementation
The example uses a blob trigger configured with `source=func.BlobSource.EVENT_GRID` so the runtime is
activated by Event Grid notifications instead of blob polling.

```python
@app.blob_trigger(
    arg_name="myblob",
    path="incoming/{name}",
    connection="AzureWebJobsStorage",
    source=func.BlobSource.EVENT_GRID,
)
@db.output("out", url="%DB_URL%", table="processed_files")
def process_uploaded_file(myblob: func.InputStream, out: DbOut) -> None:
    ...
```

Inside the invocation, the pipeline executes three explicit stages:

1. **Validate**: parse CSV or JSON, require `id`, `category`, and `amount`, and reject empty/invalid files.
2. **Transform**: normalize categories, coerce numeric amounts, and compute file-level summary fields.
3. **Persist**: write one processed-file record to the configured database table.

Structured logging surrounds the stages so each invocation emits searchable metadata such as blob name,
record counts, and persisted row identifiers.

## Project Structure
```text
examples/data-and-pipelines/file_processing_pipeline/
|-- function_app.py
|-- host.json
|-- local.settings.json.example
|-- pyproject.toml
`-- README.md
```

## Config
Set these values in `local.settings.json` when running locally:

| Variable | Purpose | Example |
|----------|---------|---------|
| `AzureWebJobsStorage` | Storage account used by the blob trigger | `UseDevelopmentStorage=true` |
| `FUNCTIONS_WORKER_RUNTIME` | Azure Functions language worker | `python` |
| `DB_URL` | Connection string or URL consumed by `azure-functions-db-python` | `postgresql://postgres:postgres@localhost:5432/appdb` |

Use an `incoming` blob container for uploaded files such as `orders.csv` or `orders.json`.

## Run Locally
```bash
cd examples/data-and-pipelines/file_processing_pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Then upload a file into the `incoming` container.

Example JSON payload:

```json
[
  {"id": "order-1001", "category": "Retail", "amount": 19.95},
  {"id": "order-1002", "category": "Wholesale", "amount": 40.0}
]
```

## Expected Output
```text
[Information] Blob pipeline started blob_name=incoming/orders.json size_bytes=118
[Information] File validated blob_name=incoming/orders.json record_count=2
[Information] File transformed blob_name=incoming/orders.json normalized_count=2 total_amount=59.95
[Information] Blob pipeline completed blob_name=incoming/orders.json persisted_id=<uuid>
```

## Production Considerations
- **Idempotency**: include blob name, ETag, or content hash in the persisted record to avoid duplicate side effects.
- **Schema evolution**: version file formats explicitly when adding or renaming columns.
- **Large files**: move to chunked parsing or queue-based fan-out when files exceed single-invocation memory limits.
- **Observability**: log validation failures, transformation counts, and persistence latency with consistent fields.
- **Security**: restrict storage and database access with managed identity, private networking, and least privilege.

## Related Links
- [Blob trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger)
- [DB Input Output](./db-input-output.md)
- [Retry and Idempotency](../reliability/retry-and-idempotency.md)
