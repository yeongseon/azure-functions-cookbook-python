# Queue Scheduled Dispatch

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/scheduled-and-background/queue-scheduled-dispatch/)

Timer-driven scheduled dispatch pattern that releases due work onto Azure Storage Queue for downstream workers.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azurite or an Azure Storage account with queue support

## Run Locally

```bash
cd examples/scheduled-and-background/queue_scheduled_dispatch
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Every 5 minutes the timer evaluates scheduled items.
- Due items are written to the `scheduled-dispatch` queue for at-least-once downstream processing.
