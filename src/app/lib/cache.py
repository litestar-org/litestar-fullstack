from __future__ import annotations

from typing import TYPE_CHECKING

from redis.asyncio import Redis
from starlite.cache.config import CacheConfig, default_cache_key_builder
from starlite.storage.redis import RedisStorage

from app.lib import settings

if TYPE_CHECKING:
    from starlite.connection import Request


redis = Redis.from_url(
    settings.redis.URL,
    encoding="utf-8",
    socket_connect_timeout=2,
    # socket_timeout= 1,
    socket_keepalive=5,
    health_check_interval=5,
)
"""
Async [`Redis`][redis.Redis] instance, configure via
[CacheSettings][dma.lib.config.CacheSettings].
"""


async def on_shutdown() -> None:
    """On Shutdown."""
    await redis.close()


def cache_key_builder(request: Request) -> str:
    """App name prefixed cache key builder.

    Parameters
    ----------
    request : Request
        Current request instance.

    Returns
    -------
    str
        App slug prefixed cache key.
    """
    return f"{settings.app.slug}:{default_cache_key_builder(request)}"


config = CacheConfig(
    backend=RedisStorage(redis, namespace=settings.app.slug),
    expiration=settings.api.CACHE_EXPIRATION,
    cache_key_builder=cache_key_builder,
)
"""Cache configuration for application."""
