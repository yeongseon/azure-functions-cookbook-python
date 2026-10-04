import importlib.util
from pathlib import Path

_ROOT = Path(__file__).parents[1]
_SCRIPT = _ROOT / "scripts" / "gen_requirements.py"
_SPEC = importlib.util.spec_from_file_location("gen_requirements", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
gen_requirements = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gen_requirements)


def test_requirements_match_project_dependencies() -> None:
    # Given: every recipe with an Azure Functions entry point.
    projects = gen_requirements.recipe_projects()

    # When: the deployment requirements are compared with project metadata.
    stale = []
    for project in projects:
        expected = gen_requirements.render(project / "pyproject.toml")
        requirements = project / "requirements.txt"
        if not requirements.exists() or requirements.read_text() != expected:
            stale.append(project.relative_to(gen_requirements.EXAMPLES).as_posix())

    # Then: every requirements file is present and deterministic.
    assert stale == [], (
        "Recipe requirements are stale; run: python scripts/gen_requirements.py\n"
        + "\n".join(stale)
    )
