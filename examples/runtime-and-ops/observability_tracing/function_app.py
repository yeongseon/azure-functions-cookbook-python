from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false
import json
import re
import uuid

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

CORRELATION_HEADER = "x-correlation-id"
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"

# W3C Trace Context traceparent syntax: 2-hex version, 32-hex trace-id,
# 16-hex parent-id, 2-hex flags, each lowercase and dash-separated. This
# recipe only supports version 00 (the only version in the spec today).
_TRACEPARENT_PATTERN = re.compile(
    r"^00-(?P<trace_id>[0-9a-f]{32})-(?P<parent_id>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)
_ALL_ZERO_TRACE_ID = "0" * 32
_ALL_ZERO_SPAN_ID = "0" * 16


def _new_trace_id() -> str:
    return uuid.uuid4().hex


def _new_span_id() -> str:
    return uuid.uuid4().hex[:16]


def _is_valid_traceparent(inbound: str) -> tuple[str, str] | None:
    """Validate a traceparent per W3C Trace Context: hex syntax, version
    00, and nonzero trace/parent IDs. Returns (trace_id, span_id) when
    valid, None otherwise -- the two failure modes this fixes (bad hex
    syntax and all-zero IDs) are otherwise both accepted silently.
    """
    match = _TRACEPARENT_PATTERN.match(inbound)
    if match is None:
        return None
    trace_id = match.group("trace_id")
    parent_id = match.group("parent_id")
    if trace_id == _ALL_ZERO_TRACE_ID or parent_id == _ALL_ZERO_SPAN_ID:
        return None
    return trace_id, parent_id


def _extract_or_create_traceparent(req: func.HttpRequest) -> tuple[str, str, str, bool]:
    inbound = (req.headers.get(TRACEPARENT_HEADER) or "").strip()
    if inbound:
        validated = _is_valid_traceparent(inbound)
        if validated is not None:
            trace_id, span_id = validated
            return inbound, trace_id, span_id, False

    trace_id = _new_trace_id()
    span_id = _new_span_id()
    return f"00-{trace_id}-{span_id}-01", trace_id, span_id, True


def _extract_or_create_correlation_id(req: func.HttpRequest) -> str:
    return (
        req.headers.get(CORRELATION_HEADER)
        or req.headers.get("x-ms-client-tracking-id")
        or f"corr-{uuid.uuid4().hex[:12]}"
    )


def _json_response(payload: dict[str, str], headers: dict[str, str]) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        mimetype="application/json",
        headers=headers,
    )


@app.route(route="trace-demo", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
@with_context
def trace_demo(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    traceparent, trace_id, span_id, generated_traceparent = _extract_or_create_traceparent(req)
    correlation_id = _extract_or_create_correlation_id(req)
    # tracestate is vendor-specific state tied to its accompanying trace.
    # Only forward it when the inbound traceparent was valid and reused
    # unchanged; a newly generated trace must not carry state belonging to
    # a different (or absent/invalid) trace.
    tracestate = req.headers.get(TRACESTATE_HEADER) if not generated_traceparent else None

    logger.info(
        "Received traced HTTP request.",
        extra={
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "generated_traceparent": generated_traceparent,
            "method": req.method,
            "url": req.url,
        },
    )
    logger.info(
        "Emitted custom telemetry event.",
        extra={
            "telemetry_type": "custom_event",
            "event_name": "observability_trace_demo",
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "span_id": span_id,
        },
    )

    payload = {
        "message": "Tracing metadata attached to logs and response.",
        "correlation_id": correlation_id,
        "traceparent": traceparent,
        "trace_id": trace_id,
        "span_id": span_id,
        "generated_traceparent": str(generated_traceparent).lower(),
    }
    headers = {
        CORRELATION_HEADER: correlation_id,
        TRACEPARENT_HEADER: traceparent,
    }
    if tracestate:
        headers[TRACESTATE_HEADER] = tracestate

    return _json_response(payload, headers)
