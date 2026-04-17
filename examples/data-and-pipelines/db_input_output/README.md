# DB Input and Output Example

Demonstrates `azure-functions-db` input/output bindings with SQLAlchemy-backed storage,
combined with `azure-functions-validation` and `azure-functions-openapi`.

## Run

```bash
pip install -r requirements.txt
cp local.settings.sample.json local.settings.json
func start
```

## Endpoints

- `GET /api/items` — list all items
- `POST /api/items` — create an item (JSON body: `{"name": "...", "category": "...", "price": 9.99}`)
