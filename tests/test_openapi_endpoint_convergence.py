"""Convergence guard: the OpenAPI spec must stay identical after producers
switch to the ``endpoint`` metadata namespace.

The cookbook is the dogfood integration point where ``azure-functions-validation``
(producer) and ``azure-functions-openapi`` (consumer) run together. This test
imports a recipe that uses ``@validate_http`` + ``@openapi``, generates the
OpenAPI spec in-process (no ``func`` host required), and asserts it matches a
committed golden snapshot. If the ``endpoint`` convergence ever changes the
generated spec, this test fails loudly.

Regenerate the snapshot intentionally with::

    hatch run python -m tests.regen_openapi_snapshot

See yeongseon/azure-functions-python-cookbook#119.
"""

from __future__ import annotations

import json
from pathlib import Path

from azure_functions_openapi import clear_openapi_registry, get_openapi_json

from tests._isolation import load_example_module

# Recipe that exercises both producers/consumer:
#   @app.route + @openapi + @validate_http(path=..., response_model=...)
EXAMPLE = "apis-and-ingress/apim_function_backend"

SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "apim_function_backend.openapi.json"


def _generate_spec() -> dict[str, object]:
    """Generate the OpenAPI spec for ``EXAMPLE`` from a clean registry."""
    clear_openapi_registry()
    load_example_module(EXAMPLE)
    spec: dict[str, object] = json.loads(get_openapi_json())
    return spec


def test_spec_matches_committed_snapshot() -> None:
    """The generated spec must equal the committed golden snapshot.

    This is the end-to-end proof that the ``endpoint`` metadata namespace
    produces the expected OpenAPI output. Any drift is an intentional-change
    signal, not a silent regression.
    """
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    actual = _generate_spec()
    assert actual == expected, (
        "Generated OpenAPI spec drifted from the committed snapshot. "
        "If this change is intentional, regenerate "
        f"{SNAPSHOT_PATH.relative_to(SNAPSHOT_PATH.parents[2])}."
    )


def test_spec_generation_is_deterministic() -> None:
    """Regenerating the spec twice yields byte-identical output."""
    first = json.dumps(_generate_spec(), sort_keys=True)
    second = json.dumps(_generate_spec(), sort_keys=True)
    assert first == second
