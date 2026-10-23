"""Startup customization is an explicit inspection gap, never inspected execution."""

from pathlib import Path
import re

from tools.recipe_discovery import recipe_files
from tools.recipe_inspection import InspectionGap


def startup_gaps(project: Path, root: Path) -> tuple[InspectionGap, ...]:
    gaps: list[InspectionGap] = []
    for path in recipe_files(project, "*"):
        if "tests" in path.relative_to(project).parts:
            continue
        name = path.name.lower()
        if name in {"sitecustomize.py", "usercustomize.py"} or path.suffix == ".pth":
            gaps.append(
                InspectionGap(path.relative_to(root).as_posix(), 1, "startup-customization", "")
            )
        if ".settings" in name or name.startswith(".env"):
            for line, text in enumerate(path.read_text().splitlines(), 1):
                if re.search(
                    r"(?i)\b(?:pythonpath|python_path|pythonhome|python_home)\b\s*[\"']?\s*[:=]",
                    text,
                ):
                    gaps.append(
                        InspectionGap(
                            path.relative_to(root).as_posix(), line, "startup-path-setting", ""
                        )
                    )
    return tuple(gaps)
