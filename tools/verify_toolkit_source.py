"""Verify where the six toolkit packages in the current environment were installed from.

Used by ``e2e-toolkit.yml``. The ``main`` axis must test sibling-repository source, and the
``latest`` axis must test published releases, so a run whose installed packages come from the other
place is mislabeled evidence and fails here. ``pip`` records a VCS install in the distribution's
``direct_url.json``; an index install has none.

    python tools/verify_toolkit_source.py main     # every toolkit package built from git
    python tools/verify_toolkit_source.py latest   # every toolkit package from the index
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import metadata
import json
import sys

TOOLKIT_PACKAGES = (
    "azure-functions-db",
    "azure-functions-doctor",
    "azure-functions-langgraph",
    "azure-functions-logging",
    "azure-functions-openapi",
    "azure-functions-validation",
)
AXES = ("main", "latest")


def installed_source(package: str) -> str:
    """Return ``git``, ``other-direct-url`` or ``index``; raise if the package is not installed."""
    text = metadata.distribution(package).read_text("direct_url.json")
    if text is None:
        return "index"
    return "git" if "vcs_info" in json.loads(text) else "other-direct-url"


def check(axis: str, packages: Sequence[str] = TOOLKIT_PACKAGES) -> list[str]:
    """Describe each package whose install source does not match *axis* (empty means a match)."""
    wanted = "git" if axis == "main" else "index"
    problems = []
    for package in packages:
        try:
            source = installed_source(package)
        except metadata.PackageNotFoundError:
            problems.append(f"{package}: not installed")
            continue
        version = metadata.version(package)
        print(f"{package}=={version} installed from {source}")
        if source != wanted:
            problems.append(f"{package}=={version}: installed from {source}, expected {wanted}")
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in AXES:
        print(f"usage: verify_toolkit_source.py {{{'|'.join(AXES)}}}", file=sys.stderr)
        return 2
    problems = check(args[0])
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
