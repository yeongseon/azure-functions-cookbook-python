# retry_and_idempotency

This recipe shows two related resilience patterns:

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
- function-level retry with `@app.retry(...)`
- idempotent queue handling with message deduplication IDs

## Retry behavior

- `scheduled_with_retry` has a function-level retry policy:
  - strategy: fixed delay
  - max retries: 3
  - delay: 5 seconds
- `host.json` also includes app-level retry defaults. Function decorators can override these.

## Idempotency behavior

- `queue_with_idempotency` reads messages from the `orders` queue
- expects payload like `{"id":"order-123","amount":42}`
- tracks IDs in `_seen_ids` and skips duplicates

## Run locally

```bash
cd examples/recipes/retry_and_idempotency
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```
