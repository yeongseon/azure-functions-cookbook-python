# etl_enrichment

Blob-triggered ETL example that reads raw JSON customer records, enriches them with lookup data, and writes the enriched rows to a database.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) for local blob storage
- A database reachable through `DB_URL`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AzureWebJobsStorage` | Storage account for the blob trigger | `UseDevelopmentStorage=true` |
| `DB_URL` | Destination database URL used by `azure-functions-db` | `postgresql://postgres:postgres@localhost:5432/appdb` |

Copy `local.settings.json.example` to `local.settings.json` and fill in the values.

## What It Demonstrates

- Blob-triggered ETL with `@app.blob_trigger`
- JSON extraction and field normalization
- Deterministic enrichment using reference lookups
- Structured logging with `azure-functions-logging`
- Database output binding with `azure-functions-db`

## Run Locally

```bash
cd examples/data-and-pipelines/etl_enrichment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

Upload a JSON file to the `raw-data` container.

Example payload:

```json
[
  {"customer_id": "cust-1001", "city": "Seattle", "country_code": "US"},
  {"customer_id": "cust-1002", "city": "Berlin", "country_code": "DE"},
  {"customer_id": "cust-1003", "city": "Tokyo", "country_code": "JP"}
]
```

## Expected Output

- Logs show extraction, per-record enrichment, and load completion.
- The `enriched_customers` table receives one row per source record.
- Unknown country codes fall back to default enrichment metadata instead of failing the batch.
