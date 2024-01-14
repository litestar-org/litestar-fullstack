from __future__ import annotations

from . import constants
from .base import BASE_DIR, DEFAULT_MODULE_NAME, Settings

__all__ = (
    "settings",
    "constants",
    "DEFAULT_MODULE_NAME",
    "BASE_DIR",
)

settings = Settings.from_env()
