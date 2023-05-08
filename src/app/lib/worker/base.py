from __future__ import annotations

import asyncio
from collections import abc
from typing import TYPE_CHECKING, Any

import saq
from redis.asyncio import Redis

from app.lib import serialization, settings

if TYPE_CHECKING:
    from signal import Signals


__all__ = ["Queue", "Worker", "WorkerFunction", "queue", "BackgroundTaskError"]


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
