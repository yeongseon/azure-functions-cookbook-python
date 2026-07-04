from __future__ import annotations

import os


def get_setting(key: str, default: str = "") -> str:
    """Read an application setting from environment variables."""
    return os.environ.get(key, default)


# Common settings
APP_NAME: str = get_setting("APP_NAME", "scaffold_walkthrough_app")
DEBUG: bool = get_setting("DEBUG", "false").lower() in ("true", "1", "yes")
