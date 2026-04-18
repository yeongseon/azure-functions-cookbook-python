# claim_check_pattern

Large-message pattern that stores payloads in Blob Storage and passes only a reference through the queue.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azurite or Azure Storage account with queue and blob support

## Run Locally

```bash
cd examples/messaging-and-pubsub/claim_check_pattern
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- `POST /api/claim-check/enqueue` stores the large payload in Blob Storage and queues a claim reference.
- The queue-triggered worker reads the referenced blob and processes the full payload.
