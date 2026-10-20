"""Deterministic Python worker signature-registration guard (#379, #380).

Twelve handlers across eight recipes previously failed actual Python worker
registration because their public binding annotations (structural Protocols,
a union, or ``list[dict[str, Any]]``) are incompatible with the real binding
converters (#379). Separately, CQRS's ``create_order`` placed its
``@app.cosmos_db_output`` decorator below ordinary wrappers, splitting the
Cosmos output onto a different SDK builder than the one carrying its HTTP
trigger, so ``app.get_functions()`` could not even discover the app before
the worker could attempt registration (#380). Importing a module,
registering decorators with the SDK, or invoking a handler with a duck-typed
fake exercises neither failure mode -- only the official worker's
``Registry.add_indexed_function()`` does, which reads the *effective*
decorated signature via ``inspect.signature()``/``typing.get_type_hints()``
and calls the installed SDK's real binding converters, after
``app.get_functions()`` has already discovered the app's functions.

This module clones the pinned upstream ``azure-functions-python-worker`` SHA
once per session, copies its checked-in protobuf test fixtures (never
modifying worker source), and indexes each listed recipe handler's real SDK
``Function`` object through that worker. Marked ``worker_registration`` and
excluded from the default test run (requires network + git); run explicitly
with ``pytest -m worker_registration``.
"""

from __future__ import annotations

from collections.abc import Iterator
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any

import pytest

from tests._isolation import load_example_module

pytestmark = pytest.mark.worker_registration

WORKER_SHA = "61af68115f048e917f786b707e92796c22eeb4de"

# (recipe path, handler function name) pairs this guard protects (#379, #380).
AFFECTED_HANDLERS: list[tuple[str, str]] = [
    ("messaging-and-pubsub/eventgrid_router", "route_events"),
    ("messaging-and-pubsub/eventgrid_domain_events", "publish_order_event"),
    ("messaging-and-pubsub/eventgrid_domain_events", "handle_order_domain_event"),
    ("messaging-and-pubsub/servicebus_dlq_replay", "inspect_dead_letter_queue"),
    ("messaging-and-pubsub/servicebus_dlq_replay", "replay_dead_letter_queue"),
    ("async-apis-and-jobs/callback_completion", "submit_task"),
    ("async-apis-and-jobs/callback_completion", "process_task"),
    ("reliability/poison_message_handling", "queue_processor"),
    ("reliability/poison_message_handling", "poison_handler"),
    ("security-and-tenancy/secretless_keyvault", "secretless_keyvault"),
    ("reliability/outbox_pattern", "create_order"),
    ("reliability/outbox_pattern", "relay_outbox_events"),
    ("data-and-pipelines/cqrs_read_projection", "create_order"),
    ("data-and-pipelines/cqrs_read_projection", "project_order_read_models"),
    ("data-and-pipelines/cqrs_read_projection", "get_order_projection"),
]


def _clone_worker(destination: Path) -> bool:
    """Clone the pinned worker SHA into *destination*. Returns False (and
    leaves *destination* unusable) if git/network is unavailable, so the
    caller can skip rather than fail the whole guard on an infra outage."""
    try:
        subprocess.run(["git", "init", "-q", str(destination)], check=True, timeout=30)
        subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "remote",
                "add",
                "origin",
                "https://github.com/Azure/azure-functions-python-worker.git",
            ],
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["git", "-C", str(destination), "fetch", "--depth=1", "origin", WORKER_SHA],
            check=True,
            timeout=60,
        )
        subprocess.run(
            ["git", "-C", str(destination), "checkout", "-q", "--detach", "FETCH_HEAD"],
            check=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    actual = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    return actual == WORKER_SHA


@pytest.fixture(scope="module")
def worker_registry() -> Iterator[ModuleType]:
    """Yield the ``azure_functions_worker.functions`` module from the pinned
    upstream SHA, with its binding registry already loaded. Skips the whole
    module if the worker cannot be cloned (no network) or its real SDK
    converters cannot be imported (missing ``azure-functions``/
    ``azurefunctions-extensions-base``)."""
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="cookbook-worker-") as worker_dir_str:
        worker_dir = Path(worker_dir_str)
        if not _clone_worker(worker_dir):
            pytest.skip("Could not clone azure-functions-python-worker (no network?)")

        with tempfile.TemporaryDirectory(prefix="cookbook-registry-") as runtime_dir_str:
            runtime_dir = Path(runtime_dir_str)
            package = runtime_dir / "azure_functions_worker"
            shutil.copytree(
                worker_dir / "workers/azure_functions_worker",
                package,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            proto_fixture = worker_dir / "runtimes/v1/tests/protos"
            for source in proto_fixture.rglob("*_pb2*.py"):
                target = package / "protos" / source.relative_to(proto_fixture)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            added_paths = [str(runtime_dir), str(repo_root), str(repo_root / "src")]
            sys.path[:0] = added_paths
            try:
                from azure_functions_worker import functions as worker_functions
                from azure_functions_worker.bindings import load_binding_registry
            except ImportError as error:
                pytest.skip(f"Worker's real SDK converters unavailable: {error}")
            try:
                load_binding_registry()
            except Exception as error:  # noqa: BLE001
                pytest.skip(f"Could not load the worker's binding registry: {error}")

            try:
                yield worker_functions
            finally:
                for path in added_paths:
                    if path in sys.path:
                        sys.path.remove(path)
                for name in list(sys.modules):
                    if name == "azure_functions_worker" or name.startswith(
                        "azure_functions_worker."
                    ):
                        del sys.modules[name]


def _index(worker_functions: ModuleType, function: Any) -> dict[str, Any]:
    try:
        info = worker_functions.Registry().add_indexed_function(function)
    except Exception as error:  # noqa: BLE001
        return {"result": "rejected", "exception": type(error).__name__, "message": str(error)}
    return {"result": "accepted", "requires_context": info.requires_context}


@pytest.mark.parametrize("recipe_path,handler_name", AFFECTED_HANDLERS)
def test_handler_registers_with_the_real_worker(
    worker_registry: ModuleType, recipe_path: str, handler_name: str
) -> None:
    module = load_example_module(recipe_path)
    functions = module.app.get_functions()
    function = next(f for f in functions if f.get_function_name() == handler_name)

    result = _index(worker_registry, function)

    assert result["result"] == "accepted", (
        f"{recipe_path}:{handler_name} failed real worker registration: {result}"
    )


def test_guard_environment_is_reported() -> None:
    """Record the SDK/worker versions used for indexing verification,
    distinguishing this in-process Registry check from real-host execution
    (per the issue's acceptance criteria)."""
    versions = {
        name: importlib.metadata.version(name)
        for name in ("azure-functions", "azurefunctions-extensions-base")
        if _is_installed(name)
    }
    assert "azure-functions" in versions
    print(f"worker_registration guard environment: worker_sha={WORKER_SHA} packages={versions}")


def _is_installed(name: str) -> bool:
    try:
        importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True
