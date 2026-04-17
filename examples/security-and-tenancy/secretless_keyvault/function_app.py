from __future__ import annotations

import importlib
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar, cast

F = TypeVar("F", bound=Callable[..., object])


class HttpRequestProtocol(Protocol):
    method: str


class HttpResponseProtocol(Protocol): ...


class AuthLevelProtocol:
    FUNCTION: str = "function"


class FunctionAppProtocol(Protocol):
    def function_name(self, *, name: str) -> Callable[[F], F]: ...

    def route(self, *, route: str, methods: list[str]) -> Callable[[F], F]: ...


class FuncModuleProtocol(Protocol):
    AuthLevel: type[AuthLevelProtocol]
    HttpRequest: type[HttpRequestProtocol]
    HttpResponse: type[HttpResponseProtocol]

    def FunctionApp(self, *, http_auth_level: object) -> FunctionAppProtocol: ...


def _passthrough(function: F) -> F:
    return function


def _fallback_setup_logging(*, format: str = "json") -> None:
    _ = format
    logging.basicConfig(level=logging.INFO)


def _fallback_get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


@dataclass
class _FallbackHttpRequest:
    method: str = "GET"


class _FallbackHttpResponse:
    def __init__(
        self,
        body: str,
        *,
        status_code: int = 200,
        mimetype: str = "text/plain",
    ) -> None:
        self.body: str = body
        self.status_code: int = status_code
        self.mimetype: str = mimetype


class _FallbackFunctionApp:
    def function_name(self, *, name: str) -> Callable[[F], F]:
        _ = name
        return _passthrough

    def route(self, *, route: str, methods: list[str]) -> Callable[[F], F]:
        _ = (route, methods)
        return _passthrough


class _FallbackFuncModule:
    AuthLevel: type[AuthLevelProtocol] = AuthLevelProtocol
    HttpRequest: type[_FallbackHttpRequest] = _FallbackHttpRequest
    HttpResponse: type[_FallbackHttpResponse] = _FallbackHttpResponse

    def FunctionApp(self, *, http_auth_level: object) -> FunctionAppProtocol:
        _ = http_auth_level
        return _FallbackFunctionApp()


try:
    func = cast(FuncModuleProtocol, cast(object, importlib.import_module("azure.functions")))
except ImportError:
    func = _FallbackFuncModule()


try:
    logging_toolkit = importlib.import_module("azure_functions_logging")
    get_logger = cast(Callable[[str], logging.Logger], getattr(logging_toolkit, "get_logger"))
    setup_logging = cast(Callable[..., None], getattr(logging_toolkit, "setup_logging"))
except ImportError:
    get_logger = _fallback_get_logger
    setup_logging = _fallback_setup_logging


setup_logging(format="json")
logger = get_logger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name(name="secretless_keyvault")
@app.route(route="secretless-keyvault", methods=["GET"])
def secretless_keyvault(req: HttpRequestProtocol) -> HttpResponseProtocol:
    upstream_api_key = os.getenv("UPSTREAM_API_KEY", "")
    secret_name = os.getenv("UPSTREAM_SECRET_NAME", "demo-api-key")
    app_name = os.getenv("UPSTREAM_APP_NAME", "sample-upstream")

    secret_loaded = bool(upstream_api_key)
    logger.info(
        "Resolved Key Vault-backed app setting",
        extra={
            "method": req.method,
            "app_name": app_name,
            "secret_name": secret_name,
            "secret_loaded": secret_loaded,
            "source": "environment-variable",
        },
    )

    response_factory = cast(Callable[..., HttpResponseProtocol], getattr(func, "HttpResponse"))
    return response_factory(
        json.dumps(
            {
                "app": app_name,
                "secretName": secret_name,
                "secretLoaded": secret_loaded,
                "source": "environment-variable",
                "usesSdk": False,
            }
        ),
        mimetype="application/json",
        status_code=200,
    )
