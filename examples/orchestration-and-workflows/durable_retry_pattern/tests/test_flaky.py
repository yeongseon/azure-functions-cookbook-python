from unittest.mock import patch

import pytest

from app.services.flaky_service import execute_flaky_operation


def test_execute_flaky_operation_raises_on_failure_roll() -> None:
    with patch("app.services.flaky_service.random.random", return_value=0.4):
        with pytest.raises(RuntimeError, match="Transient activity failure"):
            execute_flaky_operation({"input": "demo"})


def test_execute_flaky_operation_returns_success_message() -> None:
    with patch("app.services.flaky_service.random.random", return_value=0.9):
        result = execute_flaky_operation({"input": "demo"})
    assert result == "Succeeded with payload: demo"
