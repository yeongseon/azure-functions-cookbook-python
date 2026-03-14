# durable_retry_pattern

Durable Functions orchestration retrying a flaky activity.

## What It Demonstrates

- HTTP starter endpoint: `POST /api/start-retry`
- Orchestrator using `RetryOptions` with 5-second interval and 3 attempts
- Activity that intermittently fails to simulate transient errors

## Run Locally

```bash
cd examples/durable/durable_retry_pattern
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Start Example

```bash
curl -X POST "http://localhost:7071/api/start-retry"
```
