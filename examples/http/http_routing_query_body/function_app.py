"""HTTP routing example with route params, query strings, and JSON request bodies."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.users import users_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(users_blueprint)
