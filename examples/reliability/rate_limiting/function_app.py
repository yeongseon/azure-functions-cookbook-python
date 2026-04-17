from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportAny=false, reportUnknownArgumentType=false, reportUntypedBaseClass=false

import math
import os
import threading
import time

import azure.functions as func
from azure_functions_logging import get_logger, setup_logging
from azure_functions_openapi import openapi
from azure_functions_validation import validate_http
from pydantic import BaseModel, Field

setup_logging(format="json")
logger = get_logger(__name__)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _load_float(name: str, default: float, minimum: float) -> float:
    raw_value = os.getenv(name, str(default))
    try:
        return max(minimum, float(raw_value))
    except ValueError:
        logger.warning(
            "Invalid float setting; using default.",
            extra={"setting": name, "value": raw_value, "default": default},
        )
        return default


class ThrottleQuery(BaseModel):
    client_id: str = Field(default="anonymous", min_length=1, max_length=100)


class RateLimitResponse(BaseModel):
    message: str
    client_id: str
    allowed: bool
    limit: float
    refill_rate_per_second: float
    remaining_tokens: float
    retry_after_seconds: float


class BucketSnapshot(BaseModel):
    allowed: bool
    remaining_tokens: float
    retry_after_seconds: float


class InMemoryTokenBucket:
    def __init__(self, capacity: float, refill_rate_per_second: float) -> None:
        self.capacity: float = capacity
        self.refill_rate_per_second: float = refill_rate_per_second
        self._tokens: float = capacity
        self._last_refill: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def try_consume(self, cost: float = 1.0) -> BucketSnapshot:
        now = time.monotonic()
        with self._lock:
            elapsed = max(0.0, now - self._last_refill)
            replenished = elapsed * self.refill_rate_per_second
            self._tokens = min(self.capacity, self._tokens + replenished)
            self._last_refill = now

            if self._tokens >= cost:
                self._tokens -= cost
                return BucketSnapshot(
                    allowed=True,
                    remaining_tokens=round(self._tokens, 2),
                    retry_after_seconds=0.0,
                )

            missing_tokens = max(0.0, cost - self._tokens)
            retry_after_seconds = missing_tokens / self.refill_rate_per_second
            return BucketSnapshot(
                allowed=False,
                remaining_tokens=round(self._tokens, 2),
                retry_after_seconds=round(retry_after_seconds, 2),
            )


RATE_LIMIT_CAPACITY = _load_float("RATE_LIMIT_CAPACITY", default=5.0, minimum=1.0)
RATE_LIMIT_REFILL_PER_SECOND = _load_float(
    "RATE_LIMIT_REFILL_PER_SECOND",
    default=1.0,
    minimum=0.1,
)

_bucket = InMemoryTokenBucket(
    capacity=RATE_LIMIT_CAPACITY,
    refill_rate_per_second=RATE_LIMIT_REFILL_PER_SECOND,
)


def _json_response(payload: RateLimitResponse, status_code: int) -> func.HttpResponse:
    retry_after = str(max(0, math.ceil(payload.retry_after_seconds)))
    return func.HttpResponse(
        body=payload.model_dump_json(),
        status_code=status_code,
        mimetype="application/json",
        headers={
            "Retry-After": retry_after,
            "X-RateLimit-Limit": str(payload.limit),
            "X-RateLimit-Remaining": str(payload.remaining_tokens),
        },
    )


@app.route(route="rate-limit", methods=["GET"])
@openapi(
    summary="Throttle requests with an in-memory token bucket",
    description="Demonstrates function-level rate limiting that returns 429 when the bucket is empty.",
    response={200: RateLimitResponse, 429: RateLimitResponse},
    tags=["reliability"],
)
@validate_http(query=ThrottleQuery, response_model=RateLimitResponse)
def rate_limit(req: func.HttpRequest, query: ThrottleQuery) -> func.HttpResponse:
    snapshot = _bucket.try_consume(cost=1.0)
    payload = RateLimitResponse(
        message="Request accepted." if snapshot.allowed else "Rate limit exceeded.",
        client_id=query.client_id,
        allowed=snapshot.allowed,
        limit=RATE_LIMIT_CAPACITY,
        refill_rate_per_second=RATE_LIMIT_REFILL_PER_SECOND,
        remaining_tokens=snapshot.remaining_tokens,
        retry_after_seconds=snapshot.retry_after_seconds,
    )

    if snapshot.allowed:
        logger.info(
            "Accepted request through token bucket.",
            extra={
                "client_id": query.client_id,
                "remaining_tokens": snapshot.remaining_tokens,
                "rate_limit_capacity": RATE_LIMIT_CAPACITY,
                "request_url": req.url,
            },
        )
        return _json_response(payload, status_code=200)

    logger.warning(
        "Rejected request because token bucket is empty.",
        extra={
            "client_id": query.client_id,
            "remaining_tokens": snapshot.remaining_tokens,
            "retry_after_seconds": snapshot.retry_after_seconds,
            "request_url": req.url,
        },
    )
    return _json_response(payload, status_code=429)
