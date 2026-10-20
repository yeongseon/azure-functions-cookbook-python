"""Regression coverage for #357: validate JSON object shape before reading
request fields.

Six HTTP handlers across five recipes assumed successful JSON parsing
implies a dict. Valid JSON such as ``null``, ``[]``, or ``"hello"`` reached
``.get()`` and raised an uncaught ``AttributeError`` instead of a controlled
4xx response. Exercises the actual registered handlers (or their
request-shape helpers) with real ``func.HttpRequest`` objects; no network
calls or cloud resources are used.
"""

from __future__ import annotations

from collections.abc import Callable
import json
from unittest.mock import patch

import azure.functions as func

from tests._isolation import load_example_module

NON_OBJECT_BODIES = (b"null", b"[]", b'"hello"')


def _request(body: bytes, method: str = "POST") -> func.HttpRequest:
    return func.HttpRequest(
        method=method,
        url="https://example.invalid/api/review",
        params={},
        body=body,
        headers={"Content-Type": "application/json"},
    )


class _QueueOutput:
    value: object = None

    def set(self, value: object) -> None:
        self.value = value


def _get_handler(module: object, function_name: str) -> Callable[..., func.HttpResponse]:
    handler: Callable[..., func.HttpResponse] = next(
        f.get_user_function()
        for f in module.app.get_functions()  # type: ignore[attr-defined]
        if f.get_function_name() == function_name
    )
    return handler


def test_outbox_pattern_create_order_rejects_non_object_bodies() -> None:
    module = load_example_module("reliability/outbox_pattern")
    handler = _get_handler(module, "create_order")

    with patch.object(module, "_store_order_and_outbox") as store:
        for body in NON_OBJECT_BODIES:
            response = handler(req=_request(body))
            assert response.status_code == 400

        store.assert_not_called()


def test_blueprint_modular_app_create_user_rejects_non_object_bodies() -> None:
    load_example_module("runtime-and-ops/blueprint_modular_app")
    from app.functions.users import create_user_route  # noqa: PLC0415

    for body in NON_OBJECT_BODIES:
        response = create_user_route(_request(body))
        assert response.status_code == 400


def test_output_binding_vs_sdk_binding_route_rejects_non_object_bodies_safely() -> None:
    load_example_module("runtime-and-ops/output_binding_vs_sdk")
    from app.functions.binding_route import enqueue_via_binding  # noqa: PLC0415

    for body in NON_OBJECT_BODIES:
        output = _QueueOutput()
        response = enqueue_via_binding(req=_request(body), output_message=output)
        # This recipe intentionally defaults to a demo task on malformed
        # input rather than rejecting it -- preserve that documented
        # behavior while no longer crashing on non-object JSON.
        assert response.status_code == 200
        payload = json.loads(response.get_body())
        assert payload["task"] == "demo-task"


def test_output_binding_vs_sdk_sdk_route_rejects_non_object_bodies_safely() -> None:
    load_example_module("runtime-and-ops/output_binding_vs_sdk")
    import os  # noqa: PLC0415

    from app.functions.sdk_route import enqueue_via_sdk  # noqa: PLC0415

    with patch.dict(os.environ, {"StorageConnection": ""}):
        for body in NON_OBJECT_BODIES:
            response = enqueue_via_sdk(req=_request(body))
            assert response.status_code == 500
            assert "StorageConnection" in response.get_body().decode()


def test_queue_producer_enqueue_task_rejects_non_object_bodies() -> None:
    load_example_module("messaging-and-pubsub/queue_producer")
    from app.functions.enqueue import enqueue_task  # noqa: PLC0415

    for body in NON_OBJECT_BODIES:
        output = _QueueOutput()
        response = enqueue_task(req=_request(body), msg=output)
        assert response.status_code == 400
        assert output.value is None


def test_local_run_and_direct_invoke_greet_rejects_non_object_json_body() -> None:
    load_example_module("guides/local_run_and_direct_invoke")
    from app.functions.greet import greet  # noqa: PLC0415

    for body in NON_OBJECT_BODIES:
        response = greet(_request(body))
        assert response.status_code == 400


def test_all_six_handlers_accept_their_documented_object_shape() -> None:
    # Positive controls: valid object requests must keep working after the
    # shape-validation fix.
    outbox_module = load_example_module("reliability/outbox_pattern")
    outbox_handler = _get_handler(outbox_module, "create_order")
    with patch.object(outbox_module, "_store_order_and_outbox") as store:
        response = outbox_handler(
            req=_request(json.dumps({"id": "order-1", "customer_id": "one", "amount": 2}).encode())
        )
        assert response.status_code == 202
        store.assert_called_once()

    load_example_module("runtime-and-ops/blueprint_modular_app")
    from app.functions.users import create_user_route  # noqa: PLC0415

    response = create_user_route(_request(json.dumps({"id": "three", "name": "New"}).encode()))
    assert response.status_code == 201

    load_example_module("runtime-and-ops/output_binding_vs_sdk")
    from app.functions.binding_route import enqueue_via_binding  # noqa: PLC0415
    from app.functions.sdk_route import enqueue_via_sdk  # noqa: PLC0415

    binding_output = _QueueOutput()
    response = enqueue_via_binding(
        req=_request(json.dumps({"task": "demo"}).encode()), output_message=binding_output
    )
    assert response.status_code == 200

    import os  # noqa: PLC0415

    with patch.dict(os.environ, {"StorageConnection": ""}):
        response = enqueue_via_sdk(req=_request(json.dumps({"task": "demo"}).encode()))
        assert response.status_code == 500

    load_example_module("messaging-and-pubsub/queue_producer")
    from app.functions.enqueue import enqueue_task  # noqa: PLC0415

    queue_output = _QueueOutput()
    response = enqueue_task(
        req=_request(json.dumps({"task_type": "demo"}).encode()), msg=queue_output
    )
    assert response.status_code == 202

    load_example_module("guides/local_run_and_direct_invoke")
    from app.functions.greet import greet  # noqa: PLC0415

    response = greet(_request(json.dumps({"name": "Reader"}).encode()))
    assert response.status_code == 200


def test_existing_safe_parser_control_still_returns_400_for_array() -> None:
    load_example_module("apis-and-ingress/http_routing_query_body")
    from app.functions.users import create_user_http  # noqa: PLC0415

    response = create_user_http(_request(b"[]"))
    assert response.status_code == 400
