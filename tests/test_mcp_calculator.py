from __future__ import annotations

from collections.abc import Callable
import json

import azure.functions as func
import pytest

from tests._isolation import load_example_module


@pytest.fixture
def calculate() -> Callable[[str], func.HttpResponse]:
    module = load_example_module("ai-and-agents/mcp_server_example")
    handler: Callable[[func.HttpRequest], func.HttpResponse] = next(
        f.get_user_function() for f in module.app.get_functions() if f.get_function_name() == "mcp"
    )

    def call(expression: str) -> func.HttpResponse:
        return handler(
            func.HttpRequest(
                method="POST",
                url="http://localhost/api/mcp",
                params={},
                body=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 426,
                        "method": "tools/call",
                        "params": {"name": "calculate", "arguments": {"expression": expression}},
                    }
                ).encode(),
            )
        )

    return call


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("(2 + 3) * 4", "20"),
        ("2 + 3 * 4", "14"),
        ("-2 * +3", "-6"),
        ("8 / 2 / 2", "2.0"),
        (".5 + 1.25", "1.75"),
        (" 2 + 2 ", "4"),
        ("1000000000000", "1000000000000"),
        ("-1000000000000", "-1000000000000"),
        (" " * 255 + "1", "1"),
        ("+" * 15 + "1", "1"),
        ("+".join(["1"] * 16), "16"),
    ],
)
def test_calculator_accepts_bounded_arithmetic(
    calculate: Callable[[str], func.HttpResponse], expression: str, expected: str
) -> None:
    # Given documented arithmetic within the expression, depth and magnitude limits.
    # When evaluated through tools/call.
    response = calculate(expression)
    # Then precedence and numeric output are preserved.
    assert response.status_code == 200
    assert json.loads(response.get_body())["result"]["content"] == [
        {"type": "text", "text": expected}
    ]


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "2 ** 3",  # Even small powers are unsupported; never run an exhaustion payload.
        "4 // 2",
        "4 % 2",
        "1 << 2",
        "abs(2)",
        "secret_canary",
        "True",
        "[1]",
        "(1, 2)",
        "1j",
        "0xff",
        "1e3",
        "1_000",
        "1 # comment",
        "2 +",
        "1 / 0",
        "1000000000001",
        "1000000000000 + 1",
        "1000000000000 * 2",
        "1000000000000 / .1",
        "9" * 256,
        "0" * 256 + "1",
        "+" * 16 + "1",
        "+".join(["1"] * 17),
        "+".join(["(1+1)"] * 16),  # Operator nodes count toward the 64-node budget too.
    ],
)
def test_calculator_rejects_invalid_or_over_budget_expressions(
    calculate: Callable[[str], func.HttpResponse], expression: str
) -> None:
    # Given a small invalid expression (all fixtures have bounded resource cost).
    # When dispatched through the registered HTTP function.
    response = calculate(expression)
    # Then errors are explicit, stable and contain no expression or exception detail.
    assert response.status_code == 400
    assert json.loads(response.get_body()) == {
        "jsonrpc": "2.0",
        "id": 426,
        "error": {"code": -32602, "message": "Invalid calculator expression"},
    }
