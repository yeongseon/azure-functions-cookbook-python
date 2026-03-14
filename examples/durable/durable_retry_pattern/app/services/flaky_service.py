from __future__ import annotations

import random


def execute_flaky_operation(payload: dict[str, str]) -> str:
    failure_roll = random.random()
    if failure_roll < 0.6:
        raise RuntimeError("Transient activity failure. Please retry.")
    return f"Succeeded with payload: {payload['input']}"
