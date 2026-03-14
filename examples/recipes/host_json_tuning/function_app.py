"""Timer trigger recipe that pairs with rich host.json tuning options."""

from __future__ import annotations

import logging

import azure.functions as func

app = func.FunctionApp()


@app.function_name(name="host_config_demo_timer")
@app.schedule(
    schedule="0 */10 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def host_config_demo_timer(timer: func.TimerRequest) -> None:
    """Log a heartbeat that references host.json tuning in this recipe."""
    logging.info("host_json_tuning timer fired. past_due=%s", timer.past_due)
    logging.info(
        "This project demonstrates logging, timeout, queues, and serviceBus host settings.",
    )
