# saga_compensation

Durable Functions saga orchestration that compensates previously completed steps on failure.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-saga-compensation`
- Sequential orchestration for inventory reservation, payment capture, and confirmation delivery
- Compensation flow that refunds payment and releases inventory when a later step fails
- Structured logging via `azure-functions-logging-python` and DB-ready audit metadata via `azure-functions-db-python`

## Run Locally

```bash
cd examples/orchestration-and-workflows/saga_compensation
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Start Example

Successful saga:

```bash
curl -X POST "http://localhost:7071/api/start-saga-compensation" \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-2001","sku":"demo-widget","quantity":1,"amount":59.99,"email":"buyer@example.com"}'
```

Force compensation by failing the confirmation step:

```bash
curl -X POST "http://localhost:7071/api/start-saga-compensation" \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-2002","fail_confirmation":true}'
```

## Expected Result

- Success path completes with `reserve_inventory`, `charge_payment`, `send_confirmation`, and `record_saga_audit`.
- Failure path returns a compensated result after `refund_payment`, `release_inventory`, and `record_saga_audit` run.
