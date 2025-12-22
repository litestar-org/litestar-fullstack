"""Log config and utils for the worker instance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

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
    worker = cast(Any, ctx["worker"])
    await logger.ainfo("Stopping background workers for queue", queue=worker.queue.name)


async def on_startup(ctx: Context) -> None:
    """Startup events for each worker."""
    worker = cast(Any, ctx["worker"])
    await logger.ainfo("🚀 Launching background workers for queue", queue=worker.queue.name)


async def before_process(ctx: Context) -> None:
    """Clear the structlog contextvars for this task."""
    structlog.contextvars.clear_contextvars()
    ctx_dict = cast("dict[str, Any]", ctx)
    job = cast("Job | None", ctx_dict.get("job"))
    if job:
        await logger.ainfo(f"starting job {job.function} with id {job.id}", task=job.function)


async def after_process(ctx: Context) -> None:
    """Parse log context and log it along with the contextvars context."""
    # parse log context from `ctx`
    ctx_dict = cast("dict[str, Any]", ctx)
    job = cast("Job | None", ctx_dict.get("job"))
    if job:
        log_ctx = {k: getattr(job, k) for k in LOGGED_JOB_FIELDS}
        # add duration measures
        log_ctx["pickup_time_ms"] = job.started - job.queued
        log_ctx["total_runtime_ms"] = job.completed - job.started
        log_ctx["total_time_ms"] = job.completed - job.queued
        total_runtime_ms = seconds(log_ctx["total_runtime_ms"])
        if job.status == Status.FAILED:
            msg = f"job {job.function} with id '{job.id}' failed after {total_runtime_ms} seconds."
            await logger.aerror(msg, **log_ctx)
        elif job.status == Status.COMPLETE:
            msg = f"job {job.function} with id '{job.id}' completed after {total_runtime_ms} seconds."
            await logger.ainfo(msg, **log_ctx)
        elif job.status == Status.ABORTED:
            msg = f"job {job.function} with id '{job.id}' was aborted after {total_runtime_ms} seconds"
            await logger.awarning(msg, **log_ctx)
        else:
            msg = f"job {job.function} with id '{job.id}' {job.status} after {total_runtime_ms} seconds."
            await logger.ainfo(msg, **log_ctx)
    structlog.contextvars.clear_contextvars()
