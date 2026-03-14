from __future__ import annotations

import json
import logging

import azure.functions as func

from app.services.idempotency_service import is_duplicate, mark_processed

retry_blueprint = func.Blueprint()


@retry_blueprint.function_name(name="scheduled_with_retry")
@retry_blueprint.schedule(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
@retry_blueprint.retry(strategy="fixed_delay", max_retry_count="3", delay_interval="00:00:05")
def scheduled_with_retry(timer: func.TimerRequest) -> None:
    logging.info(
        "Timer fired. past_due=%s. This function retries up to 3 times every 5 seconds.",
        timer.past_due,
    )


@retry_blueprint.function_name(name="queue_with_idempotency")
@retry_blueprint.queue_trigger(
    arg_name="msg",
    queue_name="orders",
    connection="AzureWebJobsStorage",
)
def queue_with_idempotency(msg: func.QueueMessage) -> None:
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

    if is_duplicate(dedupe_id):
        logging.info("Duplicate message detected; skipping id=%s", dedupe_id)
        return

    mark_processed(dedupe_id)
    logging.info("Processing idempotent message id=%s payload=%s", dedupe_id, payload)
