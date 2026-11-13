"""Pure workflow rules: request validation, approval decisions, status mapping, publishing.

Nothing here imports Durable or Azure, so every rule is unit-testable without a host.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.limits import (
    DEFAULT_APPROVAL_TIMEOUT_SECONDS,
    MAX_APPROVAL_TIMEOUT_SECONDS,
    MAX_PROMPT_CHARS,
    MAX_REQUEST_BYTES,
    MIN_APPROVAL_TIMEOUT_SECONDS,
    STAGE_AWAITING_APPROVAL,
)


class RequestError(ValueError):
    """The caller sent something this API will not accept (maps to HTTP 400)."""


@dataclass(frozen=True)
class RunRequest:
    prompt: str
    approval_timeout_seconds: int


def _object(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise RequestError("request body too large")
    try:
        body = json.loads(raw or b"null")
    except ValueError as exc:
        raise RequestError("body must be valid JSON") from exc
    if not isinstance(body, dict):
        raise RequestError("body must be a JSON object")
    return body


def parse_run_request(raw: bytes) -> RunRequest:
    body = _object(raw)
    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RequestError("prompt must be a non-empty string")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise RequestError(f"prompt must be at most {MAX_PROMPT_CHARS} characters")
    timeout = body.get("approval_timeout_seconds", DEFAULT_APPROVAL_TIMEOUT_SECONDS)
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise RequestError("approval_timeout_seconds must be an integer")
    if not MIN_APPROVAL_TIMEOUT_SECONDS <= timeout <= MAX_APPROVAL_TIMEOUT_SECONDS:
        raise RequestError(
            "approval_timeout_seconds must be between "
            f"{MIN_APPROVAL_TIMEOUT_SECONDS} and {MAX_APPROVAL_TIMEOUT_SECONDS}"
        )
    return RunRequest(prompt=prompt, approval_timeout_seconds=timeout)


def parse_decision(raw: bytes) -> bool:
    approved = _object(raw).get("approved")
    if not isinstance(approved, bool):
        raise RequestError("approved must be true or false")
    return approved


def clamp_timeout(value: Any) -> int:
    """Deterministic clamp used inside the orchestrator (input comes from replayed history)."""
    if isinstance(value, bool) or not isinstance(value, int):
        return DEFAULT_APPROVAL_TIMEOUT_SECONDS
    return max(MIN_APPROVAL_TIMEOUT_SECONDS, min(MAX_APPROVAL_TIMEOUT_SECONDS, value))


def is_approval(decision: Any) -> bool:
    """Fail closed: only an explicit ``{"approved": true}`` authorises the final action."""
    return isinstance(decision, dict) and decision.get("approved") is True


# --- status mapping -------------------------------------------------------------------------

_OUTCOMES = {"completed", "rejected", "timed_out", "failed"}


def normalize_status(runtime_status: str | None, custom: Any, output: Any) -> dict[str, Any] | None:
    """Map a Durable instance to this API's status vocabulary; ``None`` means unknown run."""
    if runtime_status is None:
        return None
    if runtime_status == "Pending":
        return {"status": "pending"}
    if runtime_status == "Suspended":
        return {"status": "suspended"}
    if runtime_status in {"Running", "ContinuedAsNew"}:
        info = custom if isinstance(custom, dict) else {}
        if info.get("stage") == STAGE_AWAITING_APPROVAL:
            return {"status": "awaiting_approval", "draft": info.get("draft")}
        return {"status": "running", "stage": info.get("stage")}
    if runtime_status == "Completed":
        outcome = output.get("outcome") if isinstance(output, dict) else None
        if outcome in _OUTCOMES:
            return {"status": outcome, "result": output}
        return {"status": "failed", "result": {"outcome": "failed", "error": "unexpected_output"}}
    if runtime_status in {"Terminated", "Canceled"}:
        return {"status": "cancelled"}
    # Durable's failure output can carry exception text, so never pass it through.
    return {"status": "failed", "error": {"code": "run_failed", "message": "The run failed."}}


def is_terminal(runtime_status: str | None) -> bool:
    return runtime_status in {"Completed", "Failed", "Terminated", "Canceled"}


# --- publishing (the harmless "side effect") ------------------------------------------------


class ResultSink(Protocol):
    def record(self, key: str, summary: dict[str, Any]) -> bool:
        """Store ``summary`` under ``key``; return ``False`` if the key already existed."""
        ...


class InMemorySink:
    """Per-process demo store. It is lost on restart and not shared between instances.

    In Azure, replace it with a store whose write is atomic per key (for example a table upsert or
    a conditional create), so the idempotency below holds across workers.
    """

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def record(self, key: str, summary: dict[str, Any]) -> bool:
        if key in self.records:
            return False
        self.records[key] = summary
        return True


def publish_key(run_id: str) -> str:
    """Idempotency key: stable across redeliveries of the same run's publish activity."""
    return f"publish:{run_id}"


def publish_approved(run_id: str, draft: str, sink: ResultSink) -> dict[str, Any]:
    """Record the approved draft once per run and return the same receipt on every delivery."""
    receipt = hashlib.sha256(f"{run_id}:{draft}".encode()).hexdigest()[:16]
    created = sink.record(
        publish_key(run_id), {"receipt": receipt, "chars": len(draft), "run_id": run_id}
    )
    return {"receipt": receipt, "chars": len(draft), "duplicate_delivery": not created}
