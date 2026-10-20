"""Regression coverage for #365: validate trace context before propagating it.

The recipe's traceparent parser only checked field count and ID lengths,
never the hexadecimal syntax, nonzero IDs, version, or flags. An all-zero
trace ID and non-hexadecimal flags both passed through unchanged while
generated_traceparent reported false, producing a header OpenTelemetry's
standard propagator rejects.

A related pairing bug: when traceparent was missing or malformed and the
recipe generated a replacement trace, it still forwarded the inbound
tracestate -- vendor state belonging to the original/absent trace.

Exercises the actual registered HTTP handler with an inert request
context; opentelemetry-api is used solely as an independent
standards-aware consumer of the emitted traceparent header. No exporter
or network call is involved.
"""

from __future__ import annotations

from collections.abc import Callable
import json
from types import SimpleNamespace

import azure.functions as func
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from tests._isolation import load_example_module

EXAMPLE_PATH = "runtime-and-ops/observability_tracing"

VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

TraceHandler = Callable[..., func.HttpResponse]


def _context() -> func.Context:
    return SimpleNamespace(  # type: ignore[return-value]
        invocation_id="offline-test", function_name="trace_demo"
    )


def _request(traceparent: str | None, tracestate: str | None = "review=opaque") -> func.HttpRequest:
    headers: dict[str, str] = {}
    if tracestate is not None:
        headers["tracestate"] = tracestate
    if traceparent is not None:
        headers["traceparent"] = traceparent
    return func.HttpRequest(
        method="GET", url="http://localhost/api/trace-demo", headers=headers, params={}, body=b""
    )


def _handler() -> TraceHandler:
    module = load_example_module(EXAMPLE_PATH)
    handler: TraceHandler = next(
        f.get_user_function()
        for f in module.app.get_functions()
        if f.get_function_name() == "trace_demo"
    )
    return handler


def _otel_accepts(traceparent: str) -> bool:
    extracted = TraceContextTextMapPropagator().extract({"traceparent": traceparent})
    return trace.get_current_span(extracted).get_span_context().is_valid


def test_valid_traceparent_is_reused_and_tracestate_is_forwarded() -> None:
    handler = _handler()

    response = handler(req=_request(VALID_TRACEPARENT), context=_context())

    payload = json.loads(response.get_body())
    assert payload["generated_traceparent"] == "false"
    assert response.headers["traceparent"] == VALID_TRACEPARENT
    assert _otel_accepts(response.headers["traceparent"])
    assert response.headers.get("tracestate") == "review=opaque"


def test_all_zero_trace_id_is_rejected_and_replaced() -> None:
    handler = _handler()
    zero_trace_id = "00-" + "0" * 32 + "-00f067aa0ba902b7-01"

    response = handler(req=_request(zero_trace_id), context=_context())

    payload = json.loads(response.get_body())
    assert payload["generated_traceparent"] == "true"
    assert response.headers["traceparent"] != zero_trace_id
    assert _otel_accepts(response.headers["traceparent"])
    assert response.headers.get("tracestate") is None


def test_invalid_flags_are_rejected_and_replaced() -> None:
    handler = _handler()
    invalid_flags = VALID_TRACEPARENT[:-2] + "zz"

    response = handler(req=_request(invalid_flags), context=_context())

    payload = json.loads(response.get_body())
    assert payload["generated_traceparent"] == "true"
    assert response.headers["traceparent"] != invalid_flags
    assert _otel_accepts(response.headers["traceparent"])
    assert response.headers.get("tracestate") is None


def test_malformed_traceparent_generates_valid_replacement_without_tracestate() -> None:
    handler = _handler()

    response = handler(req=_request("malformed"), context=_context())

    payload = json.loads(response.get_body())
    assert payload["generated_traceparent"] == "true"
    assert _otel_accepts(response.headers["traceparent"])
    assert response.headers.get("tracestate") is None


def test_missing_traceparent_generates_valid_replacement_without_tracestate() -> None:
    handler = _handler()

    response = handler(req=_request(None), context=_context())

    payload = json.loads(response.get_body())
    assert payload["generated_traceparent"] == "true"
    assert _otel_accepts(response.headers["traceparent"])
    assert response.headers.get("tracestate") is None
