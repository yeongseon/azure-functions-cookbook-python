from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_endpoint: str
    embedding_deployment: str
    search_endpoint: str
    search_index: str

    @classmethod
    def from_env(cls) -> Settings:
        missing = [
            name for name in ("AZURE_OPENAI_ENDPOINT", "AI_SEARCH_ENDPOINT") if not os.getenv(name)
        ]
        if missing:
            raise RuntimeError(f"missing required app settings: {', '.join(missing)}")
        return cls(
            openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/"),
            embedding_deployment=os.getenv(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
            ),
            search_endpoint=os.environ["AI_SEARCH_ENDPOINT"],
            search_index=os.getenv("AI_SEARCH_INDEX", "knowledge-index"),
        )
