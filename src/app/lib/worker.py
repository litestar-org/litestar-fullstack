from __future__ import annotations

import asyncio
import atexit
import threading
from collections import abc
from multiprocessing.util import _exit_function  # type: ignore[attr-defined]
from typing import TYPE_CHECKING, Any

import saq
import uvloop
from redis.asyncio import Redis

from app.lib import serialization, settings

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection
    from signal import Signals

    from aiohttp.web_app import Application

__all__ = ["Queue", "Worker", "WorkerFunction", "create_worker_instance", "queue", "BackgroundTaskError", "run_worker"]


WorkerFunction = abc.Callable[..., abc.Awaitable[Any]]
Job = saq.Job


class BackgroundTaskError(Exception):
    """Base class for `Task` related exceptions."""


class Queue(saq.Queue):
    """[SAQ Queue](https://github.com/tobymao/saq/blob/master/saq/queue.py).

    Configures `msgspec` for msgpack serialization/deserialization if not otherwise configured.

    Parameters
    ----------
    *args : Any
        Passed through to `saq.Queue.__init__()`
    **kwargs : Any
        Passed through to `saq.Queue.__init__()`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize a new queue."""
        kwargs.setdefault("dump", serialization.to_msgpack)
        kwargs.setdefault("load", serialization.from_msgpack)
        kwargs.setdefault("name", "background-worker")
        super().__init__(*args, **kwargs)

    def namespace(self, key: str) -> str:
        """Make the namespace unique per app."""
        return f"{settings.app.slug}:{self.name}:{key}"

    def job_id(self, job_key: str) -> str:
        """Job ID.

        Args:
            job_key (str): Sets the job ID for the given key

        Returns:
            str: _description_
        """
        return f"{settings.app.slug}:{self.name}:job:{job_key}"


class Worker(saq.Worker):
    """Worker."""

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list[Signals] = []

    async def on_app_startup(self) -> None:
        """Attach the worker to the running event loop."""
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())


redis = Redis.from_url(
    settings.redis.URL,
    decode_responses=False,
    socket_connect_timeout=2,
    socket_keepalive=5,
    health_check_interval=5,
)

queue = Queue(redis)
"""
[Queue][app.lib.worker.Queue] instance instantiated with a Redis config
instance.
"""


def create_worker_instance(
    tasks: Collection[Callable[..., Any] | tuple[str, Callable]],
    scheduled_tasks: Collection[saq.CronJob] | None = None,
    startup: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    shutdown: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    before_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    after_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    concurrency: int | None = None,
) -> Worker:
    """Create worker instance.

    Args:
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


if threading.current_thread() is not threading.main_thread():
    atexit.unregister(_exit_function)


def run_worker() -> None:
    """Run a worker."""
    from app.domain import scheduled_tasks, tasks
    from app.lib import log
    from app.lib.log.worker import after_process as after_logging_process
    from app.lib.log.worker import before_process as before_logging_process
    from app.lib.log.worker import on_shutdown as shutdown_logging_process
    from app.lib.log.worker import on_startup as startup_logging_process

    logger = log.get_logger()
    logger.info("Starting working pool")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    worker_kwargs: dict[str, Any] = {
        "tasks": tasks,
        "scheduled_tasks": scheduled_tasks,
        "startup": startup_logging_process,
        "shutdown": shutdown_logging_process,
        "after_process": after_logging_process,
        "before_process": before_logging_process,
    }
    worker_instance = create_worker_instance(**worker_kwargs)
    loop = asyncio.new_event_loop()
    if settings.worker.WEB_ENABLED:
        import aiohttp.web
        from saq.web import create_app

        async def shutdown(_app: Application) -> None:
            await worker_instance.stop()

        app = create_app([queue])
        app.on_shutdown.append(shutdown)
        loop.create_task(worker_instance.start())
        aiohttp.web.run_app(app, port=settings.worker.WEB_PORT, loop=loop)
    else:
        try:
            loop.run_until_complete(worker_instance.start())
        except KeyboardInterrupt:
            loop.run_until_complete(worker_instance.stop())


async def active_workers() -> int:
    """Return the number of active workers connected to the queue."""
    workers = await redis.keys(f"{queue.namespace('stats')}:*")
    return len(workers)


async def is_healthy() -> bool:
    """Server is healthy."""
    return bool(await active_workers())
