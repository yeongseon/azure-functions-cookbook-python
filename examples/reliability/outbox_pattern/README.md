# Outbox Pattern

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/reliability/outbox-pattern/)

Transactional outbox sample for Azure Functions Python where:

- `POST /api/outbox/orders` stores the order document and an outbox event in one Cosmos DB transactional batch
- a Cosmos DB change feed trigger relays only the outbox documents
- `azure-functions-db-python` records relay audit rows in SQLite while structured logs show the broker handoff

## Prerequisites

- Python 3.11+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- Azure Cosmos DB account or emulator with database `outboxdb` and containers `orders` and `leases`
- SQLite CLI, or another `azure-functions-db-python` compatible database

## Files

- `function_app.py` - HTTP write function and Cosmos DB change feed relay
- `local.settings.json.example` - local configuration template
- `host.json` - Azure Functions host configuration

## Run locally

```bash
cd examples/reliability/outbox_pattern
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
sqlite3 relay.db "CREATE TABLE IF NOT EXISTS outbox_dispatches (event_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, event_type TEXT NOT NULL, broker_name TEXT NOT NULL, dispatched_at TEXT NOT NULL, status TEXT NOT NULL);"
func start
```

## Example request

```bash
curl -X POST http://localhost:7071/api/outbox/orders \
  -H "Content-Type: application/json" \
  -d '{
    "id": "order-1001",
    "customer_id": "cust-42",
    "amount": 149.95,
    "currency": "USD"
  }'
```

## Expected behavior

- the HTTP endpoint returns `202 Accepted` after the transactional batch succeeds
- the change feed relay ignores `order` documents and relays only `outbox` documents
- the relay writes an audit row into `outbox_dispatches` for each published event
- redelivering an already-processed outbox event (the Cosmos DB change feed processor
  delivers at-least-once) does not raise or duplicate its audit row -- the audit write
  upserts on `event_id`, so a replayed batch keeps recording any genuinely new events
  alongside the already-seen one

## Notes

- Keep both documents in the same logical partition or the transactional batch will not be atomic.
- The sample publishes to a logging-based broker boundary; replace that step with Service Bus or another broker in production.
- The audit write is idempotent per `event_id`, but the broker handoff itself is **not** exactly-once:
  the change feed's at-least-once delivery means `_publish_to_broker` can be called again for an
  event whose audit row already exists. This recipe does not promise exactly-once publication --
  only that redelivery cannot corrupt the audit trail with a permanent key conflict.
- For Azure guidance, see [Transactional outbox](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transactional-outbox-cosmos).
