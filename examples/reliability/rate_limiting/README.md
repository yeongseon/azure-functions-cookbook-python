# Rate Limiting / Throttle

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/reliability/rate-limiting-throttle/)

This recipe shows an HTTP-triggered Azure Function using an in-memory token bucket to throttle
requests and return `429 Too Many Requests` when the local bucket is empty.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)

## Behavior

- each request consumes one token from the bucket
- tokens refill continuously at `RATE_LIMIT_REFILL_PER_SECOND`
- the bucket cannot grow past `RATE_LIMIT_CAPACITY`
- when no token is available, the function returns `429` and a `Retry-After` header

## Run locally

```bash
cd examples/reliability/rate_limiting
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Try it

Consume available tokens:

```bash
for i in 1 2 3 4 5; do
  curl "http://localhost:7071/api/rate-limit?client_id=demo"
  printf "\n"
done
```

Trigger throttling:

```bash
curl -i "http://localhost:7071/api/rate-limit?client_id=demo"
```

Wait for refill, then try again:

```bash
sleep 2
curl "http://localhost:7071/api/rate-limit?client_id=demo"
```

## Notes

- This sample uses one in-memory bucket for readability, so limits are per-process rather than shared.
- For production, move the counter to Redis, Durable Entities, Cosmos DB, or Azure API Management when limits must be consistent across instances.
- For gateway-level throttling patterns, see [API Management flexible throttling](https://learn.microsoft.com/en-us/azure/api-management/api-management-sample-flexible-throttling).
