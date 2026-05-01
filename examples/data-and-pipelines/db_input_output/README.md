# DB Input and Output Bindings

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/data-and-pipelines/db-input-output/)

Demonstrates `azure-functions-db-python` input/output bindings with SQLAlchemy-backed storage,
combined with `azure-functions-validation-python` and `azure-functions-openapi-python`.

## Run

```bash
pip install -e ".[dev]"
cp local.settings.sample.json local.settings.json
func start
```

## Endpoints

- `GET /api/items` — list all items
- `POST /api/items` — create an item (JSON body: `{"name": "...", "category": "...", "price": 9.99}`)
