"""Declaration-time binding eligibility for auth-bearing expressions."""

from __future__ import annotations

import ast


def unstable_names(tree: ast.Module) -> set[str]:
    writes: dict[str, list[ast.AST]] = {}
    direct = set(tree.body)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    invalid: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.asname or (
                    alias.name if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
                )
                writes.setdefault(name, []).append(node)
                if node not in direct:
                    invalid.add(name)
        if isinstance(node, ast.ExceptHandler) and node.name:
            writes.setdefault(node.name, []).append(node)
            invalid.add(node.name)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            writes.setdefault(node.id, []).append(node)
            if parents.get(node) not in direct or not isinstance(
                parents.get(node), (ast.Assign, ast.AnnAssign)
            ):
                invalid.add(node.id)
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            invalid.update(node.names)
    invalid.update(name for name, assignments in writes.items() if len(assignments) > 1)
    return invalid


def expression_is_stable(node: ast.expr, invalid: set[str]) -> bool:
    return not any(isinstance(child, ast.Name) and child.id in invalid for child in ast.walk(node))
