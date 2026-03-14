# servicebus_worker

Service Bus queue-triggered Azure Function for reliable background work consumption.

## What It Demonstrates

- Service Bus queue trigger bound to `tasks`
- Message parsing with `correlation_id` and `delivery_count` logging
- Processing helper function and dead-letter handling guidance

## Run Locally

```bash
cd examples/servicebus/servicebus_worker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Each message logs correlation and delivery metadata, then processing status.
- Invalid JSON payloads are logged as errors and can be investigated for DLQ handling.
