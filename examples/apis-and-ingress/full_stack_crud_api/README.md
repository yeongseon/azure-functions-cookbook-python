# Full Stack CRUD API

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/apis-and-ingress/full-stack-crud-api/)

Showcase HTTP API that wires the Azure Functions Python DX Toolkit together around one `items` resource.

## Toolkit Coverage

- `azure-functions-db-python` for shared SQLAlchemy engine/session management
- `azure-functions-validation-python` for query/body validation and response shaping
- `azure-functions-openapi-python` for endpoint metadata
- `azure-functions-logging-python` for structured telemetry
- `azure-functions-doctor-python` as the recommended environment and dependency health check before deploy
- `azure-functions-scaffold-python` as the fastest way to generate the starting project skeleton this example builds on

## Files

```text
full_stack_crud_api/
├── function_app.py
├── host.json
├── local.settings.json.example
├── models.py
├── README.md
└── pyproject.toml
```

## Endpoints

- `GET /api/items?page=1&page_size=20` — list items with pagination
- `GET /api/items/{id}` — fetch one item
- `POST /api/items` — create an item
- `PUT /api/items/{id}` — replace an item
- `DELETE /api/items/{id}` — delete an item

## Run Locally

```bash
cd examples/apis-and-ingress/full_stack_crud_api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

The sample uses SQLite by default and auto-creates the `items` table on startup.

## Example Requests

```bash
curl -X POST http://localhost:7071/api/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","description":"Starter item","price":9.99}'

curl "http://localhost:7071/api/items?page=1&page_size=20"

curl http://localhost:7071/api/items/1

curl -X PUT http://localhost:7071/api/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget Pro","description":"Updated item","price":19.99}'

curl -X DELETE http://localhost:7071/api/items/1 -i
```

## Adjacent Toolkit Workflow

- Run `azure-functions-doctor-python` before deployment to catch missing settings, packaging issues, and runtime mismatches.
- Use `azure-functions-scaffold-python` when you want to generate a new Azure Functions project and then apply this CRUD recipe pattern.
