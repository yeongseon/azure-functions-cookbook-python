from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportUnusedParameter=false, reportAny=false, reportExplicitAny=false
import importlib
import json
import os
import threading
import time
from typing import Any

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_session_lock = threading.Lock()
_cached_session: Any | None = None
_dependency_loaded = False


def _lazy_import_requests() -> Any:
    global _dependency_loaded
    requests = importlib.import_module("requests")
    _dependency_loaded = True
    return requests


def _get_cached_session() -> Any:
    global _cached_session

    if _cached_session is not None:
        return _cached_session

    with _session_lock:
        if _cached_session is None:
            requests = _lazy_import_requests()
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
            session.mount("http://", adapter)  # nosec B501 # nosemgrep
            session.mount("https://", adapter)
            _cached_session = session
            logger.info("Created outbound session cache for this worker.")

    return _cached_session


def _preload_dependencies() -> dict[str, Any]:
    started = time.perf_counter()
    session = _get_cached_session()
    return {
        "dependencyLoaded": _dependency_loaded,
        "sessionCached": session is not None,
        "preloadMs": round((time.perf_counter() - started) * 1000, 2),
    }


def _maybe_probe_upstream(session: Any) -> dict[str, Any]:
    upstream_url = os.getenv("UPSTREAM_URL", "").strip()
    if not upstream_url:
        return {"enabled": False}

    timeout_seconds = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "2"))
    response = session.get(upstream_url, timeout=timeout_seconds)
    return {"enabled": True, "statusCode": response.status_code, "url": upstream_url}


@app.warm_up_trigger("warmup")
def warmup(warmup_context: object) -> None:
    _ = warmup_context
    metrics = _preload_dependencies()
    logger.info("Warmup trigger invoked; preloaded cold-start dependencies.", extra=metrics)


@app.route(route="cold-start-demo", methods=["GET"])
def cold_start_demo(req: func.HttpRequest) -> func.HttpResponse:
    session_before = _cached_session is not None
    session = _get_cached_session()

    should_probe = req.params.get("ping", "0") == "1"
    probe_result = _maybe_probe_upstream(session) if should_probe else {"enabled": False}

    payload = {
        "message": "Cold-start mitigation demo",
        "dependencyLoaded": _dependency_loaded,
        "sessionReused": session_before,
        "sessionCached": session is not None,
        "probe": probe_result,
        "recommendations": [
            "Use Premium plan for pre-warmed instances on latency-sensitive workloads.",
            "Keep imports lazy so startup work stays small.",
            "Cache outbound clients at module scope per worker.",
            "Run azure-functions-doctor-python before deployment"
            " when diagnosing cold-start regressions.",
        ],
    }

    logger.info(
        "HTTP cold-start demo invoked.",
        extra={
            "dependency_loaded": _dependency_loaded,
            "session_reused": session_before,
            "probe_enabled": should_probe,
        },
    )
    return func.HttpResponse(json.dumps(payload), mimetype="application/json", status_code=200)
