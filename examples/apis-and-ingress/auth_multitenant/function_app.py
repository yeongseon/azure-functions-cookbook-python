"""Multi-tenant access control with tenant allowlist."""

from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.auth import auth_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(auth_blueprint)
