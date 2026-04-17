# async_http_polling

HTTP-triggered Durable Functions example that returns `202 Accepted` and a `statusQueryGetUri` for client polling.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or an Azure Storage account

## What It Demonstrates

- HTTP starter endpoint at `/api/jobs/reports`
- Durable orchestration started from an HTTP request
- `202 Accepted` response with `statusQueryGetUri`
- Logging, request validation, and OpenAPI metadata on the starter function

## Run Locally

```bash
cd examples/async-apis-and-jobs/async_http_polling
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Example Request

```bash
curl -X POST "http://localhost:7071/api/jobs/reports" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-123","operation":"rebuild-report","delay_seconds":5}'
```

Poll the returned `statusQueryGetUri` until `runtimeStatus` becomes `Completed`.
