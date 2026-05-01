# Blob CSV to Table

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/blob-and-file-triggers/blob-csv-to-table/)

Event Grid-driven ingestion pattern that reads uploaded CSV blobs and writes normalized rows into Azure Table Storage.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azurite or Azure Storage account with blob and table endpoints

## Run Locally

```bash
cd examples/blob-and-file-triggers/blob_csv_to_table
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- New CSV uploads emit Event Grid notifications.
- Each parsed CSV row is upserted into the configured table.
