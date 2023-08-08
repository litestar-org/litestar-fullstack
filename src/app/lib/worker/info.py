from __future__ import annotations

from typing import TYPE_CHECKING, cast

from app.lib import settings
from app.lib.exceptions import ApplicationError

from .base import Job, redis

__all__ = ["active_workers", "is_healthy", "job"]


if TYPE_CHECKING:
    from .base import Queue


async def active_workers() -> int:
    """Return the number of active workers connected to the queue."""
    workers = await redis.keys(f"{settings.app.slug}:*:stats:*")
    return len(workers)


async def is_healthy() -> bool:
    """Server is healthy."""
    return bool(await active_workers())


async def job(queue: Queue, job_id: str) -> Job:
    job = await queue._get_job_by_id(str(job_id))
    if not job:
        raise ApplicationError("Could not find job ID %s", job_id)
    return cast("Job", job)
