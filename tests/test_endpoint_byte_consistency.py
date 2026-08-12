"""Byte-consistency guard for the shared ``endpoint`` metadata namespace.

The Azure Functions Python DX Toolkit has two independent producers of the
``endpoint`` namespace payload (schema version 1):

* ``azure_functions_validation._endpoint.build_endpoint_metadata`` — reads a
  pipeline ``config`` (``body``/``query``/``path``/``headers``/``response_model``/
  ``success_status_code``).
* ``azure_functions_langgraph._endpoint.build_endpoint_metadata`` — takes an
  explicit ``request_model``/``response_model``/``parameters``/
  ``success_status_code``.

Neither package imports the other; they independently adopt the same
``by_alias``/``ref_template``/``mode`` canonicalization so their emitted JSON
Schema stays byte-identical. The cookbook is the dogfood integration point
where both are import-available, so this test pins that contract: for the same
request/response models, the two builders must emit byte-identical values for
the *shared* fields.

Fields compared (byte-identical, ``json.dumps(sort_keys=True)``):

* ``version``
* ``request_body`` (request model schema, ``"validation"`` mode)
* ``request_body_required``
* the success ``responses[status]["schema"]`` (response model schema,
  ``"serialization"`` mode)

Fields intentionally NOT compared: ``parameters`` (validation auto-derives them
from query/path/header models; langgraph passes them through verbatim) and the
extra ``"422"`` validation-error response (validation-only convention). Those
are producer-specific by design and are covered elsewhere.

If this test fails, one producer's canonicalization drifted from the other and
the shared ``endpoint`` contract is broken.

See yeongseon/azure-functions-python-cookbook#149.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel, Field

from azure_functions_langgraph._endpoint import (
    build_endpoint_metadata as langgraph_build,
)
from azure_functions_validation._endpoint import (
    build_endpoint_metadata as validation_build,
)


class SimpleRequest(BaseModel):
    name: str
    count: int = 0


class SimpleResponse(BaseModel):
    message: str
    status: str = "ok"


class Nested(BaseModel):
    label: str
    value: int


class NestedRequest(BaseModel):
    title: str
    nested: Nested


class NestedResponse(BaseModel):
    result: Nested
    total: int


class AliasRequest(BaseModel):
    user_name: str = Field(alias="userName")
    is_active: bool = Field(default=True, alias="isActive")


class AliasResponse(BaseModel):
    display_name: str = Field(alias="displayName")


def _validation_payload(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    success_status_code: int = 200,
) -> dict[str, Any]:
    """Run the validation builder with a minimal config stub.

    The validation builder only reads a handful of attributes off ``config``;
    a :class:`~types.SimpleNamespace` supplies exactly those. Only ``body`` is
    set (no query/path/header models) so the shared fields — not the
    validation-only ``parameters``/422 — are what differs.
    """
    config = SimpleNamespace(
        body=request_model,
        query=None,
        path=None,
        headers=None,
        response_model=response_model,
        success_status_code=success_status_code,
    )
    return dict(validation_build(config))


def _langgraph_payload(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    success_status_code: int = 200,
) -> dict[str, Any]:
    return dict(
        langgraph_build(
            request_model=request_model,
            response_model=response_model,
            parameters=None,
            success_status_code=success_status_code,
        )
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _assert_shared_fields_identical(
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    success_status_code: int = 200,
) -> None:
    v = _validation_payload(request_model, response_model, success_status_code)
    lg = _langgraph_payload(request_model, response_model, success_status_code)

    assert v["version"] == lg["version"], "endpoint schema version diverged"

    assert _canonical(v["request_body"]) == _canonical(lg["request_body"]), (
        "request_body JSON Schema diverged between validation and langgraph "
        "producers (validation-mode canonicalization drift)"
    )
    assert v["request_body_required"] == lg["request_body_required"], (
        "request_body_required diverged between producers"
    )

    status = str(success_status_code)
    v_schema = v["responses"][status]["schema"]
    lg_schema = lg["responses"][status]["schema"]
    assert _canonical(v_schema) == _canonical(lg_schema), (
        f"success response ({status}) JSON Schema diverged between validation "
        "and langgraph producers (serialization-mode canonicalization drift)"
    )


def test_simple_models_are_byte_consistent() -> None:
    _assert_shared_fields_identical(SimpleRequest, SimpleResponse)


def test_nested_models_are_byte_consistent() -> None:
    """Nested models exercise ``$defs``/``$ref`` canonicalization."""
    _assert_shared_fields_identical(NestedRequest, NestedResponse)


def test_alias_models_are_byte_consistent() -> None:
    """Field aliases exercise ``by_alias=True`` canonicalization."""
    _assert_shared_fields_identical(AliasRequest, AliasResponse)


def test_non_default_success_status_is_byte_consistent() -> None:
    """The success status keys the response identically in both producers."""
    _assert_shared_fields_identical(SimpleRequest, SimpleResponse, success_status_code=201)
