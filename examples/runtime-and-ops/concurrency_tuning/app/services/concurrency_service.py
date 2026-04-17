"""Service layer for concurrency tuning demonstration."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def process_concurrent_message(body: str) -> bool:
    """Process a queue message under dynamic concurrency settings.

    Args:
        body: Decoded message body.

    Returns:
        True if processing succeeded.
    """
    logger.info("Processing queue item with dynamic concurrency enabled: %s", body)
    return True
