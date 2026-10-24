"""Compile every recipe main.bicep and fail if any produce a Bicep CLI
error. Used both as a CI guard and locally (#377).

Unlike targeted checks for one known diagnostic (see
tests/test_bicep_linux_plans.py), this compiles the full shipped IaC
inventory so expression/schema errors are caught before recipes are
published, regardless of which specific diagnostic code they produce.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


def _bicep_cli() -> str | None:
    return os.environ.get("BICEP_CLI") or shutil.which("bicep")


def compile_all_templates(bicep: str) -> list[tuple[str, str]]:
    """Return a list of (relative_path, diagnostics) for every main.bicep
    that fails to compile. Empty list means every template compiled
    cleanly (warnings are tolerated; only a non-zero compiler exit or an
    ``Error `` diagnostic fails). Finding no template at all is a failure,
    never a pass (#438)."""
    templates = sorted(EXAMPLES.glob("**/main.bicep"))
    if not templates:
        return [("examples/**/main.bicep", "no templates found; refusing to report success")]
    failures: list[tuple[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="cookbook-bicep-") as tmp:
        output_dir = Path(tmp)
        for template in templates:
            label = template.relative_to(EXAMPLES).as_posix()
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
            if result.returncode != 0 or "Error " in diagnostics:
                failures.append((label, diagnostics))
    return failures


def main() -> int:
    bicep = _bicep_cli()
    if not bicep:
        print("Bicep CLI not found; install it or set BICEP_CLI.", file=sys.stderr)
        return 1

    failures = compile_all_templates(bicep)
    if failures:
        for label, diagnostics in failures:
            print(f"=== {label} ===", file=sys.stderr)
            print(diagnostics, file=sys.stderr)
        print(f"{len(failures)} template(s) failed to compile.", file=sys.stderr)
        return 1

    print("All recipe main.bicep templates compiled successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
