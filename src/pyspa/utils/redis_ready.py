import asyncio
import sys

from redis.asyncio import Redis

from app.config import cache_settings


async def c() -> None:
    """
    Checks for cache connectivity.
    """
    redis = Redis.from_url(cache_settings.URL)
    try:
        await redis.ping()
    except Exception as e:  # pylint: disable=broad-except
        print(f"Waiting  for Redis: {e}")  # noqa: T201
        sys.exit(-1)
    else:
        print("Redis OK!")  # noqa: T201
    finally:
        await redis.close()


def main() -> None:
    """Entrypoint"""
    asyncio.run(c())
