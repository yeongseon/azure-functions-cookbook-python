from __future__ import annotations


def apply_counter_operation(
    current_value: int,
    operation: str,
    amount: int | None,
) -> tuple[int, int | dict[str, str]]:
    if operation == "add":
        increment = 1 if amount is None else int(amount)
        updated = current_value + increment
        return updated, updated

    if operation == "reset":
        return 0, 0

    if operation == "get":
        return current_value, current_value

    return current_value, {"error": f"Unsupported operation: {operation}"}
