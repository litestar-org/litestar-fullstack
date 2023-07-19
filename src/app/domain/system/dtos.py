from dataclasses import dataclass
from typing import Literal

from litestar.dto import DataclassDTO

from app.lib import dto, settings

__all__ = ["SystemHealth", "SystemHealthDTO"]


@dataclass
class SystemHealth:
    database_status: Literal["online", "offline"]
    cache_status: Literal["online", "offline"]
    worker_status: Literal["online", "offline"]
    app: str = settings.app.NAME
    version: str = settings.app.BUILD_NUMBER


class SystemHealthDTO(DataclassDTO[SystemHealth]):
    """Team Create."""

    config = dto.config()
