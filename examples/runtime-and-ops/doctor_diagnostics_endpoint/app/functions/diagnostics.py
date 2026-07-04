from __future__ import annotations

import json

import azure.functions as func

from app.services.diagnostics_service import (
    get_health_payload,
    run_project_diagnostics,
    summarize,
)

diagnostics_blueprint = func.Blueprint()


@diagnostics_blueprint.route(
    route="health",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_health(req: func.HttpRequest) -> func.HttpResponse:
    """Anonymous liveness probe. Does not invoke Doctor."""
    del req
    return func.HttpResponse(
        body=json.dumps(get_health_payload()),
        mimetype="application/json",
        status_code=200,
    )


@diagnostics_blueprint.route(route="diagnostics", methods=["GET"])
def get_diagnostics(req: func.HttpRequest) -> func.HttpResponse:
    """Return the full azure-functions-doctor SectionResult list as JSON."""
    del req
    sections = run_project_diagnostics()
    return func.HttpResponse(
        body=json.dumps({"sections": sections}),
        mimetype="application/json",
        status_code=200,
    )


@diagnostics_blueprint.route(route="diagnostics/summary", methods=["GET"])
def get_diagnostics_summary(req: func.HttpRequest) -> func.HttpResponse:
    """Return a compact pass/fail summary of the diagnostics."""
    del req
    sections = run_project_diagnostics()
    return func.HttpResponse(
        body=json.dumps(summarize(sections)),
        mimetype="application/json",
        status_code=200,
    )
