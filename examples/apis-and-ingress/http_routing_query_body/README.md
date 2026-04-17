# http_routing_query_body

HTTP CRUD and search example showing route params, query strings, JSON body parsing, and status codes.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- `GET /api/users`, `GET /api/users/{user_id}` for list and lookup
- `POST`, `PUT`, and `DELETE` endpoints with standard REST status codes
- JSON request body validation and JSON response helper usage
- Query-string search with `q` and `limit`

## Run Locally

```bash
cd examples/http/http_routing_query_body
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl "http://localhost:7071/api/users"
```

```json
{"users":[{"id":"1","name":"Ada Lovelace","email":"ada@example.com"},{"id":"2","name":"Grace Hopper","email":"grace@example.com"}]}
```
