# Async Job Lifecycle

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/orchestration-and-workflows/async-job-lifecycle/)

Durable Functions recipe for full async job lifecycle management: create, status, cancel, and purge.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or an Azure Storage account

## What It Demonstrates

- `POST /api/jobs` starts a Durable Functions orchestration
- Durable management URLs are returned in the `202 Accepted` payload
- `GET /api/jobs/{instance_id}` projects Durable runtime status into `pending`, `running`, `completed`, `failed`, or `cancelled`
- `DELETE /api/jobs/{instance_id}` requests cancellation
- `DELETE /api/jobs/{instance_id}/history` purges terminal instance history
- Validation, OpenAPI metadata, and structured logging on the HTTP control plane

## Run Locally

```bash
cd examples/orchestration-and-workflows/async_job_lifecycle
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Requests

Create a job:

```bash
curl -X POST "http://localhost:7071/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"render-invoice","customer_id":"cust-123","duration_seconds":10,"should_fail":false}'
```

Check job status:

```bash
curl "http://localhost:7071/api/jobs/<instance_id>"
```

Cancel a running job:

```bash
curl -X DELETE "http://localhost:7071/api/jobs/<instance_id>?reason=client-requested"
```

Purge a terminal job:

```bash
curl -X DELETE "http://localhost:7071/api/jobs/<instance_id>/history"
```

You can also call the returned Durable `statusQueryGetUri`, `terminatePostUri`, and `purgeHistoryDeleteUri` directly.
