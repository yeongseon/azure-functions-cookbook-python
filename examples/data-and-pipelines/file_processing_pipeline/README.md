# file_processing_pipeline

Blob-triggered Azure Function that validates uploaded CSV or JSON files, transforms the records, and persists the processed result to a database.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for local blob storage
- A database reachable through the `DB_URL` consumed by `azure-functions-db`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AzureWebJobsStorage` | Storage account for the blob trigger | `UseDevelopmentStorage=true` |
| `DB_URL` | Target database for processed file records | `postgresql://postgres:postgres@localhost:5432/appdb` |

Copy `local.settings.json.example` to `local.settings.json` and fill in the values.

## What It Demonstrates

- `@app.blob_trigger(..., source=func.BlobSource.EVENT_GRID)` for Event Grid-backed blob activation
- Validation for required `id`, `category`, and `amount` fields in CSV and JSON payloads
- Record normalization plus summary generation before persistence
- Structured logging with `azure-functions-logging`
- Database output binding with `azure-functions-db`

## Run Locally

```bash
cd examples/data-and-pipelines/file_processing_pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

Upload a file to the `incoming` container.

Example CSV:

```text
id,category,amount
order-1001,Retail,19.95
order-1002,Wholesale,40.00
```

Example JSON:

```json
[
  {"id": "order-1001", "category": "Retail", "amount": 19.95},
  {"id": "order-1002", "category": "Wholesale", "amount": 40.0}
]
```

## Expected Output

- Logs show the start, validation, transformation, and persistence stages.
- The `processed_files` table receives one record per successfully processed blob.
- Invalid files raise validation errors and are retried according to Azure Functions behavior.
