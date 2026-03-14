"""Direct invocation script - call function handlers without the Azure runtime.

Usage:
    python invoke.py

This script constructs ``azure.functions.HttpRequest`` objects manually
and passes them to the function handler, printing the response.
No ``func start`` or Azurite required.
"""

from __future__ import annotations

import json

import azure.functions as func
from function_app import greet


def main() -> None:
    """Demonstrate direct function invocation."""
    get_req = func.HttpRequest(
        method="GET",
        url="/api/greet",
        body=b"",
        headers={},
        params={"name": "Alice"},
    )
    get_resp = greet(get_req)
    print(f"GET  /api/greet?name=Alice -> {get_resp.status_code}: {get_resp.get_body().decode()}")

    post_req = func.HttpRequest(
        method="POST",
        url="/api/greet",
        body=json.dumps({"name": "Bob"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    post_resp = greet(post_req)
    print(f"POST /api/greet           -> {post_resp.status_code}: {post_resp.get_body().decode()}")

    err_req = func.HttpRequest(
        method="GET",
        url="/api/greet",
        body=b"",
        headers={},
    )
    err_resp = greet(err_req)
    print(f"GET  /api/greet           -> {err_resp.status_code}: {err_resp.get_body().decode()}")


if __name__ == "__main__":
    main()
