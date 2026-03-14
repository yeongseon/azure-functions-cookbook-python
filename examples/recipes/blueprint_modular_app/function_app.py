"""Modular function app using Azure Functions Blueprints."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.health import health_blueprint
from app.functions.users import users_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(health_blueprint)
app.register_functions(users_blueprint)
