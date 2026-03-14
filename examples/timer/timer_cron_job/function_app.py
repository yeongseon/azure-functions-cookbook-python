"""Timer-triggered scheduled job with NCRONTAB expression."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

import azure.functions as func

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def scheduled_cleanup(timer: func.TimerRequest) -> None:
    """Run maintenance every 5 minutes.

    The NCRONTAB expression ``0 */5 * * * *`` uses six fields:
    {second} {minute} {hour} {day} {month} {day-of-week}.
    """
    utc_now = datetime.now(tz=timezone.utc).isoformat()

    if timer.past_due:
        logger.warning("Timer is past due - running catch-up at %s", utc_now)

    result = _perform_maintenance()
    logger.info("Scheduled cleanup complete at %s: %s", utc_now, result)


def _perform_maintenance() -> str:
    """Simulate a maintenance task (for example, purge expired cache entries)."""
    return "Maintenance complete - 0 stale entries purged"
