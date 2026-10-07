from __future__ import annotations

from azure_functions_logging import JsonFormatter, get_logger, setup_logging


def configure_logging() -> None:
    """Configure structured logging for the Azure Functions application."""
    setup_logging(functions_formatter=JsonFormatter(), use_record_factory=True)


logger = get_logger("scaffold_walkthrough_app")
