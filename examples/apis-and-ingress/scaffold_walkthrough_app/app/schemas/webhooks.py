from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    event_type: str = Field(..., description="Type of the event, e.g. 'order.completed'.")
    source: str = Field(..., description="Origin system, e.g. 'shopify'.")
    occurred_at: str = Field(..., description="ISO-8601 timestamp of when the event occurred.")
    data: dict[str, Any] = Field(default_factory=dict, description="Arbitrary event payload.")


class WebhookAcceptedResponse(BaseModel):
    delivery_id: str = Field(..., description="Unique delivery identifier.")
    status: str = Field(default="accepted", description="Processing status.")
    received_at: str = Field(
        ..., description="ISO-8601 timestamp of when the webhook was received."
    )
