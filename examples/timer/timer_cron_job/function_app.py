"""Timer-triggered scheduled job with NCRONTAB expression."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.timer import timer_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(timer_blueprint)
