# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportAny=false, reportUntypedFunctionDecorator=false

from __future__ import annotations

import json
import logging
import os
import threading
import time
import socket
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from enum import Enum

import azure.functions as func


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class DownstreamServiceError(RuntimeError):
    pass


@dataclass(slots=True)
class CircuitSnapshot:
    state: str
    failure_count: int
    failure_threshold: int
    cooldown_seconds: float
    seconds_until_retry: float


class InMemoryCircuitBreaker:
    def __init__(self, failure_threshold: int, cooldown_seconds: float) -> None:
        self.failure_threshold: int = failure_threshold
        self.cooldown_seconds: float = cooldown_seconds
        self._lock: threading.Lock = threading.Lock()
        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._opened_at: float = 0.0
        self._probe_in_flight: bool = False

    def before_call(self) -> tuple[bool, str]:
        now = time.monotonic()
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = now - self._opened_at
                if elapsed >= self.cooldown_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._probe_in_flight = True
                    logging.info("Cooldown elapsed; circuit moved to half-open.")
                    return True, "half-open probe allowed"

                logging.warning("Circuit open; rejecting request during cooldown.")
                return False, "circuit open"

            if self._state == CircuitState.HALF_OPEN:
                if self._probe_in_flight:
                    logging.warning("Half-open probe already in flight; rejecting request.")
                    return False, "half-open probe already in flight"

                self._probe_in_flight = True
                return True, "half-open probe allowed"

            return True, "circuit closed"

    def record_success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = 0.0
            self._probe_in_flight = False
            logging.info("Downstream call succeeded; circuit closed.")

    def record_failure(self) -> None:
        now = time.monotonic()
        with self._lock:
            self._probe_in_flight = False

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = now
                logging.error("Half-open probe failed; circuit reopened.")
                return

            self._failure_count += 1
            logging.warning(
                "Downstream failure recorded. failure_count=%s threshold=%s",
                self._failure_count,
                self.failure_threshold,
            )

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = now
                logging.error("Circuit opened after repeated downstream failures.")

    def snapshot(self) -> CircuitSnapshot:
        now = time.monotonic()
        with self._lock:
            seconds_until_retry = 0.0
            if self._state == CircuitState.OPEN:
                remaining = self.cooldown_seconds - (now - self._opened_at)
                seconds_until_retry = max(0.0, remaining)

            return CircuitSnapshot(
                state=self._state.value,
                failure_count=self._failure_count,
                failure_threshold=self.failure_threshold,
                cooldown_seconds=self.cooldown_seconds,
                seconds_until_retry=round(seconds_until_retry, 2),
            )


def _load_int_setting(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        return max(1, int(raw_value))
    except ValueError:
        logging.warning("Invalid integer for %s=%s. Using default=%s", name, raw_value, default)
        return default


def _load_float_setting(name: str, default: float) -> float:
    raw_value = os.getenv(name, str(default))
    try:
        return max(1.0, float(raw_value))
    except ValueError:
        logging.warning("Invalid float for %s=%s. Using default=%s", name, raw_value, default)
        return default


FAILURE_THRESHOLD = _load_int_setting("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 3)
COOLDOWN_SECONDS = _load_float_setting("CIRCUIT_BREAKER_COOLDOWN_SECONDS", 15.0)
DOWNSTREAM_API_BASE_URL = os.getenv("DOWNSTREAM_API_BASE_URL", "https://httpstat.us")

breaker = InMemoryCircuitBreaker(
    failure_threshold=FAILURE_THRESHOLD,
    cooldown_seconds=COOLDOWN_SECONDS,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _build_downstream_url(status_code: int) -> str:
    base_url = DOWNSTREAM_API_BASE_URL.rstrip("/")
    return f"{base_url}/{status_code}"


def call_downstream_api(status_code: int, timeout_seconds: float) -> dict[str, object]:
    url = _build_downstream_url(status_code)
    logging.info("Calling downstream URL %s", url)
    request = urllib.request.Request(url=url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "status_code": response.getcode(),
                "body_preview": response_body[:200],
            }
    except urllib.error.HTTPError as exc:
        raise DownstreamServiceError(f"downstream returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise DownstreamServiceError(f"downstream unavailable: {exc.reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise DownstreamServiceError("downstream timed out") from exc


def _json_response(payload: dict[str, object], status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload, indent=2),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="circuit-breaker", methods=["GET"])
def circuit_breaker_demo(req: func.HttpRequest) -> func.HttpResponse:
    status_raw = req.params.get("status", "200")
    timeout_raw = req.params.get("timeout", "5")

    try:
        status_code = int(status_raw)
        timeout_seconds = max(1.0, float(timeout_raw))
    except ValueError:
        return _json_response(
            {
                "message": "Invalid query parameters. Use numeric status and timeout values.",
                "example": "/api/circuit-breaker?status=503&timeout=5",
            },
            status_code=400,
        )

    allowed, reason = breaker.before_call()
    if not allowed:
        snapshot = breaker.snapshot()
        return _json_response(
            {
                "message": "Request blocked by circuit breaker.",
                "reason": reason,
                "breaker": asdict(snapshot),
            },
            status_code=503,
        )

    try:
        downstream = call_downstream_api(status_code=status_code, timeout_seconds=timeout_seconds)
    except DownstreamServiceError as exc:
        breaker.record_failure()
        snapshot = breaker.snapshot()
        return _json_response(
            {
                "message": "Downstream call failed.",
                "error": str(exc),
                "breaker": asdict(snapshot),
            },
            status_code=502,
        )

    breaker.record_success()
    snapshot = breaker.snapshot()
    return _json_response(
        {
            "message": "Downstream call succeeded.",
            "breaker": asdict(snapshot),
            "downstream": downstream,
        },
        status_code=200,
    )
