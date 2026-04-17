# change_feed_processor

Cosmos DB change feed-triggered Azure Function for downstream synchronization.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- An Azure Cosmos DB account (or [Cosmos DB emulator](https://learn.microsoft.com/azure/cosmos-db/how-to-develop-emulator)) with a database `demodb` and containers `items` and `leases`

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `CosmosDBConnection` | Cosmos DB connection string | `AccountEndpoint=https://<account>.documents.azure.com:443/;AccountKey=<key>;` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- `@app.cosmos_db_trigger` configuration with lease container support
- Iterating changed documents and logging per-document processing output
- Isolated `_process_change` helper for business workflow extension

## Run Locally

```bash
cd examples/cosmosdb/change_feed_processor
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Change feed batches log document counts and per-document processing status.
- Empty batches are handled gracefully with an informational log entry.
