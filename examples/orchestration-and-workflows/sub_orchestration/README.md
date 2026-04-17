# sub_orchestration

Durable Functions parent orchestration delegating work to two child sub-orchestrators.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-sub-orchestration`
- Parent orchestrator calling `customer_sync_sub_orchestrator` and `inventory_sync_sub_orchestrator`
- Activity-level structured logging with `azure-functions-logging`
- Final parent result that aggregates both child workflow outputs

## Run Locally

```bash
cd examples/orchestration-and-workflows/sub_orchestration
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-sub-orchestration" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-2001","customer_segment":"partner","skus":["SKU-10","SKU-20","SKU-30"]}'
```

## Expected Result

- The parent orchestrator starts and waits for both child sub-orchestrators.
- `sync_customer_profile` and `build_inventory_snapshot` run as child-owned activity work.
- The final status payload includes the parent instance ID plus both child results.
