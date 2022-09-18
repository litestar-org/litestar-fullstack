from pyspa.config import settings
from pyspa.schemas.base import CamelizedBaseSchema


class SystemHealth(CamelizedBaseSchema):
    """
    Health check response schema.
    """

    app: str
    version: str
    database_status: str
    cache_status: str

    class Config:
        """
        Schema configuration.
        """

        schema_extra = {
            "app": settings.app.NAME,
            "version": settings.app.BUILD_NUMBER,
        }
