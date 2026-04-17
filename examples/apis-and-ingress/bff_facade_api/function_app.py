# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

import azure.functions as func
import requests
from pydantic import BaseModel, Field

try:
    from azure_functions_logging import setup_logging
except ImportError:

    def setup_logging(*args: Any, **kwargs: Any) -> None:
        _ = (args, kwargs)
        logging.basicConfig(level=logging.INFO)


try:
    from azure_functions_openapi import openapi
except ImportError:

    def openapi(*args: Any, **kwargs: Any):
        _ = (args, kwargs)

        def decorator(fn: Any) -> Any:
            return fn

        return decorator


try:
    from azure_functions_validation import validate_http
except ImportError:

    def validate_http(*args: Any, **kwargs: Any):
        _ = (args, kwargs)

        def decorator(fn: Any) -> Any:
            return fn

        return decorator


_ = setup_logging(format="json")
logger = logging.getLogger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

PROFILE_SERVICE_URL = os.getenv("PROFILE_SERVICE_URL", "https://httpbin.org/anything/profile")
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "https://httpbin.org/anything/orders")
RECOMMENDATIONS_SERVICE_URL = os.getenv("RECOMMENDATIONS_SERVICE_URL", "https://httpbin.org/uuid")
BACKEND_TIMEOUT_SECONDS = float(os.getenv("BACKEND_TIMEOUT_SECONDS", "5"))


class DashboardQuery(BaseModel):
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    include_headers: bool = Field(
        default=False,
        description="Include echoed request headers from backend responses for debugging.",
    )


class AggregatedFragment(BaseModel):
    source: str
    path: str
    customer_id: str
    args: dict[str, str]
    echoed_headers: dict[str, str] | None = None


class RecommendationFragment(BaseModel):
    source: str
    request_id: str
    customer_id: str


class DashboardResponse(BaseModel):
    customer_id: str
    profile: AggregatedFragment
    orders: AggregatedFragment
    recommendations: RecommendationFragment
    sources: list[str]


def _fetch_backend(
    url: str,
    *,
    source: str,
    customer_id: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        timeout=BACKEND_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    logger.info(
        "Fetched backend response.",
        extra={"source": source, "customer_id": customer_id, "status_code": response.status_code},
    )
    return payload


def _normalize_httpbin_fragment(
    payload: dict[str, Any], *, source: str, customer_id: str, include_headers: bool
) -> AggregatedFragment:
    headers = payload.get("headers")
    echoed_headers = (
        {str(key): str(value) for key, value in headers.items()}
        if isinstance(headers, dict)
        else None
    )
    return AggregatedFragment(
        source=source,
        path=str(payload.get("url", "")) and urlparse(str(payload.get("url", ""))).path,
        customer_id=customer_id,
        args={str(key): str(value) for key, value in dict(payload.get("args") or {}).items()},
        echoed_headers=echoed_headers if include_headers else None,
    )


def _normalize_recommendations(
    payload: dict[str, Any], *, customer_id: str
) -> RecommendationFragment:
    request_id = str(payload.get("uuid") or payload.get("origin") or "unknown")
    return RecommendationFragment(
        source="recommendations",
        request_id=request_id,
        customer_id=customer_id,
    )


def _json_response(payload: BaseModel, *, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=payload.model_dump_json(),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="dashboard", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@openapi(
    summary="Aggregate dashboard data",
    description="Calls multiple backend services and returns one frontend-shaped response.",
    response={200: DashboardResponse},
    tags=["apis-and-ingress"],
)
@validate_http(query=DashboardQuery, response_model=DashboardResponse)
def dashboard(req: func.HttpRequest, query: DashboardQuery) -> func.HttpResponse:
    profile_payload = _fetch_backend(
        PROFILE_SERVICE_URL,
        source="profile",
        customer_id=query.customer_id,
        params={"customer_id": query.customer_id},
    )
    orders_payload = _fetch_backend(
        ORDERS_SERVICE_URL,
        source="orders",
        customer_id=query.customer_id,
        params={"customer_id": query.customer_id},
    )
    recommendations_payload = _fetch_backend(
        RECOMMENDATIONS_SERVICE_URL,
        source="recommendations",
        customer_id=query.customer_id,
        params=None,
    )

    payload = DashboardResponse(
        customer_id=query.customer_id,
        profile=_normalize_httpbin_fragment(
            profile_payload,
            source="profile",
            customer_id=query.customer_id,
            include_headers=query.include_headers,
        ),
        orders=_normalize_httpbin_fragment(
            orders_payload,
            source="orders",
            customer_id=query.customer_id,
            include_headers=query.include_headers,
        ),
        recommendations=_normalize_recommendations(
            recommendations_payload,
            customer_id=query.customer_id,
        ),
        sources=["profile", "orders", "recommendations"],
    )

    logger.info(
        "Aggregated BFF dashboard response.",
        extra={
            "customer_id": query.customer_id,
            "include_headers": query.include_headers,
            "source_count": len(payload.sources),
            "request_url": req.url,
        },
    )
    return _json_response(payload)
