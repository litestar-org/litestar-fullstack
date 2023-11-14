"""Application lifespan handlers."""
# pylint: disable=broad-except,import-outside-toplevel
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar


async def _db_ready() -> None:
    """Wait for database to become responsive."""

    from sqlalchemy import text

    from app.lib import db, log

    logger = log.get_logger()

    while True:
        try:
            async with db.config.get_engine().begin() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001
            logger.info("Waiting for DB: %s", exc)
            await asyncio.sleep(5)
        else:
            logger.info("DB OK!")
            break


async def _redis_ready() -> None:
    """Wait for redis to become responsive."""

    from app.lib import cache, log

    logger = log.get_logger()
    while True:
        try:
            await cache.redis.ping()
        except Exception as exc:  # noqa: BLE001
            logger.info("Waiting  for Redis: %s", exc)
            await asyncio.sleep(5)
        else:
            logger.info("Redis OK!")
            break


async def on_startup(_: Litestar) -> None:
    """Do things before the app starts up."""
    await _db_ready()
    await _redis_ready()


def wait_for_redis() -> None:
    """Do things before the app starts up."""
    import anyio

    anyio.run(_redis_ready)


def wait_for_postgres() -> None:
    """Do things before the app starts up."""
    import anyio

    anyio.run(_db_ready)
