"""Regenerate the committed OpenAPI convergence snapshot.

Run intentionally when a spec change is expected::

    hatch run python -m tests.regen_openapi_snapshot

See tests/test_openapi_endpoint_convergence.py and
yeongseon/azure-functions-python-cookbook#119.
"""

from __future__ import annotations

import json

from azure_functions_openapi import (
    clear_openapi_registry,
    get_openapi_json,
    scan_endpoint_metadata,
)

from tests._isolation import load_example_module
from tests.test_openapi_endpoint_convergence import EXAMPLE, SNAPSHOT_PATH


def main() -> None:
    clear_openapi_registry()
    module = load_example_module(EXAMPLE)
    scan_endpoint_metadata(module.app)
    spec = json.loads(get_openapi_json())
    SNAPSHOT_PATH.write_text(
        json.dumps(spec, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
