from __future__ import annotations

import subprocess


def main() -> int:
    outcomes = [
        subprocess.run(["make", target], check=False).returncode
        for target in (
            "format-check",
            "lint",
            "typecheck",
            "security",
            "lint-workflows",
            "generated-check",
        )
    ]
    print(f"Non-mutating quality tasks: {len(outcomes)}; typecheck executed once")
    return next((code for code in outcomes if code), 0)


if __name__ == "__main__":
    raise SystemExit(main())
