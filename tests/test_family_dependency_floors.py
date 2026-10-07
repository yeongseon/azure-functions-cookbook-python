from pathlib import Path
import tomllib

from packaging.requirements import Requirement
from packaging.version import Version

_ROOT = Path(__file__).parents[1]
_KNOWN_GOOD = {
    "azure-functions-db": Version("0.8.0"),
    "azure-functions-doctor": Version("0.22.0"),
    "azure-functions-langgraph": Version("0.10.0"),
    "azure-functions-logging": Version("0.14.0"),
    "azure-functions-openapi": Version("0.29.0"),
    "azure-functions-scaffold": Version("0.9.1"),
    "azure-functions-validation": Version("0.14.0"),
}


def test_recipe_family_dependency_floors_are_known_good() -> None:
    # Given: the first family versions supporting recipe API usage.
    stale: list[str] = []

    # When: every recipe's explicit family lower bounds are inspected.
    for pyproject in sorted((_ROOT / "examples").glob("**/pyproject.toml")):
        dependencies = tomllib.loads(pyproject.read_text())["project"]["dependencies"]
        for dependency in dependencies:
            requirement = Requirement(dependency)
            known_good = _KNOWN_GOOD.get(requirement.name)
            if known_good is None:
                continue
            lower_bounds = [
                Version(specifier.version)
                for specifier in requirement.specifier
                if specifier.operator == ">="
            ]
            if not lower_bounds or max(lower_bounds) < known_good:
                stale.append(f"{pyproject.relative_to(_ROOT)}: {dependency}")

    # Then: no recipe advertises an incompatible family floor.
    assert stale == [], "\n".join(stale)
