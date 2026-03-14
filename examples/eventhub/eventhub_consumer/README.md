# eventhub_consumer

Event Hub-triggered Azure Function for near real-time telemetry stream processing.

## What It Demonstrates

- Event Hub trigger bound to `telemetry`
- Reading event body plus partition key, sequence number, and offset
- Telemetry helper function for stream transformation and logging

## Run Locally

```bash
cd examples/eventhub/eventhub_consumer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Logs include stream metadata (`partition_key`, `sequence_number`, `offset`).
- Telemetry payloads are processed and logged with a normalized status message.
