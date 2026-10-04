from pathlib import Path

import tomli

_ROOT = Path(__file__).parents[1]
_KNOWN_GOOD = {"azure-functions-openapi": (0, 20, 0)}


def test_recipe_family_dependency_floors_are_known_good() -> None:
    # Given: the first family versions supporting recipe API usage.
    stale: list[str] = []

    # When: every recipe's explicit family lower bounds are inspected.
    for pyproject in sorted((_ROOT / "examples").glob("**/pyproject.toml")):
        dependencies = tomli.loads(pyproject.read_text())["project"]["dependencies"]
        for package, known_good in _KNOWN_GOOD.items():
            for dependency in dependencies:
                if not dependency.startswith(f"{package}>="):
                    continue
                floor = dependency.removeprefix(f"{package}>=").split(",", maxsplit=1)[0]
                if tuple(int(part) for part in floor.split(".")) < known_good:
                    stale.append(f"{pyproject.relative_to(_ROOT)}: {dependency}")

    # Then: no recipe advertises an incompatible family floor.
    assert stale == [], "\n".join(stale)
