from dataclasses import dataclass
from typing import Literal

from app.__about__ import __version__ as current_version
from app.config.base import get_settings

__all__ = ("SystemHealth",)

settings = get_settings()


@dataclass
class SystemHealth:
    database_status: Literal["online", "offline"]
    cache_status: Literal["online", "offline"]
    app: str = settings.app.NAME
    version: str = current_version
