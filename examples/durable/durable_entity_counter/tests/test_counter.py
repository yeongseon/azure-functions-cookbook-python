from app.services.counter_service import apply_counter_operation


def test_add_operation_with_default_increment() -> None:
    state, result = apply_counter_operation(4, "add", None)
    assert state == 5
    assert result == 5


def test_reset_operation() -> None:
    state, result = apply_counter_operation(9, "reset", None)
    assert state == 0
    assert result == 0


def test_get_operation() -> None:
    state, result = apply_counter_operation(7, "get", None)
    assert state == 7
    assert result == 7


def test_unsupported_operation() -> None:
    state, result = apply_counter_operation(2, "noop", None)
    assert state == 2
    assert result == {"error": "Unsupported operation: noop"}
