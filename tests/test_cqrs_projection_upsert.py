"""Regression tests for #369: CQRS read-model projection writes must upsert
on the order id, not fail with a permanent unique-constraint conflict when
an order changes or a change-feed batch redelivers an existing document.

Uses the documented schema.sql and the actual decorated projector --
no network requests, running Functions host, or cloud resources.
"""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from unittest.mock import patch

from tests._isolation import load_example_module

EXAMPLE_PATH = "data-and-pipelines/cqrs_read_projection"
SCHEMA_PATH = Path("examples") / EXAMPLE_PATH / "schema.sql"


def _order(order_id: str, *, status: str, updated_at: str) -> dict[str, object]:
    return {
        "id": order_id,
        "customer_id": f"customer-{order_id}",
        "status": status,
        "items": [{"sku": "one", "quantity": 1, "unit_price": 5.0}],
        "updated_at": updated_at,
    }


def _projector() -> tuple[ModuleType, Callable[..., Any]]:
    module = load_example_module(EXAMPLE_PATH)
    return module, module.project_order_read_models.build().get_user_function()


def test_a_later_change_to_the_same_order_updates_its_single_row() -> None:
    with TemporaryDirectory() as d:
        db_path = Path(d) / "readmodels.sqlite"
        with sqlite3.connect(db_path) as connection:
            connection.executescript(SCHEMA_PATH.read_text())

        with patch.dict(os.environ, {"READ_DB_URL": f"sqlite:///{db_path}"}):
            _, handler = _projector()
            original = _order("order-1", status="pending", updated_at="2026-01-01T00:00:00Z")
            handler(documents=[original])

            updated = _order("order-1", status="shipped", updated_at="2026-01-02T00:00:00Z")
            handler(documents=[updated])  # must not raise

        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                "SELECT id, status, updated_at FROM order_read_models"
            ).fetchall()

        assert rows == [("order-1", "shipped", "2026-01-02T00:00:00Z")]


def test_repeated_unchanged_delivery_keeps_one_row() -> None:
    with TemporaryDirectory() as d:
        db_path = Path(d) / "readmodels.sqlite"
        with sqlite3.connect(db_path) as connection:
            connection.executescript(SCHEMA_PATH.read_text())

        with patch.dict(os.environ, {"READ_DB_URL": f"sqlite:///{db_path}"}):
            _, handler = _projector()
            order = _order("order-2", status="pending", updated_at="2026-01-01T00:00:00Z")
            handler(documents=[order])
            handler(documents=[order])  # exact redelivery: must not raise

        with sqlite3.connect(db_path) as connection:
            rows = connection.execute("SELECT id FROM order_read_models").fetchall()

        assert rows == [("order-2",)]


def test_mixed_batch_of_existing_and_new_orders_upserts_both() -> None:
    with TemporaryDirectory() as d:
        db_path = Path(d) / "readmodels.sqlite"
        with sqlite3.connect(db_path) as connection:
            connection.executescript(SCHEMA_PATH.read_text())

        with patch.dict(os.environ, {"READ_DB_URL": f"sqlite:///{db_path}"}):
            _, handler = _projector()
            existing = _order("order-3", status="pending", updated_at="2026-01-01T00:00:00Z")
            handler(documents=[existing])

            existing_changed = _order(
                "order-3", status="shipped", updated_at="2026-01-02T00:00:00Z"
            )
            new_order = _order("order-4", status="pending", updated_at="2026-01-02T00:00:00Z")
            handler(documents=[existing_changed, new_order])  # must not raise

        with sqlite3.connect(db_path) as connection:
            rows = {
                row[0]: row[1]
                for row in connection.execute("SELECT id, status FROM order_read_models").fetchall()
            }

        assert rows == {"order-3": "shipped", "order-4": "pending"}
