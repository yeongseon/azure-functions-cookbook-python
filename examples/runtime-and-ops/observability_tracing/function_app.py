from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false

import json
import uuid

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging, with_context

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

CORRELATION_HEADER = "x-correlation-id"
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"


def _new_trace_id() -> str:
    return uuid.uuid4().hex


def _new_span_id() -> str:
    return uuid.uuid4().hex[:16]


def _extract_or_create_traceparent(req: func.HttpRequest) -> tuple[str, str, str, bool]:
    inbound = (req.headers.get(TRACEPARENT_HEADER) or "").strip()
    if inbound:
        parts = inbound.split("-")
        if len(parts) == 4 and len(parts[1]) == 32 and len(parts[2]) == 16:
            return inbound, parts[1], parts[2], False

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
def trace_demo(req: func.HttpRequest) -> func.HttpResponse:
    traceparent, trace_id, span_id, generated_traceparent = _extract_or_create_traceparent(req)
    correlation_id = _extract_or_create_correlation_id(req)
    tracestate = req.headers.get(TRACESTATE_HEADER)

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
