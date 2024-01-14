from dataclasses import dataclass
from typing import Literal

from litestar.dto import DataclassDTO

from app.__about__ import __version__ as current_version
from app.config import settings
from app.lib import dto

__all__ = ["SystemHealth", "SystemHealthDTO"]


@dataclass
class SystemHealth:
    database_status: Literal["online", "offline"]
    cache_status: Literal["online", "offline"]
    worker_status: Literal["online", "offline"]
    app: str = settings.app.NAME
    version: str = current_version


class SystemHealthDTO(DataclassDTO[SystemHealth]):
    """Team Create."""

    config = dto.config()
