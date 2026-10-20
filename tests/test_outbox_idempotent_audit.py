"""Regression tests for #360: outbox dispatch audit writes must tolerate
at-least-once redelivery of the same change-feed event without a permanent
unique-constraint conflict.

Uses a real temporary SQLite database with the documented schema and the
actual decorated relay handler -- no network requests, running Functions
host, or cloud resources.
"""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from unittest.mock import patch

from tests._isolation import load_example_module

EXAMPLE_PATH = "reliability/outbox_pattern"
SCHEMA = (
    "CREATE TABLE outbox_dispatches ("
    "event_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, "
    "event_type TEXT NOT NULL, broker_name TEXT NOT NULL, "
    "dispatched_at TEXT NOT NULL, status TEXT NOT NULL)"
)


def _relay_handler(module: ModuleType) -> Any:
    return next(
        f for f in module.app.get_functions() if f.get_function_name() == "relay_outbox_events"
    )


def test_exact_replay_of_the_same_event_does_not_raise_or_duplicate() -> None:
    with TemporaryDirectory() as temp:
        path = Path(temp) / "relay.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute(SCHEMA)

        with patch.dict(os.environ, {"DISPATCH_DB_URL": f"sqlite:///{path}"}):
            module = load_example_module(EXAMPLE_PATH)
            handler = _relay_handler(module).get_user_function()
            event = module._build_outbox_document(
                module._build_order_document(
                    {
                        "id": "one",
                        "customer_id": "one",
                        "amount": 2,
                        "currency": "USD",
                        "status": "accepted",
                    }
                )
            )

            handler(documents=[event])
            handler(documents=[event])  # exact replay: must not raise

        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT event_id FROM outbox_dispatches").fetchall()

        assert rows == [("evt-one-created",)]


def test_mixed_replay_and_new_event_batch_records_the_new_event() -> None:
    """A replayed old event must not prevent a genuinely new event in the
    same batch from being recorded."""
    with TemporaryDirectory() as temp:
        path = Path(temp) / "relay.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute(SCHEMA)

        with patch.dict(os.environ, {"DISPATCH_DB_URL": f"sqlite:///{path}"}):
            module = load_example_module(EXAMPLE_PATH)
            handler = _relay_handler(module).get_user_function()
            old_event = module._build_outbox_document(
                module._build_order_document(
                    {
                        "id": "one",
                        "customer_id": "one",
                        "amount": 2,
                        "currency": "USD",
                        "status": "accepted",
                    }
                )
            )
            new_event = module._build_outbox_document(
                module._build_order_document(
                    {
                        "id": "two",
                        "customer_id": "two",
                        "amount": 5,
                        "currency": "USD",
                        "status": "accepted",
                    }
                )
            )

            handler(documents=[old_event])
            handler(documents=[old_event, new_event])

        with sqlite3.connect(path) as connection:
            rows = {
                row[0]
                for row in connection.execute("SELECT event_id FROM outbox_dispatches").fetchall()
            }

        assert rows == {"evt-one-created", "evt-two-created"}


def test_non_outbox_documents_are_still_filtered_out() -> None:
    """Preserve the existing filtering of non-outbox (e.g. plain order)
    documents -- the upsert fix must not relax that filter."""
    with TemporaryDirectory() as temp:
        path = Path(temp) / "relay.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute(SCHEMA)

        with patch.dict(os.environ, {"DISPATCH_DB_URL": f"sqlite:///{path}"}):
            module = load_example_module(EXAMPLE_PATH)
            handler = _relay_handler(module).get_user_function()
            order_document = module._build_order_document(
                {
                    "id": "three",
                    "customer_id": "three",
                    "amount": 1,
                    "currency": "USD",
                    "status": "accepted",
                }
            )

            handler(documents=[order_document])

        with sqlite3.connect(path) as connection:
            rows = connection.execute("SELECT event_id FROM outbox_dispatches").fetchall()

        assert rows == []
