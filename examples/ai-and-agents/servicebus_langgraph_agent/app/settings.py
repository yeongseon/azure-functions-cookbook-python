from __future__ import annotations

import math
import os
from dataclasses import dataclass
from enum import StrEnum


class ModelMode(StrEnum):
    FAKE = "fake"
    AZURE_OPENAI = "azure_openai"


@dataclass(frozen=True, slots=True)
class AzureOpenAISettings:
    endpoint: str
    deployment: str
    api_version: str
    api_key: str | None
    use_entra_id: bool


@dataclass(frozen=True, slots=True)
class AgentSettings:
    model_mode: ModelMode
    model_timeout_seconds: float
    queue_name: str
    sessions: bool
    lock_timeout_seconds: float


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _finite_seconds(name: str, default: str) -> float:
    value = float(os.getenv(name, default))
    if not math.isfinite(value) or value < 0:
        raise RuntimeError(f"{name} must be a finite, non-negative number of seconds")
    return value


def load_settings() -> AgentSettings:
    """Read the app settings. Unknown model modes fail loudly instead of falling back."""
    return AgentSettings(
        model_mode=ModelMode(os.environ.get("AGENT_MODEL_MODE", "fake")),
        model_timeout_seconds=_finite_seconds("AGENT_MODEL_TIMEOUT_SECONDS", "30"),
        queue_name=os.environ.get("SERVICEBUS_QUEUE_NAME", "agent-requests"),
        sessions=_enabled("SERVICEBUS_SESSIONS"),
        lock_timeout_seconds=_finite_seconds("SERVICEBUS_LOCK_TIMEOUT_SECONDS", "5"),
    )


def load_azure_openai_settings() -> AzureOpenAISettings:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or None
    use_entra_id = _enabled("AZURE_OPENAI_USE_ENTRA_ID")
    missing = [
        name
        for name, present in (
            ("AZURE_OPENAI_ENDPOINT", bool(endpoint)),
            ("AZURE_OPENAI_DEPLOYMENT", bool(deployment)),
        )
        if not present
    ]
    if api_key is None and not use_entra_id:
        missing.append("AZURE_OPENAI_API_KEY or AZURE_OPENAI_USE_ENTRA_ID")
    if missing:
        raise RuntimeError(f"Missing Azure OpenAI settings: {', '.join(missing)}")
    return AzureOpenAISettings(
        endpoint=endpoint,
        deployment=deployment,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        api_key=api_key,
        use_entra_id=use_entra_id,
    )
