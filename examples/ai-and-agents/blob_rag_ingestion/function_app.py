"""Event-driven RAG ingestion: Blob upload -> chunk -> embed -> Azure AI Search index."""

from __future__ import annotations

import azure.functions as func

from app.functions.ingest import rag_ingestion_blueprint

app = func.FunctionApp()
app.register_functions(rag_ingestion_blueprint)
