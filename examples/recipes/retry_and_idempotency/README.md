# retry_and_idempotency

This recipe shows two related resilience patterns:

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
pip install -r requirements.txt
func start
```
