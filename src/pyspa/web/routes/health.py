import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlite import MediaType, get

from pyspa import schemas
from pyspa.config import settings
from pyspa.config.paths import urls
from pyspa.version import __version__

logger = logging.getLogger()


@get(path=urls.HEALTH, media_type=MediaType.JSON, cache=False, tags=["Server"])
async def health_check(db: AsyncSession) -> schemas.SystemHealth:
    """Health check handler"""
    logger.info("Checking Server Health")
    try:
        await db.execute(text("select count(1) from ddl_version"))
        db_status = "online"
    except ConnectionRefusedError:
        db_status = "offline"
        logger.error("Failed to connect to database")
    return schemas.SystemHealth.parse_obj(
        {"app": settings.app.NAME, "version": __version__, "status": "ok", "database_status": db_status}
    )
