#!/usr/bin/env python3
"""Verify the scheduled-trigger-smoke workflow's suites actually select tests.

Guards #177: the workflow previously ran all three E2E test files through a
single ``-m e2e`` selector, but ``tests/e2e/test_durable_examples.py`` is
marked ``smoke`` (import-only coverage, not live Durable orchestration), so
every Durable test was silently deselected despite the job/step names and
``docs/scheduled-trigger-smoke.md`` describing Durable coverage as executed.

This script collection-only (``--collect-only``) checks each of the
workflow's two real selectors and fails loudly, printing the exact selected
count, if either one would select zero tests -- the same failure mode a
marker typo or a future file rename could reintroduce silently.
"""

from __future__ import annotations

import subprocess
import sys


def _collected_count(args: list[str]) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-cov", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1, 5):
        # 0 = items collected, 1 = collection errors; 5 = "no tests ran" is
        # the failure this guards and is handled by the zero-count check
        # below, not treated as an unexpected subprocess failure.
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"pytest collection failed unexpectedly: {args}")
    total = 0
    for line in result.stdout.splitlines():
        # Quiet collect-only output is either a per-file summary
        # ("tests/e2e/test_durable_examples.py: 7") or, when a marker
        # filter deselects some items in a mixed file, a trailing summary
        # line ("13 tests collected / 7 deselected / 6 selected").
        stripped = line.strip()
        if " selected" in stripped:
            for token in stripped.replace(",", " ").split():
                if token.isdigit():
                    total = int(token)
            continue
        if ": " in stripped:
            suffix = stripped.rsplit(": ", 1)[-1]
            if suffix.isdigit():
                total += int(suffix)
    return total


SUITES: list[tuple[str, list[str]]] = [
    (
        "queue+blob (e2e)",
        [
            "-m",
            "e2e",
            "tests/e2e/test_queue_examples.py",
            "tests/e2e/test_blob_examples.py",
        ],
    ),
    ("durable (smoke)", ["-m", "smoke", "tests/e2e/test_durable_examples.py"]),
]


def main() -> int:
    failures = []
    for label, args in SUITES:
        count = _collected_count(args)
        print(f"{label}: {count} test(s) selected")
        if count == 0:
            failures.append(label)
    if failures:
        print(
            f"ERROR: the following suite(s) selected zero tests: {', '.join(failures)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
