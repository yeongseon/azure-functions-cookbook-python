from __future__ import annotations

import logging

import azure.functions as func

from app.services.heartbeat_service import log_heartbeat

timer_blueprint = func.Blueprint()


@timer_blueprint.function_name(name="host_config_demo_timer")
@timer_blueprint.schedule(
    schedule="0 */10 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def host_config_demo_timer(timer: func.TimerRequest) -> None:
    logging.info(log_heartbeat(past_due=timer.past_due))
    logging.info(
        "This project demonstrates logging, timeout, queues, and serviceBus host settings.",
    )
