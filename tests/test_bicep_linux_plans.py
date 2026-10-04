from pathlib import Path
import re

_EXAMPLES = Path(__file__).parents[1] / "examples"
_PLAN = re.compile(
    r"resource\s+\w+\s+'Microsoft\.Web/serverfarms@[^']+'\s*=\s*\{(?P<body>.*?)\n\}",
    re.DOTALL,
)


def test_python_bicep_plans_are_linux_consumption() -> None:
    # Given: every recipe Bicep template targeting a Linux Python runtime.
    invalid: list[str] = []

    # When: its App Service plan declarations are inspected.
    for template in sorted(_EXAMPLES.glob("**/main.bicep")):
        source = template.read_text()
        if "linuxFxVersion" not in source:
            continue
        for plan in _PLAN.finditer(source):
            body = plan.group("body")
            if "kind: 'linux'" not in body or "reserved: true" not in body:
                invalid.append(template.relative_to(_EXAMPLES).as_posix())

    # Then: every attached plan explicitly selects Linux Consumption.
    assert invalid == [], "\n".join(invalid)
