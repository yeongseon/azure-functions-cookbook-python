# managed_identity_storage

This recipe shows an Azure Storage Queue trigger using `connection="StorageConnection"`.

You can back that setting with either a connection string or managed identity settings.

## Connection setting patterns

- Connection string pattern:
  - `StorageConnection="DefaultEndpointsProtocol=https;..."`
- Managed identity pattern:
  - `StorageConnection__queueServiceUri="https://<account>.queue.core.windows.net"`

The `__queueServiceUri` suffix tells the Functions host to resolve an identity-based queue endpoint
instead of reading a connection string.

## Run locally

```bash
pip install -r requirements.txt
func start
```
