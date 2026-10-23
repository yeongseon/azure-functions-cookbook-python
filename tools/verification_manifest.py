from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Recipe:
    path: str
    family: str
    has_tests: bool
    azure_supported: bool = False


def recipes(root: Path) -> tuple[Recipe, ...]:
    return tuple(
        Recipe(
            path.parent.relative_to(root / "examples").as_posix(),
            path.parent.parent.name,
            bool(list((path.parent / "tests").glob("test_*.py"))),
        )
        for path in sorted((root / "examples").glob("*/*/recipe.yaml"))
    )


LOCAL_SUITES = (
    ("http", "tests/e2e/test_http_examples.py", "e2e"),
    ("queue", "tests/e2e/test_queue_examples.py", "e2e"),
    ("blob", "tests/e2e/test_blob_examples.py", "e2e"),
    ("toolkit-runtime", "tests/e2e/test_package_runtime.py", "e2e"),
    ("durable-import", "tests/e2e/test_durable_examples.py", "smoke"),
    ("non-emulatable-import", "tests/e2e/test_smoke_examples.py", "smoke"),
    ("agent-storage", "tests/test_personal_langgraph_agent.py", "e2e"),
)
