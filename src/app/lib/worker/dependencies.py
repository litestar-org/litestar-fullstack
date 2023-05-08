from __future__ import annotations

from typing import TYPE_CHECKING

from app.lib.exceptions import ApplicationError

from .base import Job, Queue, queue

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from uuid import UUID


def provide_queue() -> Generator[Queue, None, None]:
    yield queue


async def provide_job(queue: Queue, job_id: UUID) -> AsyncGenerator[Job, None]:
    job = await queue._get_job_by_id(str(job_id))
    if not job:
        raise ApplicationError("Could not find job ID %s", job_id)
    yield job
