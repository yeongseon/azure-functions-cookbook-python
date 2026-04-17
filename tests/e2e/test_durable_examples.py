"""Smoke tests for Durable Functions examples.

Durable Functions require the Durable Task Framework storage backend,
which takes 90+ seconds to initialize with Azurite locally, making
real E2E tests impractical in CI/local environments.

These tests verify that each example's ``function_app.py`` can be imported
successfully, confirming valid Blueprint structure and dependency resolution.
"""

from __future__ import annotations

import pytest

from tests.e2e.conftest import import_function_app

pytestmark = pytest.mark.smoke

# ---------------------------------------------------------------------------
# durable_hello_sequence
# ---------------------------------------------------------------------------


class TestDurableHelloSequence:
    """Verify durable_hello_sequence imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_hello_sequence")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_fan_out_fan_in
# ---------------------------------------------------------------------------


class TestDurableFanOutFanIn:
    """Verify durable_fan_out_fan_in imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_fan_out_fan_in")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_human_interaction
# ---------------------------------------------------------------------------


class TestDurableHumanInteraction:
    """Verify durable_human_interaction imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_human_interaction")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_entity_counter
# ---------------------------------------------------------------------------


class TestDurableEntityCounter:
    """Verify durable_entity_counter imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_entity_counter")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_retry_pattern
# ---------------------------------------------------------------------------


class TestDurableRetryPattern:
    """Verify durable_retry_pattern imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_retry_pattern")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_determinism_gotchas
# ---------------------------------------------------------------------------


class TestDurableDeterminismGotchas:
    """Verify durable_determinism_gotchas imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_determinism_gotchas")
        assert hasattr(module, "app")


# ---------------------------------------------------------------------------
# durable_unit_testing
# ---------------------------------------------------------------------------


class TestDurableUnitTesting:
    """Verify durable_unit_testing imports cleanly."""

    def test_module_imports(self) -> None:
        module = import_function_app("orchestration-and-workflows/durable_unit_testing")
        assert hasattr(module, "app")
