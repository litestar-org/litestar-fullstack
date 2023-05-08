from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, MediaType, get, post
from litestar.di import Provide

from . import dependencies, urls

if TYPE_CHECKING:
    from uuid import UUID

    from saq.types import QueueInfo

    from .base import Job, Queue

__all__ = ["WorkerController"]


class WorkerController(Controller):
    tags = ["Worker"]
    dependencies = {
        "queue": Provide(dependencies.provide_queue),
        "job": Provide(dependencies.provide_job),
    }

    @get(
        operation_id="WorkerQueueList",
        name="worker:queue-list",
        path=urls.WORKER_QUEUE_LIST,
        media_type=MediaType.JSON,
        cache=False,
        summary="Queue List",
        description="List configured worker queues.",
    )
    async def queue_list(self, queue: Queue) -> QueueInfo:
        """Get Worker queues."""
        return await queue.info()

    @get(
        operation_id="WorkerQueueDetail",
        name="worker:queue-detail",
        path=urls.WORKER_QUEUE_DETAIL,
        media_type=MediaType.JSON,
        cache=False,
        summary="Queue Detail",
        description="List queue details.",
    )
    async def queue_detail(self, queue: Queue, queue_id: UUID) -> QueueInfo:
        """Get queue information."""
        return await queue.info()

    @get(
        operation_id="WorkerJobDetail",
        name="worker:job-detail",
        path=urls.WORKER_JOB_DETAIL,
        media_type=MediaType.JSON,
        cache=False,
        summary="Job Details",
        description="List job details.",
    )
    async def job_detail(self, queue: Queue, job: Job, queue_id: UUID, job_id: UUID) -> dict:
        """Get job information."""
        job_dict = job.to_dict()
        if "kwargs" in job_dict:
            job_dict["kwargs"] = repr(job_dict["kwargs"])
        if "result" in job_dict:
            job_dict["result"] = repr(job_dict["result"])
        return {"job": job_dict}

    @post(
        operation_id="WorkerJobRetry",
        name="worker:job-retry",
        path=urls.WORKER_JOB_DETAIL,
        media_type=MediaType.JSON,
        cache=False,
        summary="Job Retry",
        description="Retry a failed job..",
    )
    async def job_retry(self, queue: Queue, job: Job, queue_id: UUID, job_id: UUID) -> dict:
        """Retry job."""
        await job.retry("retried from ui")
        return {}

    @post(
        operation_id="WorkerJobAbort",
        name="worker:job-abort",
        path=urls.WORKER_JOB_ABORT,
        media_type=MediaType.JSON,
        cache=False,
        summary="Job Abort",
        description="Abort active job.",
    )
    async def job_abort(self, queue: Queue, job: Job, queue_id: UUID, job_id: UUID) -> dict:
        """Abort job."""
        await job.abort("aborted from ui")
        return {}

    # static site
    @get(
        [urls.WORKER_ROOT, urls.WORKER_QUEUE_ROOT, urls.WORKER_JOB_ROOT],
        operation_id="WorkerIndex",
        name="worker:index",
        media_type=MediaType.HTML,
        cache=False,
        include_in_schema=False,
    )
    async def index(self) -> str:
        """Serve site root."""
        return SITE_BODY


SITE_BODY = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="/static/pico.min.css.gz">
        <title>SAQ</title>
    </head>
    <body>
        <div id="app"></div>
        <script src="/static/snabbdom.js.gz"></script>
        <script src="/static/app.js"></script>
    </body>
</html>
""".strip()
