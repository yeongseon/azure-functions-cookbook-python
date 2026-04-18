# SQLAlchemy REST Pagination Example

HTTP API example that combines:

- `azure-functions-db-python` for shared engine management
- SQLAlchemy ORM for the `Item` model and paginated queries
- `azure-functions-validation-python` for request/query validation
- `azure-functions-openapi-python` for API documentation metadata
- `azure-functions-logging-python` for structured logs

## Files

```text
sqlalchemy_rest_pagination/
|-- function_app.py
|-- host.json
|-- local.settings.json.example
|-- models.py
|-- README.md
`-- pyproject.toml
```

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

The sample uses SQLite by default and creates the `items` table on startup.

## Endpoints

- `GET /api/items?page=1&page_size=20` — list items with offset pagination
- `POST /api/items` — create an item

## Example Requests

```bash
curl -X POST http://localhost:7071/api/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","price":9.99}'

curl "http://localhost:7071/api/items?page=1&page_size=20"
```
