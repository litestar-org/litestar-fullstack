from typing import Literal

from app.lib import settings
from app.lib.schema import CamelizedBaseModel

__all__ = ["SystemHealth"]


class SystemHealth(CamelizedBaseModel):
    """Health check response schema."""

    app: str = settings.app.NAME
    version: str = settings.app.BUILD_NUMBER
    database_status: Literal["online", "offline"]
    cache_status: Literal["online", "offline"]
    worker_status: Literal["online", "offline"]

    class Config:
        """Schema configuration."""

        schema_extra = {
            "app": settings.app.NAME,
            "version": settings.app.BUILD_NUMBER,
        }
