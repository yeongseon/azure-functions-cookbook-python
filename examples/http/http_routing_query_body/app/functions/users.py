from __future__ import annotations

import azure.functions as func

from app.services.user_service import (
    _json_response,
    _parse_json_body,
    create_user,
    delete_user,
    get_user_by_id,
    list_all_users,
    search_users,
    update_user,
)

users_blueprint = func.Blueprint()


@users_blueprint.route(route="users", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def list_users(req: func.HttpRequest) -> func.HttpResponse:
    del req
    return _json_response(list_all_users())


@users_blueprint.route(
    route="users/{user_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS
)
def get_user(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get("user_id", "")
    user = get_user_by_id(user_id)
    if user is None:
        return _json_response({"error": f"User '{user_id}' not found."}, status_code=404)
    return _json_response(user)


@users_blueprint.route(route="users", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_user_http(req: func.HttpRequest) -> func.HttpResponse:
    payload = _parse_json_body(req)
    if payload is None:
        return _json_response({"error": "Request body must be a JSON object."}, status_code=400)

    response_body, status_code = create_user(payload)
    return _json_response(response_body, status_code=status_code)


@users_blueprint.route(
    route="users/{user_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS
)
def update_user_http(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get("user_id", "")
    payload = _parse_json_body(req)
    if payload is None:
        return _json_response({"error": "Request body must be a JSON object."}, status_code=400)

    response_body, status_code = update_user(user_id, payload)
    return _json_response(response_body, status_code=status_code)


@users_blueprint.route(
    route="users/{user_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS
)
def delete_user_http(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.route_params.get("user_id", "")
    response_body, status_code = delete_user(user_id)
    if status_code == 204:
        return func.HttpResponse(status_code=204)
    return _json_response(response_body, status_code=status_code)


@users_blueprint.route(route="search", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def search_users_http(req: func.HttpRequest) -> func.HttpResponse:
    query = req.params.get("q", "").strip().lower()
    limit_raw = req.params.get("limit", "10")
    try:
        limit = max(1, int(limit_raw))
    except ValueError:
        return _json_response(
            {"error": "Query parameter 'limit' must be an integer."}, status_code=400
        )

    return _json_response(search_users(query, limit))
