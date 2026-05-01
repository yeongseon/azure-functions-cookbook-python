# Queue-Backed Job

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/async-apis-and-jobs/queue-backed-job/)

HTTP + Storage Queue recipe for accepting a job, returning `202 Accepted`, and polling a stored status record.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or an Azure Storage account

Create the queue and blob container used by the sample before starting:

- Queue: `job-requests`
- Blob container: `job-status`

## What It Demonstrates

- HTTP POST endpoint at `/api/jobs`
- Input validation, OpenAPI metadata, and structured logging on the submission API
- Queue output binding for background job dispatch
- Queue-triggered worker for asynchronous processing
- HTTP GET polling endpoint at `/api/jobs/{job_id}` backed by blob-stored job status

## Run Locally

```bash
cd examples/async-apis-and-jobs/queue_backed_job
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Example Request

```bash
curl -X POST "http://localhost:7071/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"thumbnail","customer_id":"cust-123","payload":{"asset_url":"https://example.invalid/image.png"}}'
```

The response includes `job_id` and `status_url`. Poll that URL until the job reaches `completed`.

```bash
curl "http://localhost:7071/api/jobs/<job-id>"
```
