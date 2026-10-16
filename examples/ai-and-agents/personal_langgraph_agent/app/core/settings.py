from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never


class ModelMode(StrEnum):
    FAKE = "fake"
    AZURE_OPENAI = "azure_openai"


class MemoryMode(StrEnum):
    MEMORY = "memory"
    BLOB = "blob"


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
    memory_mode: MemoryMode
    model_timeout_seconds: float
    tool_timeout_seconds: float
    storage_connection_string: str | None
    blob_container: str
    auto_create_storage: bool

    def require_storage_connection_string(self) -> str:
        if self.storage_connection_string is None:
            raise RuntimeError("Missing Blob memory setting: AZURE_STORAGE_CONNECTION_STRING")
        return self.storage_connection_string


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> AgentSettings:
    model_mode = ModelMode(os.environ.get("AGENT_MODEL_MODE", "fake"))
    memory_mode = MemoryMode(os.environ.get("AGENT_MEMORY_MODE", "memory"))
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING") or None
    if memory_mode is MemoryMode.BLOB and connection_string is None:
        raise RuntimeError("Missing Blob memory setting: AZURE_STORAGE_CONNECTION_STRING")
    return AgentSettings(
        model_mode=model_mode,
        memory_mode=memory_mode,
        model_timeout_seconds=float(os.getenv("AGENT_MODEL_TIMEOUT_SECONDS", "30")),
        tool_timeout_seconds=float(os.getenv("AGENT_TOOL_TIMEOUT_SECONDS", "5")),
        storage_connection_string=connection_string,
        blob_container=os.getenv("LANGGRAPH_BLOB_CONTAINER", "personal-agent-checkpoints"),
        auto_create_storage=_enabled("LANGGRAPH_AUTO_CREATE_STORAGE"),
    )


def load_azure_openai_settings(mode: ModelMode) -> AzureOpenAISettings | None:
    match mode:
        case ModelMode.FAKE:
            return None
        case ModelMode.AZURE_OPENAI:
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
        case unreachable:
            assert_never(unreachable)
