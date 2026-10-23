"""Offline settings, shell and Bicep checks; no claim of Azure deployment validation."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from tools.security_report import Check, Finding, Status

IGNORED = {".venv", ".git", "__pycache__", "node_modules", ".pytest_cache"}
SECRET = re.compile(
    r"(?:AccountKey|SharedAccessKey|api[_-]?key|AZURE_OPENAI_KEY|password|secret)"
    r"[\s\"':=]+([A-Za-z0-9+/=_-]{24,})",
    re.IGNORECASE,
)


def source_files(root: Path, suffix: str) -> tuple[Path, ...]:
    from tools.recipe_discovery import recipe_files

    return tuple(
        sorted(
            path
            for path in recipe_files(root, f"*{suffix}")
            if not IGNORED.intersection(path.relative_to(root).parts)
        )
    )


def check_structure(root: Path) -> Check:
    files = set(source_files(root / "examples", ".bicep"))
    if (root / "infra").exists():
        files.update(source_files(root / "infra", ".bicep"))
    files.update(source_files(root / "tools", ".sh"))
    files.update(source_files(root / "scripts", ".sh"))
    from tools.recipe_discovery import recipe_files

    for path in recipe_files(root / "examples", "*"):
        if path.is_file() and not IGNORED.intersection(path.relative_to(root).parts):
            if ".settings" in path.name or path.name.startswith(".env"):
                files.add(path)
    findings: list[Finding] = []
    if not files:
        return Check("structure", Status.INCOMPLETE, {"files": 0})
    public: list[Finding] = []
    shell_errors = 0
    try:
        for path in sorted(files):
            name = path.relative_to(root).as_posix()
            for number, line in enumerate(path.read_text().splitlines(), 1):
                for match in SECRET.finditer(line):
                    candidate = match.group(1)
                    if candidate.lower() not in {
                        "your_api_key_placeholder",
                        "replace_with_your_api_key",
                        "replace-with-strong-random-string",
                        "replace-with-your-webhook-secret",
                    }:
                        findings.append(Finding("HARDCODED_SECRET", name, number, "HIGH"))
                if path.suffix == ".bicep":
                    if re.search(
                        r"httpsOnly:\s*false|allowBlobPublicAccess:\s*true|"
                        r"(?:minTlsVersion|scmMinTlsVersion|minimumTlsVersion):\s*['\"]"
                        r"(?:TLS1_[01]|1\.[01])['\"]",
                        line,
                    ):
                        findings.append(Finding("INSECURE_TRANSPORT", name, number, "HIGH"))
                    if re.search(
                        r"publicNetworkAccess:\s*'Enabled'|allowBlobPublicAccess:\s*true", line
                    ):
                        public.append(Finding("PUBLIC_NETWORK_DEMO", name, number, "INFO"))
            if path.suffix == ".sh":
                process = subprocess.run(
                    ["bash", "-n", str(path)], capture_output=True, check=False, timeout=20
                )
                shell_errors += process.returncode != 0
        if shell_errors:
            return Check("structure", Status.TOOL_ERROR, {"shell_errors": shell_errors})
        return Check(
            "structure",
            Status.FAIL if findings else Status.PASS,
            {"files": len(files), "blocking": len(findings), "public_network_demo": len(public)},
            tuple(findings + public),
            tuple(p.relative_to(root).as_posix() for p in sorted(files)),
            message="Educational public networking; Azure validation pending",
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return Check("structure", Status.TOOL_ERROR, message="Structure scan could not complete")
