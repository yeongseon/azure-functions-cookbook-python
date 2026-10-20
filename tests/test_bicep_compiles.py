"""Regression guard for #377: every shipped recipe main.bicep must compile
without errors (not just the specific BCP025/BCP327/BCP037 diagnostics this
issue originally reported).

Skips cleanly if the Bicep CLI is not installed -- this is a supplementary
compile-time check, not the sole source of truth; see
tests/test_bicep_linux_plans.py for the targeted, structural (CLI-independent)
Linux-plan and duplicate-properties checks.
"""

from __future__ import annotations

import os
import shutil

from tools.compile_bicep_templates import compile_all_templates


def test_every_recipe_bicep_template_compiles_without_errors() -> None:
    bicep = os.environ.get("BICEP_CLI") or shutil.which("bicep")
    if not bicep:
        import pytest

        pytest.skip("Bicep CLI not installed; set BICEP_CLI or install it to run this check.")

    failures = compile_all_templates(bicep)

    assert failures == [], "\n\n".join(
        f"{label}:\n{diagnostics}" for label, diagnostics in failures
    )
