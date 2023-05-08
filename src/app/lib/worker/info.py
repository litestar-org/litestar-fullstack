from __future__ import annotations

from .base import queue, redis


async def active_workers() -> int:
    """Return the number of active workers connected to the queue."""
    workers = await redis.keys(f"{queue.namespace('stats')}:*")
    return len(workers)


async def is_healthy() -> bool:
    """Server is healthy."""
    return bool(await active_workers())
