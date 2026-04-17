# cqrs_read_projection

CQRS sample for Azure Functions Python where:

- `POST /api/orders` writes the canonical document to Cosmos DB
- a Cosmos DB change feed trigger builds a projection
- `GET /api/orders/{id}/projection` reads the materialized view from a SQL-style store

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)
- Azure Cosmos DB account or emulator with database `ordersdb` and containers `orders` and `leases`
- SQLite CLI (or another database compatible with `azure-functions-db`)

## Files

- `function_app.py` - write API, projection function, and read API
- `schema.sql` - read model table definition
- `local.settings.json.example` - local configuration template

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
sqlite3 readmodels.db < schema.sql
func start
```

## Example Requests

Write an order:

```bash
curl -X POST http://localhost:7071/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-1001",
    "customer_id": "cust-42",
    "status": "confirmed",
    "items": [
      {"sku": "sku-1", "quantity": 1, "unit_price": 12.50},
      {"sku": "sku-2", "quantity": 2, "unit_price": 16.50}
    ]
  }'
```

Read the projection after the change feed runs:

```bash
curl http://localhost:7071/api/orders/order-1001/projection
```

## Expected Behavior

- The write API returns `202 Accepted`
- The change feed function writes a flattened row into `order_read_models`
- The read API returns the projected order summary from SQLite
