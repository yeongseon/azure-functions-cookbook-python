# change_feed_processor

Cosmos DB change feed-triggered Azure Function for downstream synchronization.

## What It Demonstrates

- `@app.cosmos_db_trigger` configuration with lease container support
- Iterating changed documents and logging per-document processing output
- Isolated `_process_change` helper for business workflow extension

## Run Locally

```bash
cd examples/cosmosdb/change_feed_processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Change feed batches log document counts and per-document processing status.
- Empty batches are handled gracefully with an informational log entry.
