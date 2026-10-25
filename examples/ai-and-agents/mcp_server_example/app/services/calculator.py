from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from typing import Final

MAX_EXPRESSION_LENGTH: Final = 256
MAX_AST_NODES: Final = 64
MAX_DEPTH: Final = 16
MAX_MAGNITUDE: Final = 10**12


@dataclass(frozen=True, slots=True)
class InvalidExpression(ValueError):
    def __str__(self) -> str:
        return "Invalid calculator expression"


def calculate(expression: str) -> str:
    """Interpret only bounded decimal arithmetic; never execute Python code."""
    if not 0 < len(expression) <= MAX_EXPRESSION_LENGTH:
        raise InvalidExpression()
    if any(character not in "0123456789+-*/() ." for character in expression):
        raise InvalidExpression()
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise InvalidExpression()
        return str(_evaluate(tree.body, 1))
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise InvalidExpression() from exc


def _evaluate(node: ast.AST, depth: int) -> int | float:
    if depth > MAX_DEPTH:
        raise InvalidExpression()
    match node:
        case ast.Constant(value=int() | float() as value) if not isinstance(value, bool):
            result = value
        case ast.UnaryOp(op=ast.UAdd(), operand=operand):
            result = _evaluate(operand, depth + 1)
        case ast.UnaryOp(op=ast.USub(), operand=operand):
            result = -_evaluate(operand, depth + 1)
        case ast.BinOp(left=left, op=ast.Add(), right=right):
            result = _evaluate(left, depth + 1) + _evaluate(right, depth + 1)
        case ast.BinOp(left=left, op=ast.Sub(), right=right):
            result = _evaluate(left, depth + 1) - _evaluate(right, depth + 1)
        case ast.BinOp(left=left, op=ast.Mult(), right=right):
            result = _evaluate(left, depth + 1) * _evaluate(right, depth + 1)
        case ast.BinOp(left=left, op=ast.Div(), right=right):
            result = _evaluate(left, depth + 1) / _evaluate(right, depth + 1)
        case _:
            # AST is an open hierarchy: every node outside this grammar is rejected.
            raise InvalidExpression()
    if not math.isfinite(result) or abs(result) > MAX_MAGNITUDE:
        raise InvalidExpression()
    return result
