from typing import Literal

from app.__metadata__ import __version__
from app.lib.settings import get_settings
from app.schemas.base import CamelizedBaseStruct

__all__ = ("SystemHealth",)

settings = get_settings()


class SystemHealth(CamelizedBaseStruct):
    database_status: Literal["online", "offline"] = "offline"
    app: str = settings.app.NAME
    version: str = __version__
