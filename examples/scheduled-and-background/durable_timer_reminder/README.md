# Durable Timer Reminder

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/scheduled-and-background/durable-timer-reminder/)

Durable Functions orchestration that waits for a long delay and then executes a reminder callback activity.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Storage account or Azurite for Durable task state

## Run Locally

```bash
cd examples/scheduled-and-background/durable_timer_reminder
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

Start a reminder:

```bash
curl -X POST http://localhost:7071/api/reminders/start \
  -H "Content-Type: application/json" \
  -d '{"recipient":"ada@example.com","subject":"Trial expiry","delay_days":7}'
```

## Expected Output

- The HTTP endpoint returns `202 Accepted` with a Durable status URL.
- After the durable timer completes, the activity logs the reminder delivery step.
