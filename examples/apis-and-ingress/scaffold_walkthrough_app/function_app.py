from __future__ import annotations

import azure.functions as func
from azure_functions_openapi.spec import get_openapi_json, get_openapi_yaml
from azure_functions_openapi.swagger_ui import render_swagger_ui

from app.core.logging import configure_logging
from app.functions.health import health_blueprint
from app.functions.webhooks import webhooks_blueprint

# azure-functions-scaffold: function imports

configure_logging()

app = func.FunctionApp()
# azure-functions-scaffold: function registrations
app.register_functions(health_blueprint)
app.register_functions(webhooks_blueprint)


@app.route(route="openapi.json", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def openapi_json(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=get_openapi_json(title="scaffold_walkthrough_app", version="0.1.0"),
        mimetype="application/json",
    )


@app.route(route="openapi.yaml", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def openapi_yaml(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=get_openapi_yaml(title="scaffold_walkthrough_app", version="0.1.0"),
        mimetype="text/yaml",
    )


@app.route(route="docs", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def swagger_ui(req: func.HttpRequest) -> func.HttpResponse:
    return render_swagger_ui(openapi_url="/api/openapi.json")
