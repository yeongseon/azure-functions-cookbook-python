"""Retry and idempotency patterns for Azure Functions triggers."""

from __future__ import annotations

import json
import logging

import azure.functions as func

app = func.FunctionApp()
_seen_ids: set[str] = set()


@app.function_name(name="scheduled_with_retry")
@app.schedule(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
@app.retry(strategy="fixed_delay", max_retry_count="3", delay_interval="00:00:05")
def scheduled_with_retry(timer: func.TimerRequest) -> None:
    """Run with a function-level fixed delay retry policy."""
    logging.info(
        "Timer fired. past_due=%s. This function retries up to 3 times every 5 seconds.",
        timer.past_due,
    )


@app.function_name(name="queue_with_idempotency")
@app.queue_trigger(
    arg_name="msg",
    queue_name="orders",
    connection="AzureWebJobsStorage",
)
def queue_with_idempotency(msg: func.QueueMessage) -> None:
    """Skip duplicate messages using an idempotency key check."""
    raw_body = msg.get_body().decode("utf-8")
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        logging.warning("Invalid JSON payload; skipping message: %s", raw_body)
        return

    dedupe_id = str(payload.get("id", "")).strip()
    if not dedupe_id:
        logging.warning("Missing id field; cannot apply idempotency. payload=%s", payload)
        return

    if dedupe_id in _seen_ids:
        logging.info("Duplicate message detected; skipping id=%s", dedupe_id)
        return

    _seen_ids.add(dedupe_id)
    logging.info("Processing idempotent message id=%s payload=%s", dedupe_id, payload)
