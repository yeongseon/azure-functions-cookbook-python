from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp()


def _load_schedule() -> list[dict[str, object]]:
    raw = os.getenv(
        "SCHEDULED_DISPATCHES_JSON",
        '[{"job_id":"dispatch-100","scheduled_for":"2026-04-17T12:00:00+00:00","destination":"reminder-emails","payload":{"recipient":"ada@example.com"}}]',
    )
    loaded = json.loads(raw)
    return loaded if isinstance(loaded, list) else []


@app.function_name(name="dispatch_due_messages")
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
@app.queue_output(
    arg_name="outbox", queue_name="scheduled-dispatch", connection="AzureWebJobsStorage"
)
@with_context
def dispatch_due_messages(timer: func.TimerRequest, outbox: func.Out[str], context: func.Context) -> None:
    now = datetime.now(timezone.utc)
    due_messages: list[dict[str, object]] = []

    for item in _load_schedule():
        scheduled_for = datetime.fromisoformat(str(item["scheduled_for"]))
        if scheduled_for <= now:
            due_messages.append(
                {
                    "job_id": item["job_id"],
                    "destination": item["destination"],
                    "payload": item["payload"],
                    "dispatched_at": now.isoformat(),
                }
            )

    if due_messages:
        outbox.set(json.dumps(due_messages[0] if len(due_messages) == 1 else due_messages))

    logger.info(
        "Scheduled dispatch run complete",
        extra={
            "past_due": timer.past_due,
            "due_count": len(due_messages),
            "schedule_source": "storage-queue-visibility-timeout",
        },
    )
