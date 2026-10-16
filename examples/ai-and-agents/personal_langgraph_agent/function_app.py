from __future__ import annotations

from typing import Any

import azure.functions as func
from azure_functions_langgraph import LangGraphApp, LoggingRunObserver
from langgraph.checkpoint.memory import InMemorySaver

from app.core.model import build_model
from app.core.settings import MemoryMode, load_settings
from app.services.graph import build_graph
from app.services.notes import SampleNoteLookup, build_note_tool

settings = load_settings()
tools = [build_note_tool(SampleNoteLookup())]
model = build_model(settings, tools)
checkpointer: Any

match settings.memory_mode:
    case MemoryMode.MEMORY:
        checkpointer = InMemorySaver()
        thread_lock = None
    case MemoryMode.BLOB:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import ContainerClient
        from azure_functions_langgraph.checkpointers.azure_blob import AzureBlobCheckpointSaver
        from azure_functions_langgraph.locks import AzureBlobLeaseThreadLock

        container: Any = ContainerClient.from_connection_string(
            settings.require_storage_connection_string(), settings.blob_container
        )
        if settings.auto_create_storage:
            try:
                container.create_container()
            except ResourceExistsError:
                pass
        checkpointer = AzureBlobCheckpointSaver(container_client=container)
        thread_lock = AzureBlobLeaseThreadLock(container_client=container)

graph = build_graph(settings, model, tools, checkpointer)
adapter = LangGraphApp(
    auth_level=func.AuthLevel.FUNCTION,
    observer=LoggingRunObserver(),
    thread_lock=thread_lock,
)
adapter.register(
    graph=graph,
    name="personal_agent",
    description="Tool-calling personal notes assistant with per-thread memory.",
    stream=False,
)
app = adapter.function_app
