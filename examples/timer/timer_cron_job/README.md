# timer_cron_job

Timer-triggered Azure Function that runs a scheduled maintenance job every 5 minutes.

## What It Demonstrates

- NCRONTAB schedule expression with six fields (`0 */5 * * * *`)
- Past-due detection via `timer.past_due`
- Extracting UTC timestamps and structured logging for scheduled execution

## Run Locally

```bash
cd examples/timer/timer_cron_job
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Every 5 minutes, the function logs a maintenance message with the current UTC timestamp.
- If local runtime was paused, a past-due warning appears before normal completion logs.
