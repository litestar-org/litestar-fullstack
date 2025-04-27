"""Log config and utils for the worker instance."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from saq import Status
from saq.utils import seconds

if TYPE_CHECKING:
    from saq import Job
    from saq.types import Context

LOGGED_JOB_FIELDS = [
    "function",
    "kwargs",
    "key",
    "scheduled",
    "attempts",
    "completed",
    "queued",
    "started",
    "result",
    "error",
]

logger = structlog.get_logger()


async def on_shutdown(ctx: Context) -> None:
    """Shutdown events for each worker.."""
    worker = ctx["worker"]
    await logger.ainfo("Stopping background workers for queue", queue=worker.queue.name)


async def on_startup(ctx: Context) -> None:
    """Startup events for each worker."""
    worker = ctx["worker"]
    await logger.ainfo("🚀 Launching background workers for queue", queue=worker.queue.name)


async def before_process(ctx: Context) -> None:
    """Clear the structlog contextvars for this task."""
    structlog.contextvars.clear_contextvars()
    job: Job | None = ctx.get("job", None)
    if job:
        await logger.ainfo(f"starting job {job.function} with id {job.id}", task=job.function)


async def after_process(ctx: Context) -> None:
    """Parse log context and log it along with the contextvars context."""
    # parse log context from `ctx`
    job: Job | None = ctx.get("job", None)
    if job:
        log_ctx = {k: getattr(job, k) for k in LOGGED_JOB_FIELDS}
        # add duration measures
        log_ctx["pickup_time_ms"] = job.started - job.queued
        log_ctx["completed_time_ms"] = job.completed - job.started
        log_ctx["total_time_ms"] = job.completed - job.queued
        total_time_seconds = seconds(log_ctx["total_time_ms"])
        if job.status == Status.FAILED:
            msg = f"job {job.function} with id '{job.id}' failed after {total_time_seconds} seconds."
            await logger.aerror(msg, **log_ctx)
        elif job.status == Status.COMPLETE:
            msg = f"job {job.function} with id '{job.id}' completed after {total_time_seconds} seconds."
            await logger.ainfo(msg, **log_ctx)
        elif job.status == Status.ABORTED:
            msg = f"job {job.function} with id '{job.id}' was aborted after {total_time_seconds} seconds"
            await logger.awarning(msg, **log_ctx)
        else:
            msg = f"job {job.function} with id '{job.id}' {job.status} after {total_time_seconds} seconds."
            await logger.ainfo(msg, **log_ctx)
    structlog.contextvars.clear_contextvars()
