"""Regression guard for #281: every Python-targeting recipe Bicep plan/site
must be Linux-configured, with no duplicate ``properties`` members.

The prior guard only inspected templates that already contained
``linuxFxVersion``, silently skipping any template still using the
non-Linux ``pythonVersion`` site config (15 such templates existed) and
accepting duplicate top-level ``properties`` members by string presence
alone (53 templates had both an empty ``properties: {}`` and a real
``properties: { reserved: true }`` on the same plan resource -- a shape
Bicep rejects with BCP025, which this string-based check could not see).
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

_EXAMPLES = Path(__file__).parents[1] / "examples"
_RESOURCE = re.compile(
    r"resource\s+(?P<name>\w+)\s+'(?P<kind>Microsoft\.Web/serverfarms|Microsoft\.Web/sites)@[^']+'"
    r"\s*=\s*\{(?P<body>.*?)\n\}",
    re.DOTALL,
)
_TOP_LEVEL_PROPERTIES = re.compile(r"^\s{2}properties:\s*\{", re.MULTILINE)


def _resources(source: str) -> list[re.Match[str]]:
    return list(_RESOURCE.finditer(source))


def _is_python_template(source: str) -> bool:
    return "pythonVersion" in source or "linuxFxVersion" in source


def test_python_bicep_plans_are_linux_consumption() -> None:
    """Every plan/site pair in a Python-targeting template must declare
    Linux configuration -- not just the subset that already happened to
    contain ``linuxFxVersion`` (#281)."""
    invalid: list[str] = []

    for template in sorted(_EXAMPLES.glob("**/main.bicep")):
        source = template.read_text()
        if not _is_python_template(source):
            continue

        resources = _resources(source)
        plans = [m for m in resources if m.group("kind") == "Microsoft.Web/serverfarms"]
        sites = [m for m in resources if m.group("kind") == "Microsoft.Web/sites"]
        label = template.relative_to(_EXAMPLES).as_posix()

        for plan in plans:
            body = plan.group("body")
            if "kind: 'linux'" not in body or "reserved: true" not in body:
                invalid.append(f"{label}: plan {plan.group('name')!r} is not Linux-configured")

        for site in sites:
            body = site.group("body")
            if "functionapp,linux" not in body:
                invalid.append(
                    f"{label}: site {site.group('name')!r} kind is not 'functionapp,linux'"
                )
            if "linuxFxVersion" not in body:
                invalid.append(
                    f"{label}: site {site.group('name')!r} siteConfig has no linuxFxVersion"
                )
            if "pythonVersion" in body:
                invalid.append(
                    f"{label}: site {site.group('name')!r} siteConfig still has "
                    "non-Linux pythonVersion"
                )

    assert invalid == [], "\n".join(invalid)


def test_bicep_plan_and_site_have_no_duplicate_properties_member() -> None:
    """No ``Microsoft.Web/serverfarms`` or ``Microsoft.Web/sites`` resource
    body may declare the top-level ``properties:`` member more than once --
    Bicep rejects that shape with BCP025, and the prior string-presence
    guard could not detect it (#281)."""
    invalid: list[str] = []

    for template in sorted(_EXAMPLES.glob("**/main.bicep")):
        source = template.read_text()
        label = template.relative_to(_EXAMPLES).as_posix()
        for resource in _resources(source):
            body = resource.group("body")
            count = len(_TOP_LEVEL_PROPERTIES.findall(body))
            if count > 1:
                invalid.append(
                    f"{label}: {resource.group('kind')} {resource.group('name')!r} "
                    f"declares 'properties:' {count} times"
                )

    assert invalid == [], "\n".join(invalid)


def test_fixed_python_plan_site_templates_compile_without_bcp025() -> None:
    """Compile every template this issue fixed and confirm the specific
    BCP025 (duplicate member) diagnostic this guard targets does not
    reappear. Skipped entirely if the Bicep CLI is not installed -- this
    is a supplementary compile-time check, not the sole source of truth
    (the two structural checks above run regardless)."""
    bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if not bicep:
        return

    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        for template in sorted(_EXAMPLES.glob("**/main.bicep")):
            source = template.read_text()
            if "reserved: true" not in source:
                continue
            label = template.relative_to(_EXAMPLES).as_posix()
            result = subprocess.run(
                [
                    bicep,
                    "build",
                    "--no-restore",
                    str(template),
                    "--outfile",
                    str(output_dir / f"{label.replace('/', '_')}.json"),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            diagnostics = result.stdout + result.stderr
            assert "BCP025" not in diagnostics, f"{label}: {diagnostics}"
