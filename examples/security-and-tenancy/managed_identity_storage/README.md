# managed_identity_storage

This recipe shows an Azure Storage Queue trigger using `connection="StorageConnection"`.
You can back that setting with either a connection string or managed identity settings.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- An Azure Storage account (Azurite does not support identity-based connections)

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `StorageConnection` | Storage connection string (classic) | `DefaultEndpointsProtocol=https;AccountName=<account>;AccountKey=<key>;EndpointSuffix=core.windows.net` |
| `StorageConnection__queueServiceUri` | Queue endpoint for managed identity | `https://<account>.queue.core.windows.net` |

Use **either** `StorageConnection` (connection string) **or** `StorageConnection__queueServiceUri` (managed identity), not both.

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## Connection Setting Patterns

- Connection string pattern:
  - `StorageConnection="DefaultEndpointsProtocol=https;..."`
- Managed identity pattern:
  - `StorageConnection__queueServiceUri="https://<account>.queue.core.windows.net"`

The `__queueServiceUri` suffix tells the Functions host to resolve an identity-based queue endpoint
instead of reading a connection string.

## Run Locally

```bash
cd examples/recipes/managed_identity_storage
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Queue messages on `identity-tasks` trigger the function and log processing status.
- When using managed identity, ensure the identity has **Storage Queue Data Contributor** role.
