"""Exact reviewed SDK fallback bindings, separate from registration reviews."""

import ast
import json
from pathlib import Path


def binding_digest(node: ast.AST) -> str:
    import hashlib

    def normalized(value: ast.AST | list[ast.AST] | str | int | float | bool | None) -> str:
        if isinstance(value, ast.AST):
            fields = ", ".join(
                f"{name}={normalized(child)}"
                for name, child in ast.iter_fields(value)
                if child is not None and name != "type_params"
            )
            return f"{type(value).__name__}({fields})"
        if isinstance(value, list):
            return "[" + ", ".join(normalized(child) for child in value) + "]"
        return repr(value)

    return hashlib.sha256(normalized(node).encode()).hexdigest()


def reviewed_bindings(path: Path, root: Path, tree: ast.Module) -> frozenset[str]:
    manifest = root / "security/recipe-security-manifest.json"
    if not manifest.exists():
        return frozenset()
    entries = json.loads(manifest.read_text()).get("binding_reviews", [])
    return frozenset(
        entry["name"]
        for entry in entries
        if entry["file"] == path.relative_to(root).as_posix()
        and entry.get("reason")
        and entry.get("owner")
        and any(
            node.lineno == entry["line"]
            and binding_digest(node) == entry["digest"]
            and all(
                node.lineno <= child.lineno <= (node.end_lineno or node.lineno)
                for child in ast.walk(tree)
                if isinstance(child, ast.Name)
                and child.id == entry["name"]
                and isinstance(child.ctx, (ast.Store, ast.Del))
            )
            and all(
                node.lineno <= child.lineno <= (node.end_lineno or node.lineno)
                for child in ast.walk(tree)
                if isinstance(child, (ast.Import, ast.ImportFrom))
                and any(
                    (alias.asname or alias.name.split(".")[0]) == entry["name"]
                    for alias in child.names
                )
            )
            for node in tree.body
        )
    )
