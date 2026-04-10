# DB Input and Output Bindings

## Overview
This recipe demonstrates declarative database read and write operations using
`azure-functions-db` input and output bindings.
The input binding injects query results directly into your handler.
The output binding accepts data via a `DbOut` helper — call `.set()` to write rows.

Both patterns avoid manual driver setup.
You declare the connection URL, table, and query in decorators,
and `azure-functions-db` handles engine creation, execution, and cleanup.

## When to Use
- You need CRUD endpoints backed by PostgreSQL, MySQL, or SQL Server.
- You want declarative data access without raw SQLAlchemy sessions in handlers.
- You want a FastAPI-like decorator experience on Azure Functions.

## Architecture
```text
+-------------+       GET /api/items         +-------------------+
|   Client    | ---------------------------> | list_items        |
| (curl/web)  |                              | @db.input(query)  |
+-------------+                              +---------+---------+
                                                       |
                                                       v
                                              +------------------+
                                              |  SQLAlchemy      |
                                              |  SELECT * FROM   |
                                              |  items           |
                                              +--------+---------+
                                                       |
                                                       v
                                              JSON response body

+-------------+      POST /api/items         +-------------------+
|   Client    | ---------------------------> | create_item       |
| (curl/web)  |                              | @db.output(table) |
+-------------+                              +---------+---------+
                                                       |
                                                       v
                                              +------------------+
                                              |  SQLAlchemy      |
                                              |  INSERT INTO     |
                                              |  items           |
                                              +--------+---------+
                                                       |
                                                       v
                                              201 Created
```

## Prerequisites
- Python 3.10+
- Azure Functions Core Tools v4
- `azure-functions-db[postgres]` (or `[mysql]`, `[mssql]`)
- A running database with an `items` table
- `DB_URL` app setting with a SQLAlchemy connection string

## Project Structure
```text
my-db-api/
|- function_app.py
|- host.json
|- local.settings.json.example
|- requirements.txt
`- README.md
```

## Implementation
Initialize `DbBindings` once and apply decorators to each handler.

**Read — list items with a SQL query:**

```python
import json

import azure.functions as func
from azure_functions_db import DbBindings

app = func.FunctionApp()
db = DbBindings()


@app.route(route="items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@db.input("items", url="%DB_URL%",
             query="SELECT * FROM items WHERE active = :active",
             params={"active": True})
def list_items(req: func.HttpRequest, items: list[dict]) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(items, default=str),
        mimetype="application/json",
    )
```

`@db.input` injects the query result as `items: list[dict]`.
The `%DB_URL%` syntax resolves from app settings at runtime.

**Read — single item by primary key:**

```python
@app.route(route="items/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@db.input("item", url="%DB_URL%", table="items",
             pk=lambda req: {"id": req.route_params["id"]})
def get_item(req: func.HttpRequest, item: dict | None) -> func.HttpResponse:
    if item is None:
        return func.HttpResponse("Not found", status_code=404)
    return func.HttpResponse(json.dumps(item, default=str), mimetype="application/json")
```

**Write — insert a new item:**

```python
from azure_functions_db import DbOut


@app.route(route="items", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@db.output("out", url="%DB_URL%", table="items")
def create_item(req: func.HttpRequest, out: DbOut) -> func.HttpResponse:
    body = req.get_json()
    out.set({"name": body["name"], "price": body["price"], "active": True})
    return func.HttpResponse("Created", status_code=201)
```

`@db.output` injects a `DbOut` instance. Call `out.set()` with a dict (single row)
or `list[dict]` (batch insert). The handler return value is independent of the write.

## Run Locally
```bash
cd my-db-api
pip install -r requirements.txt
func start
```

Set `DB_URL` in `local.settings.json`:

```json
{
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DB_URL": "postgresql+psycopg://user:pass@localhost:5432/mydb"
  }
}
```

## Expected Output
```text
GET /api/items
-> 200 [{"id": 1, "name": "Widget", "price": 9.99, "active": true}]

GET /api/items/1
-> 200 {"id": 1, "name": "Widget", "price": 9.99, "active": true}

POST /api/items {"name": "Gadget", "price": 19.99}
-> 201 Created
```

## Production Considerations
- Scaling: each function instance creates its own connection pool; monitor pool exhaustion under high concurrency.
- Retries: clients should retry on transient 5xx errors; writes should be idempotent (use upsert with `action="upsert"` and `conflict_columns`).
- Idempotency: accept client-supplied IDs or use natural keys to prevent duplicate inserts on retry.
- Observability: log request correlation IDs alongside query parameters and row counts.
- Connection pooling: `azure-functions-db` creates engines lazily; use `EngineProvider` when sharing connections across bindings.

## Scaffold Starter
```bash
afs new my-db-api --profile db-api
cd my-db-api
pip install -e .
func start
```

The `db-api` profile generates a project with openapi, validation, and db integrations pre-wired.

## Related Recipes
- [Hello HTTP Minimal](./hello-http-minimal.md)
- [Queue Producer](./queue-producer.md)
- [Output Binding vs SDK](./output-binding-vs-sdk.md)
