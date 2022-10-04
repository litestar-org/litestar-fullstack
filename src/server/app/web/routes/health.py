import logging
from typing import cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlite import MediaType, Response, get

from app import schemas
from app.config import settings
from app.config.paths import urls
from app.core.cache import RedisAsyncioBackend
from app.core.cache import config as cache_config
from app.version import __version__

logger = logging.getLogger()


@get(path=urls.HEALTH, media_type=MediaType.JSON, cache=False, tags=["Server"])
async def health_check(db_session: AsyncSession) -> Response[schemas.SystemHealth]:
    """Health check handler"""
    logger.info("Checking Server Health")
    try:
        await db_session.execute(text("select count(1) from ddl_version"))
        db_ping = True
    except ConnectionRefusedError:
        db_ping = False
        logger.error("Failed to connect to database")
    db_status = "online" if db_ping else "offline"
    cache = cache_config.backend
    cache_ping = await cast("RedisAsyncioBackend", cache).ping() if cache else False
    cache_status = "online" if cache_ping else "offline"
    return Response(
        content=schemas.SystemHealth.parse_obj(
            {
                "app": settings.app.NAME,
                "version": __version__,
                "database_status": db_status,
                "cache_status": cache_status,
            }
        ),
        status_code=200 if cache_status and db_status else 500,
        media_type=MediaType.JSON,
    )
