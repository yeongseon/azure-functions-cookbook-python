# durable_singleton_monitor

Durable Functions singleton orchestration that continuously polls an external dependency and emits alerts on changes.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Storage account or Azurite for Durable task state

## Run Locally

```bash
cd examples/orchestration-and-workflows/durable_singleton_monitor
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- `POST /api/monitor/start` ensures the singleton orchestration exists.
- The timer starter keeps the singleton alive and the orchestrator polls every 5 minutes.
