"""Check complete runnable inventory against reviewed route-risk classifications."""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.recipe_discovery import recipe_files
from tools.recipe_inspection import unreviewed_gaps
from tools.recipe_routes import routes
from tools.recipe_startup import startup_gaps
from tools.security_report import (
    Check,
    Finding,
    Status,
    load,
    mapping,
    sequence,
    text,
    write_report,
)

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    "public-health",
    "auth-demonstration",
    "public-webhook-with-own-verification",
    "local-demo-no-backend",
    "paid-backend",
    "protected",
    "non-http",
    "cloud-backend-demo",
    "public-api-documentation",
    "edge-auth-demonstration",
}
PAID = {"openai_direct_chat", "ai_image_generation", "streaming_ai_response"}


def inventory(root: Path) -> dict[str, list[str]]:
    return {
        path.parent.relative_to(root).as_posix(): [
            f"{route.handler}={route.auth}" for route in routes(path.parent, root)
        ]
        for path in recipe_files(root / "examples", "function_app.py")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
    }


def check_manifest(root: Path) -> Check:
    try:
        discovered = inventory(root)
        manifest = mapping(
            load((root / "security/recipe-security-manifest.json").read_text())["recipes"]
        )
        findings: list[Finding] = []
        classified = 0
        paid_incomplete = False
        inspection_incomplete = False
        for project, declarations in discovered.items():
            if project not in manifest:
                findings.append(Finding("UNCLASSIFIED", file=project))
                continue
            entry = mapping(manifest[project])
            gaps = (*unreviewed_gaps(root / project, root), *startup_gaps(root / project, root))
            inspection_incomplete |= bool(gaps)
            paid_incomplete |= bool(gaps) and (
                Path(project).name in PAID or entry["category"] == "paid-backend"
            )
            findings.extend(
                Finding("INCOMPLETE_INSPECTION", file=gap.file, line=gap.line) for gap in gaps
            )
            text(entry["reason"])
            if text(entry["category"]) not in CATEGORIES:
                findings.append(Finding("CATEGORY", file=project))
            expected = [text(item) for item in sequence(entry["routes"])]
            if expected != declarations:
                findings.append(Finding("ROUTE_DRIFT", file=project))
            else:
                classified += 1
            for route in declarations:
                if route.endswith("=UNKNOWN"):
                    findings.append(Finding("UNRESOLVED_AUTH", file=project))
                if (
                    Path(project).name in PAID or entry["category"] == "paid-backend"
                ) and not route.endswith("=FUNCTION"):
                    findings.append(Finding("PAID_BACKEND_PUBLIC", file=project))
            if any(route.endswith("=ANONYMOUS") for route in declarations) and entry[
                "category"
            ] in {"protected", "non-http"}:
                findings.append(Finding("MISCLASSIFIED_ANONYMOUS", file=project))
            if bool(declarations) == (entry["category"] == "non-http"):
                findings.append(Finding("CATEGORY_DRIFT", file=project))
        for stale in set(manifest) - set(discovered):
            findings.append(Finding("STALE_RECIPE", file=stale))
        return Check(
            "recipe-manifest",
            Status.INCOMPLETE
            if inspection_incomplete and not paid_incomplete
            else (Status.FAIL if findings or not discovered else Status.PASS),
            {
                "discovered": len(discovered),
                "scanned": len(discovered),
                "classified": classified,
                "routes": sum(map(len, discovered.values())),
                "anonymous": sum(
                    r.endswith("=ANONYMOUS") for rs in discovered.values() for r in rs
                ),
            },
            tuple(findings),
            tuple(discovered),
        )
    except (OSError, ValueError, KeyError, TypeError, SyntaxError):
        return Check("recipe-manifest", Status.TOOL_ERROR, message="Invalid source or manifest")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "security-results/manifest")
    args = parser.parse_args()
    return write_report([check_manifest(ROOT)], args.output)


if __name__ == "__main__":
    raise SystemExit(main())
