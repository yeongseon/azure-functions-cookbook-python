"""Modular function app using Azure Functions Blueprints."""

from __future__ import annotations

import azure.functions as func
from bp_health import bp as health_bp
from bp_users import bp as users_bp

app = func.FunctionApp()
app.register_blueprint(health_bp)
app.register_blueprint(users_bp)
