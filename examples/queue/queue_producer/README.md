# queue_producer

HTTP-triggered Azure Function that validates JSON and enqueues tasks to Storage Queue.

## What It Demonstrates

- HTTP POST endpoint at `/api/enqueue`
- Queue output binding to `outbound-tasks`
- Payload validation and `202 Accepted` response with generated `message_id`

## Run Locally

```bash
cd examples/queue/queue_producer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

```bash
curl -X POST "http://localhost:7071/api/enqueue" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"email","payload":{"to":"user@example.com"}}'
```

- Response includes `status=accepted` and a generated `message_id`.
- Queue message is written to `outbound-tasks` in Azurite or your configured storage account.
