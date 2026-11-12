"""Generate docs/compatibility.md from this repository's manifests and recorded CI evidence.

Declared ranges come from ``pyproject.toml``, ``constraints-min.txt`` and every recipe's
``pyproject.toml``. Evidence (which versions CI actually installed or ran against a Functions
host, with date and run reference) comes from ``docs/compat-evidence.json``, which is written
only from real GitHub Actions runs:

    python scripts/gen_compat_table.py                       # rewrite docs/compatibility.md
    python scripts/gen_compat_table.py --check               # exit 1 if it is stale
    python scripts/gen_compat_table.py --record RUN_ID...    # refresh evidence with ``gh``

Tags: ``declared`` (a manifest allows it), ``installed`` (a CI job installed and ran the
library suite on it) and ``host-tested`` (a CI job started a Functions host on it). A tag never
implies a stronger one. There is no combination matrix: only the combinations CI actually ran.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from typing import Any

from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = REPO_ROOT / "docs" / "compat-evidence.json"
OUTPUT = REPO_ROOT / "docs" / "compatibility.md"
SLUG = "yeongseon/azure-functions-cookbook-python"
TRACKED = (
    "azure-functions",
    "azure-functions-durable",
    "pydantic",
    "azure-functions-openapi",
    "azure-functions-validation",
    "azure-functions-logging",
    "azure-functions-db",
    "azure-functions-langgraph",
    "azure-functions-doctor",
    "langgraph",
)
# job-name pattern -> (tag, scope). Only these jobs are recorded as evidence.
JOB_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        r"^Test \(Py (3\.\d+), minimum deps\)$",
        "installed",
        "library suite on the lowest declared floors (`constraints-min.txt`)",
    ),
    (
        r"^Test \(Py (3\.\d+), latest deps\)$",
        "installed",
        "library suite on the latest compatible releases",
    ),
    (
        r"^Recipe host smoke \((.+)\)$",
        "host-tested",
        "Functions host smoke with Azurite",
    ),
    (
        r"^E2E \(latest toolkit\)$",
        "host-tested",
        "local-host e2e tier on the latest PyPI toolkit releases",
    ),
)
_NAME_VERSION = re.compile(r"^(.+?)-(\d[^-]*)$")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _specs(pyproject: Path) -> list[str]:
    project = tomllib.loads(_text(pyproject)).get("project", {})
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs.extend(group)
    return specs


def _split(spec: str) -> tuple[str, str]:
    match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(.*?)\s*(?:;.*)?$", spec)
    if not match:
        raise ValueError(f"unparseable requirement: {spec!r}")
    return str(canonicalize_name(match.group(1))), match.group(2)


def inventory() -> dict[str, Any]:
    """Declared Python/package ranges from the manifests (the drift-tested inputs)."""
    root = tomllib.loads(_text(REPO_ROOT / "pyproject.toml"))
    root_ranges = {}
    for spec in _specs(REPO_ROOT / "pyproject.toml"):
        name, rng = _split(spec)
        if name in TRACKED:
            root_ranges[name] = rng
    min_pins = {}
    for line in _text(REPO_ROOT / "constraints-min.txt").splitlines():
        if line and not line.startswith("#"):
            name, pin = line.split("==", 1)
            if canonicalize_name(name) in TRACKED:
                min_pins[str(canonicalize_name(name))] = pin.strip()
    recipes: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for pyproject in sorted((REPO_ROOT / "examples").glob("*/*/pyproject.toml")):
        slug = pyproject.parent.name
        for spec in _specs(pyproject):
            name, rng = _split(spec)
            if name in TRACKED and slug not in recipes[name][rng or "(unpinned)"]:
                recipes[name][rng or "(unpinned)"].append(slug)
    return {
        "requires_python": root["project"]["requires-python"],
        "root": root_ranges,
        "min_pins": min_pins,
        "recipes": {n: {r: sorted(s) for r, s in sorted(v.items())} for n, v in recipes.items()},
    }


def digest(inv: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(inv, sort_keys=True).encode()).hexdigest()[:16]


def _lower_bound(rng: str) -> Version | None:
    for spec in SpecifierSet(rng.replace(" ", "")) if rng and rng != "(unpinned)" else ():
        if spec.operator in (">=", "~=", "=="):
            return Version(spec.version)
    return None


def _versions(installed: dict[str, str]) -> str:
    return "; ".join(f"{name} {installed[name]}" for name in TRACKED if name in installed) or "-"


def render(inv: dict[str, Any], evidence: dict[str, Any]) -> str:
    stale = evidence["inventory_digest"] != digest(inv)
    out = [
        "# Compatibility evidence",
        "",
        "<!-- Generated by scripts/gen_compat_table.py from the manifests and "
        "docs/compat-evidence.json. Do not edit by hand. -->",
        "",
        "This page separates what the manifests **declare** from what CI **installed** and what "
        "CI **ran on a Functions host**. Each tag below is backed only by the listed CI run; "
        "nothing here is a support promise (see [Versions, snapshots, and verification]"
        "(snapshots-and-verification.md)).",
        "",
        "- `declared`: a manifest allows the combination. No CI run is implied.",
        "- `installed`: a CI job installed the combination and ran the library test suite.",
        "- `host-tested`: a CI job started a Functions host on the combination and called it.",
        "",
    ]
    if stale:
        out += [
            "> **Evidence is older than the manifests.** The declared ranges below changed after "
            "the CI runs were recorded, so the `installed` and `host-tested` rows describe the "
            "earlier manifests. Re-record with "
            "`python scripts/gen_compat_table.py --record RUN_ID`.",
            "",
        ]
    out += [
        "## Declared ranges",
        "",
        f"Python: `{inv['requires_python']}` (`requires-python` in `pyproject.toml`).",
        "",
        "| Package | Root range | Recipe ranges (recipes) | Lowest declared floor "
        "| Lowest version CI installs | Floor installed by CI? |",
        "|---|---|---|---|---|---|",
    ]
    for name in TRACKED:
        recipes = inv["recipes"].get(name, {})
        pin = inv["min_pins"].get(name)
        root = inv["root"].get(name)
        cells = "; ".join(f"`{rng}` ({len(slugs)})" for rng, slugs in recipes.items()) or "-"
        bounds = [_lower_bound(root or ""), *(_lower_bound(rng) for rng in recipes)]
        floor = min((b for b in bounds if b is not None), default=None)
        if floor is None or pin is None:
            verdict = "-"
        else:
            verdict = "yes" if floor >= Version(pin) else "no"
        out.append(
            f"| `{name}` | {f'`{root}`' if root else '-'} | {cells} "
            f"| {f'`{floor}`' if floor is not None else '-'} | {f'`{pin}`' if pin else '-'} "
            f"| {verdict} |"
        )
    out += [
        "",
        "`no` means some manifest declares a floor lower than anything CI installs, so that "
        "floor is declared but not installed. `(unpinned)` recipes declare no floor.",
        "",
        "## Combinations CI actually ran",
        "",
        "| Tag | Python | What ran | Resolved versions | CI job | Date | Run |",
        "|---|---|---|---|---|---|---|",
        f"| declared | `{inv['requires_python']}` | all manifests | root ranges above "
        "| - | - | - |",
    ]
    for run in evidence["runs"]:
        for job in run["jobs"]:
            out.append(
                f"| {job['tag']} | {job['python']} | {job['scope']} "
                f"| {_versions(job['installed'])} | {job['name']} | {job['date']} "
                f"| [{run['run_id']}]({run['url']}) |"
            )
    out += [
        "",
        "Runs: "
        + "; ".join(
            f"{r['workflow']} run {r['run_id']} at commit `{r['head_sha'][:7]}`"
            for r in evidence["runs"]
        )
        + ".",
        "",
    ]
    hosts = ", ".join(
        sorted(
            {j["python"] for r in evidence["runs"] for j in r["jobs"] if j["tag"] == "host-tested"}
        )
    )
    out += [
        "## Not covered",
        "",
        "- No CI job deploys to Azure, so nothing here is Azure-verified.",
        "- Only the recipes named in the `host-tested` rows were started on a Functions host; "
        "every other recipe is covered at most by unit or import tests.",
        "- Versions between the lowest tested and the latest are not installed.",
        f"- `host-tested` rows ran on Python {hosts} only.",
    ]
    if not any(r["workflow"] == "E2E Toolkit Matrix" for r in evidence["runs"]):
        out.append(
            "- The weekly `E2E Toolkit Matrix` run is not recorded: recording requires a run on "
            "the current manifests, and none exists yet."
        )
    return "\n".join([*out, ""])


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _installed(log: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in log.splitlines():
        if "Successfully installed" in line:
            for token in line.split("Successfully installed", 1)[1].split():
                match = _NAME_VERSION.match(token)
                if match and canonicalize_name(match.group(1)) in TRACKED:
                    found[str(canonicalize_name(match.group(1)))] = match.group(2)
        else:
            match = re.search(r"Z\s+([A-Za-z0-9._-]+)\s{2,}(\d[\w.]*)\s*$", line)
            if match and canonicalize_name(match.group(1)) in TRACKED:
                found.setdefault(str(canonicalize_name(match.group(1))), match.group(2))
    return found


def record(run_ids: list[str]) -> dict[str, Any]:
    inv = inventory()
    runs = []
    for run_id in run_ids:
        data = json.loads(
            _gh("run", "view", run_id, "-R", SLUG, "--json", "workflowName,url,headSha,jobs")
        )
        drift = subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                data["headSha"],
                "--",
                "pyproject.toml",
                "constraints-min.txt",
                "examples",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        if drift.returncode != 0:
            raise SystemExit(
                f"manifests changed since run {run_id} ({data['headSha'][:7]}); "
                "record a run on the current manifests"
            )
        jobs = []
        for job in data["jobs"]:
            for pattern, tag, scope_text in JOB_SPECS:
                match = re.match(pattern, job["name"])
                if not match:
                    continue
                if job["conclusion"] != "success":
                    raise SystemExit(f"{job['name']} did not succeed in run {run_id}")
                log = _gh(
                    "run", "view", run_id, "-R", SLUG, "--log", "--job", str(job["databaseId"])
                )
                python = re.search(r"Successfully set up CPython \((3\.\d+)", log)
                tools = re.search(r"Core Tools Version:\s+(\d+\.\d+\.\d+)", log)
                scope = scope_text
                if match.groups() and not match.group(1).startswith("3."):
                    scope = f"{scope_text}: recipe `{match.group(1)}`"
                if tools:
                    scope += f" (Core Tools {tools.group(1)})"
                label = (
                    match.group(1) if match.groups() and match.group(1).startswith("3.") else None
                )
                jobs.append(
                    {
                        "name": job["name"],
                        "tag": tag,
                        "python": label or (python.group(1) if python else "?"),
                        "scope": scope,
                        "date": job["completedAt"][:10],
                        "installed": _installed(log),
                    }
                )
        runs.append(
            {
                "workflow": data["workflowName"],
                "run_id": int(run_id),
                "url": data["url"],
                "head_sha": data["headSha"],
                "jobs": sorted(jobs, key=lambda j: (j["tag"], j["name"])),
            }
        )
    return {"schema": 1, "inventory_digest": digest(inv), "runs": runs}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="Fail if docs/compatibility.md is stale"
    )
    parser.add_argument(
        "--record", nargs="+", metavar="RUN_ID", help="Record evidence from CI runs"
    )
    args = parser.parse_args(argv)
    if args.record:
        EVIDENCE.write_text(json.dumps(record(args.record), indent=2) + "\n", encoding="utf-8")
    generated = render(inventory(), json.loads(_text(EVIDENCE)))
    if args.check:
        if not OUTPUT.is_file() or _text(OUTPUT) != generated:
            print(
                "docs/compatibility.md is stale. Run: python scripts/gen_compat_table.py",
                file=sys.stderr,
            )
            return 1
        print("docs/compatibility.md is up to date.")
        return 0
    OUTPUT.write_text(generated, encoding="utf-8")
    print("Wrote docs/compatibility.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
