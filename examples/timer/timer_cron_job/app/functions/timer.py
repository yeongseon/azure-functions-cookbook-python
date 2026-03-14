from __future__ import annotations

import logging
from datetime import datetime, timezone

import azure.functions as func

from app.services.maintenance_service import perform_maintenance

timer_blueprint = func.Blueprint()
logger = logging.getLogger(__name__)


@timer_blueprint.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def scheduled_cleanup(timer: func.TimerRequest) -> None:
    utc_now = datetime.now(tz=timezone.utc).isoformat()

    if timer.past_due:
        logger.warning("Timer is past due - running catch-up at %s", utc_now)

    result = perform_maintenance()
    logger.info("Scheduled cleanup complete at %s: %s", utc_now, result)
