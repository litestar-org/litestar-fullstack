from __future__ import annotations

import asyncio
import atexit
import platform
import threading
from multiprocessing.util import _exit_function  # type: ignore[attr-defined]
from typing import TYPE_CHECKING, Any

if platform.system() != "Windows":
    import uvloop

from app.lib import settings

from .base import Queue, Worker

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection

    import saq
    from saq.types import Context

__all__ = ["create_worker_instance", "run_worker"]


def create_worker_instance(
    queue: Queue,
    tasks: Collection[Callable[..., Any] | tuple[str, Callable]],
    scheduled_tasks: Collection[saq.CronJob] | None = None,
    startup: Callable[[Context], Awaitable[Any]] | None = None,
    shutdown: Callable[[Context], Awaitable[Any]] | None = None,
    before_process: Callable[[Context], Awaitable[Any]] | None = None,
    after_process: Callable[[Context], Awaitable[Any]] | None = None,
    concurrency: int | None = None,
) -> Worker:
    """Create worker instance.

    Args:
        queue: Queue: The queue instance to use for the worker
        tasks: Collection[Callable[..., Any] | tuple[str, Callable]]: Functions to be called via the async workers
        scheduled_tasks (Collection[saq.CronJob] | None, optional): Scheduled functions to be called via the async workers. Defaults to None.
        startup (Callable[[dict[str, Any]], Awaitable[Any]] | None, optional): Async function called on startup. Defaults to None.
        shutdown (Callable[[dict[str, Any]], Awaitable[Any]] | None, optional): Async functions called on startup. Defaults to None.
        before_process (Callable[[dict[str, Any]], Awaitable[Any]] | None, optional): Async function called before a job processes.. Defaults to None.
        after_process (Callable[[dict[str, Any]], Awaitable[Any]] | None, optional): _Async function called after a job processes. Defaults to None.
        concurrency (int | None, optional): _description_. Defaults to None.

    Returns:
        Worker: The worker instance
    """
    if concurrency is None:
        concurrency = settings.worker.CONCURRENCY
    return Worker(
        queue,
        functions=tasks,
        cron_jobs=scheduled_tasks,
        startup=startup,
        shutdown=shutdown,
        before_process=before_process,
        after_process=after_process,
        concurrency=concurrency,
    )


def run_worker() -> None:
    """Run a worker."""
    from app.domain import scheduled_tasks, tasks
    from app.lib import log
    from app.lib.log.worker import after_process as after_logging_process
    from app.lib.log.worker import before_process as before_logging_process
    from app.lib.log.worker import on_shutdown as shutdown_logging_process
    from app.lib.log.worker import on_startup as startup_logging_process
    from app.lib.worker import queues

    if threading.current_thread() is not threading.main_thread():
        atexit.unregister(_exit_function)
    logger = log.get_logger()
    logger.info("Starting working pool")
    loop = _create_event_loop()
    worker_instances: list[Worker] = [
        create_worker_instance(
            queue=queue,
            tasks=tasks.get(queue, []),
            scheduled_tasks=scheduled_tasks.get(queue, []),
            startup=startup_logging_process,  # type: ignore[arg-type]
            shutdown=shutdown_logging_process,  # type: ignore[arg-type]
            after_process=after_logging_process,  # type: ignore[arg-type]
            before_process=before_logging_process,  # type: ignore[arg-type]
        )
        for queue in queues.values()
    ]
    try:
        for i, worker_instance in enumerate(worker_instances):
            if i < len(worker_instances) - 1:
                loop.create_task(worker_instance.start())
            else:
                loop.run_until_complete(worker_instance.start())
    except KeyboardInterrupt:
        for worker_instance in worker_instances:
            loop.run_until_complete(worker_instance.stop())


def _create_event_loop() -> asyncio.AbstractEventLoop:
    if platform.system() != "Windows":
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    return asyncio.new_event_loop()
