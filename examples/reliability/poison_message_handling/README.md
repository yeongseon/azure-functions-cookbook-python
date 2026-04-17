# poison_message_handling

Queue-triggered Azure Functions recipe that lets repeated failures move automatically to the poison
queue and then logs the failed payload for operator follow-up.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) or an Azure Storage account

## What It Demonstrates

- Queue trigger processing for the `orders` queue
- Deliberate repeated failure with `should_fail=true`
- Automatic move to the `orders-poison` queue after `maxDequeueCount` is exhausted
- Poison queue monitoring with logging-only alert behavior

## Local Settings

- `AzureWebJobsStorage`: storage connection used by the queue trigger and poison queue trigger
- `FUNCTIONS_WORKER_RUNTIME`: set to `python`

## Run Locally

```bash
cd examples/reliability/poison_message_handling
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Sample Messages

Success:

```json
{"order_id": "A100", "should_fail": false}
```

Poison-message demo:

```json
{"order_id": "A200", "should_fail": true}
```

## Expected Output

- Successful messages are logged once by `queue_processor`.
- Failing messages are retried three times.
- After retries are exhausted, `poison_handler` logs the payload from `orders-poison`.
