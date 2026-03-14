from __future__ import annotations

import logging


def configure_logging() -> None:
    """Configure structured logging for the function app."""
    logging.basicConfig(level=logging.INFO)
