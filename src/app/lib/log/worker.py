"""Log config and utils for the worker instance."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import structlog

from app.lib import settings

__all__ = ["after_process", "before_process", "on_shutdown", "on_startup"]


if TYPE_CHECKING:
    from typing import Any, TypeAlias

    from saq import Job

LOGGER = structlog.get_logger()

Context: TypeAlias = "dict[str, Any]"


async def on_shutdown(_: Context) -> None:
    """Shutdown events for each worker.."""
    await LOGGER.ainfo("Worker is shutting down.")


async def on_startup(_: Context) -> None:
    """Startup events for each worker."""
    await LOGGER.ainfo("Worker is starting up.")


async def before_process(_: Context) -> None:
    """Clear the structlog contextvars for this task."""
    structlog.contextvars.clear_contextvars()


async def after_process(ctx: Context) -> None:
    """Parse log context and log it along with the contextvars context."""
    # parse log context from `ctx`
    job: Job = ctx["job"]
    log_ctx = {k: getattr(job, k) for k in settings.log.JOB_FIELDS}
    # add duration measures
    log_ctx["pickup_time_ms"] = job.started - job.queued
    log_ctx["completed_time_ms"] = job.completed - job.started
    log_ctx["total_time_ms"] = job.completed - job.queued
    # emit the log
    level = logging.ERROR if job.error else logging.INFO
    await LOGGER.alog(level, settings.log.WORKER_EVENT, **log_ctx)
