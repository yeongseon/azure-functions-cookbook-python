from __future__ import annotations

import json

import azure.functions as func

from app.services.mcp_service import _json_rpc_error, handle_mcp_request

mcp_blueprint = func.Blueprint()


@mcp_blueprint.route(route="mcp", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def mcp(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        response_body = _json_rpc_error(None, -32700, "Parse error")
        return func.HttpResponse(
            json.dumps(response_body),
            mimetype="application/json",
            status_code=400,
        )

    response_body, status_code = handle_mcp_request(body)
    return func.HttpResponse(
        json.dumps(response_body),
        mimetype="application/json",
        status_code=status_code,
    )
