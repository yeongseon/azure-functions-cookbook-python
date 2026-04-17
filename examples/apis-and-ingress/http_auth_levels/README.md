# http_auth_levels

HTTP trigger example that demonstrates anonymous, function-key, and admin-key endpoints.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- `AuthLevel.ANONYMOUS` route with no key requirement
- `AuthLevel.FUNCTION` route requiring a function key
- `AuthLevel.ADMIN` route requiring the master/admin key

## Run Locally

```bash
cd examples/http/http_auth_levels
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl "http://localhost:7071/api/public"
```

```text
This endpoint is public (anonymous).
```
