"""Regression tests for #370: three database recipes called
``reader.fetch_all()``, which is not part of the public ``DbReader`` API,
and ``tenant_isolation`` passed a callable instead of a resolved string as
``inject_reader``'s ``url``. All three raised before returning their
documented data.

Exercises each complete decorated handler chain against temporary SQLite
databases -- no network requests, running Functions host, or cloud
resources -- and parses the actual response body (not just status code),
per the issue's own note that a schema-valid OpenAPI declaration does not
prove the runtime response is itself valid JSON.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest.mock import patch

import azure.functions as func

from tests._isolation import load_example_module

CQRS_SCHEMA = Path("examples/data-and-pipelines/cqrs_read_projection/schema.sql").read_text()


def _request(
    *,
    method: str = "GET",
    route_params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> func.HttpRequest:
    return func.HttpRequest(
        method=method,
        url="https://example.invalid/api/review",
        body=body,
        headers=headers or {},
        route_params=route_params or {},
    )


def test_db_input_output_list_items_returns_valid_json_for_nonempty_and_empty() -> None:
    with TemporaryDirectory() as d:
        db_path = Path(d) / "items.sqlite"
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT, category TEXT, price REAL)"
            )
            connection.execute("INSERT INTO items VALUES ('one', 'Widget', 'hardware', 9.5)")

        with patch.dict(os.environ, {"DB_URL": f"sqlite:///{db_path}"}):
            module = load_example_module("data-and-pipelines/db_input_output")
            handler = module.list_items.build().get_user_function()

            response = handler(req=_request(), context=None)
            assert response.status_code == 200
            assert response.mimetype == "application/json"
            parsed = json.loads(response.get_body())
            assert parsed == [{"id": "one", "name": "Widget", "category": "hardware", "price": 9.5}]

        with sqlite3.connect(db_path) as connection:
            connection.execute("DELETE FROM items")

        with patch.dict(os.environ, {"DB_URL": f"sqlite:///{db_path}"}):
            module = load_example_module("data-and-pipelines/db_input_output")
            handler = module.list_items.build().get_user_function()
            empty_response = handler(req=_request(), context=None)
            assert json.loads(empty_response.get_body()) == []


def test_cqrs_get_order_projection_returns_a_single_match_by_id() -> None:
    with TemporaryDirectory() as d:
        db_path = Path(d) / "readmodels.sqlite"
        with sqlite3.connect(db_path) as connection:
            connection.executescript(CQRS_SCHEMA)
            connection.execute(
                "INSERT INTO order_read_models VALUES "
                "('order-1', 'customer-1', 'pending', 1, 5.0, '2026-01-01T00:00:00Z')"
            )

        with patch.dict(os.environ, {"READ_DB_URL": f"sqlite:///{db_path}"}):
            module = load_example_module("data-and-pipelines/cqrs_read_projection")
            handler = module.get_order_projection.build().get_user_function()

            response = handler(req=_request(route_params={"id": "order-1"}), context=None)
            assert response.status_code == 200
            parsed = json.loads(response.get_body())
            assert parsed["id"] == "order-1"
            assert parsed["status"] == "pending"

            missing = handler(req=_request(route_params={"id": "missing"}), context=None)
            assert missing.status_code == 404


def test_tenant_isolation_queries_two_distinct_tenant_mappings() -> None:
    with TemporaryDirectory() as d:
        db_a = Path(d) / "tenant_a.sqlite"
        db_b = Path(d) / "tenant_b.sqlite"
        for path, invoice_id, customer in ((db_a, "inv-a", "cust-a"), (db_b, "inv-b", "cust-b")):
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "CREATE TABLE invoices (invoice_id TEXT PRIMARY KEY, customer_id TEXT, "
                    "status TEXT, amount REAL)"
                )
                connection.execute(
                    "INSERT INTO invoices VALUES (?, ?, 'paid', 10.0)", (invoice_id, customer)
                )

        env = {
            "TENANT_TENANT_A_DB_URL": f"sqlite:///{db_a}",
            "TENANT_TENANT_B_DB_URL": f"sqlite:///{db_b}",
        }
        with patch.dict(os.environ, env):
            module = load_example_module("security-and-tenancy/tenant_isolation")
            handler = module.query_tenant_invoices.build().get_user_function()

            response_a = handler(
                req=_request(
                    method="POST",
                    headers={"Content-Type": "application/json", "X-Tenant-ID": "tenant-a"},
                    body=b"{}",
                ),
                context=None,
            )
            assert response_a.status_code == 200
            parsed_a = json.loads(response_a.get_body())
            assert parsed_a["tenant_id"] == "tenant-a"
            assert parsed_a["items"][0]["invoice_id"] == "inv-a"

            response_b = handler(
                req=_request(
                    method="POST",
                    headers={"Content-Type": "application/json", "X-Tenant-ID": "tenant-b"},
                    body=b"{}",
                ),
                context=None,
            )
            assert response_b.status_code == 200
            parsed_b = json.loads(response_b.get_body())
            assert parsed_b["tenant_id"] == "tenant-b"
            assert parsed_b["items"][0]["invoice_id"] == "inv-b"


def test_tenant_isolation_rejects_missing_tenant_context_with_400() -> None:
    module = load_example_module("security-and-tenancy/tenant_isolation")
    handler = module.query_tenant_invoices.build().get_user_function()

    response = handler(
        req=_request(method="POST", headers={"Content-Type": "application/json"}, body=b"{}"),
        context=None,
    )

    assert response.status_code == 400


def test_tenant_isolation_rejects_unmapped_tenant_with_404() -> None:
    module = load_example_module("security-and-tenancy/tenant_isolation")
    handler = module.query_tenant_invoices.build().get_user_function()

    response = handler(
        req=_request(
            method="POST",
            headers={"Content-Type": "application/json", "X-Tenant-ID": "unmapped-tenant"},
            body=b"{}",
        ),
        context=None,
    )

    assert response.status_code == 404
