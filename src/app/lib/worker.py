from __future__ import annotations

import asyncio
import atexit
import dataclasses
import inspect
import threading
from collections import abc
from functools import wraps
from multiprocessing.util import _exit_function  # type: ignore[attr-defined]
from typing import TYPE_CHECKING, Any, Final

import anyio
import saq
import uvloop
from redis.asyncio import Redis

from app import utils
from app.lib import log, serialization, settings
from app.lib.exceptions import MissingDependencyError
from app.lib.log import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Collection, MutableMapping
    from signal import Signals

    from saq.types import Context

    from app.lib.service.generic import Service

__all__ = [
    "JobConfig",
    "Queue",
    "Worker",
    "Job",
    "CronJob",
    "WorkerFunction",
    "create_worker_instance",
    "default_job_config_dict",
    "make_service_callback",
    "enqueue_background_task_for_service",
    "queue",
    "monitored_job",
    "PeriodicHeartbeat",
    "run_worker",
]

logger = get_logger()


redis_client: Redis[bytes] = Redis.from_url(
    settings.redis.URL,
    decode_responses=False,
    socket_connect_timeout=settings.redis.SOCKET_CONNECT_TIMEOUT,
    health_check_interval=settings.redis.HEALTH_CHECK_INTERVAL,
    socket_keepalive=settings.redis.SOCKET_KEEPALIVE,
)
"""Async [`Redis`][redis.Redis] instance.

Configure via [CacheSettings][litestar_saqlalchemy.settings.RedisSettings].
This has the addition of setting the default encoder and decoder to msgpack for redis connectivity.
"""

WorkerFunction = abc.Callable[..., abc.Awaitable[Any]]
Job = saq.Job
CronJob = saq.CronJob

SERVICE_OBJECT_IDENTITY_MAP: MutableMapping[str, type[Service[Any]]] = {}
"""Used by the worker to lookup methods for service object callbacks."""


class Queue(saq.Queue):
    """Async task queue."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create an SAQ Queue.

        See: https://github.com/tobymao/saq/blob/master/saq/queue.py

        Names the queue per the application slug - namespaces SAQ's redis keys to the app.

        Configures `msgspec` for MessagePack serialization/deserialization if not
        otherwise configured.

        Args:
            *args: Passed through to `saq.Queue.__init__()`
            **kwargs: Passed through to `saq.Queue.__init__()`
        """
        kwargs.setdefault("name", "background-worker")
        kwargs.setdefault("dump", serialization.to_msgpack)
        kwargs.setdefault("load", serialization.from_msgpack)
        super().__init__(*args, **kwargs)

    def namespace(self, key: str) -> str:
        """Namespace for the Queue.

        Args:
            key (str): The unique key to use for the namespace.

        Returns:
            str: The worker namespace
        """
        return f"{settings.app.slug}:{self.name}:{key}"

    def job_id(self, job_key: str) -> str:
        """Job ID.

        Args:
            job_key (str): _description_

        Returns:
            str: _description_
        """
        return f"{settings.app.slug}:{self.name}:job:{job_key}"


class Worker(saq.Worker):
    """Modify behavior of saq worker for orchestration by Litestar."""

    # same issue: https://github.com/samuelcolvin/arq/issues/182
    SIGNALS: list[Signals] = []

    async def on_app_startup(self) -> None:  # pragma: no cover
        """Attach the worker to the running event loop."""
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())


queue = Queue(redis_client)
"""Async worker queue.

[Queue][litestar_saqlalchemy.worker.Queue] instance instantiated with
[redis][litestar_saqlalchemy.redis.client] instance.
"""


@dataclasses.dataclass()
class JobConfig:
    """Configure a Job.

    Used to configure jobs enqueued via
    `Service.enqueue_background_task()`
    """

    # pylint:disable=too-many-instance-attributes

    queue: Queue = queue
    """Queue associated with the job."""
    key: str | None = None
    """Pass in to control duplicate jobs."""
    timeout: int = settings.worker.JOB_TIMEOUT
    """Max time a job can run for, in seconds.

    Set to `0` for no timeout.
    """
    heartbeat: int = settings.worker.JOB_HEARTBEAT
    """Max time a job can survive without emitting a heartbeat. `0` to disable.

    `job.update()` will trigger a heartbeat.
    """
    retries: int = settings.worker.JOB_RETRIES
    """Max attempts for any job."""
    ttl: int = settings.worker.JOB_TTL
    """Lifetime of available job information, in seconds.

    0: indefinite
    -1: disabled (no info retained)
    """
    retry_delay: float = settings.worker.JOB_TTL
    """Seconds to delay before retrying a job."""
    retry_backoff: bool | float = settings.worker.JOB_RETRY_BACKOFF
    """If true, use exponential backoff for retry delays.

    - The first retry will have whatever retry_delay is.
    - The second retry will have retry_delay*2. The third retry will have retry_delay*4. And so on.
    - This always includes jitter, where the final retry delay is a random number between 0 and the calculated retry delay.
    - If retry_backoff is set to a number, that number is the maximum retry delay, in seconds."
    """


default_job_config_dict = utils.dataclass_as_dict_shallow(JobConfig(), exclude_none=True)


def create_worker_instance(
    functions: Collection[Callable[..., Any] | tuple[str, Callable]],
    cron_jobs: Collection[saq.CronJob] = (),
    concurrency: int | None = None,
    startup: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    shutdown: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    before_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    after_process: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
) -> Worker:
    """Create worker instance.

    Args:
        functions: Functions to be called via the async workers.
        cron_jobs: Cron configuration to schedule at startup.
        concurrency: The number of jobs allowed to execute simultaneously per worker.
        startup: Async function called on worker startup.
        shutdown: Async function called on worker shutdown.
        before_process: Async function called before a job processes.
        after_process: Async function called after a job processes.

    Returns:
        The worker instance, instantiated with `functions`.
    """
    if concurrency is None:
        concurrency = settings.worker.CONCURRENCY
    return Worker(
        queue,
        functions=functions,
        cron_jobs=cron_jobs,
        startup=startup,
        concurrency=concurrency,
        shutdown=shutdown,
        before_process=before_process,
        after_process=after_process,
    )


async def make_service_callback(
    _ctx: Context,
    *,
    service_type_id: str,
    service_method_name: str,
    **kwargs: Any,
) -> None:
    """Make an async service callback.

    Args:
        _ctx: the SAQ context
        service_type_id: Value of `__id__` class var on service type.
        service_method_name: Method to be called on the service object.
        **kwargs: Unpacked into the service method call as keyword arguments.
    """
    service_type = SERVICE_OBJECT_IDENTITY_MAP[service_type_id]
    async with service_type.new() as service_object:
        method = getattr(service_object, service_method_name)
        await method(**kwargs)


async def enqueue_background_task_for_service(
    service_obj: Service,
    method_name: str,
    job_config: JobConfig | None = None,
    **kwargs: Any,
) -> None:
    """Enqueue an async callback for the operation and data.

    Args:
        service_obj: The Service instance that is requesting the callback.
        method_name: Method on the service object that should be called by the async worker.
        job_config: Configuration object to control the job that is enqueued.
        **kwargs: Arguments to be passed to the method when called. Must be JSON serializable.
    """
    module = inspect.getmodule(service_obj)
    if module is None:  # pragma: no cover
        logger.warning("Callback not enqueued, no module resolved for %s", service_obj)
        return
    job_config_dict: dict[str, Any]
    if job_config is None:
        job_config_dict = default_job_config_dict
    else:
        job_config_dict = utils.dataclass_as_dict_shallow(job_config, exclude_none=True)

    kwargs["service_type_id"] = service_obj.__id__
    kwargs["service_method_name"] = method_name
    job = saq.Job(
        function=make_service_callback.__qualname__,
        kwargs=kwargs,
        **job_config_dict,
    )
    await queue.enqueue(job)


TEN: Final = 10


class PeriodicHeartbeat:
    """Periodic Heartbeat.

    Class to manage agent Heartbeats while the agent is running Posts a
    message to a redis key with a limited TTL.
    """

    def __init__(self, job: Job) -> None:
        """Initialize heartbeat.

        Args:
            job (Job): _description_
        """
        self._running: bool = True
        self.job = job
        self.heartbeat_enabled: bool = bool(
            job.timeout and job.timeout > 0 and job.heartbeat and job.heartbeat > 0,
        )
        if self.heartbeat_enabled and job.heartbeat <= TEN:
            self.heartbeat = 1
        elif self.heartbeat_enabled and job.heartbeat > TEN:
            self.heartbeat = 5
        else:
            self.heartbeat = 0

    async def start(self, func: Awaitable) -> Any:
        """Start Heartbeat."""
        if self.heartbeat_enabled:
            logger.debug(
                "❤️  starting heartbeat service for %s. Ticking every %s seconds",
                self.job.id,
                self.heartbeat,
            )
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(self._periodically_publish)
            executed_func = await func
            await task_group.cancel_scope.cancel()
            return executed_func

    async def stop(self) -> None:
        """Stop heartbeat service."""
        if self.heartbeat_enabled:
            logger.debug("❤️  stopping heartbeat service for %s", self.job.id)
        if self._running:
            self._running = False

    async def _periodically_publish(self) -> None:
        """Periodically publish heartbeat message."""
        while self._running and self.heartbeat_enabled:
            logger.debug(
                "❤️  ticking heartbeat for %s, and sleeping for %s seconds",
                self.job.id,
                self.heartbeat,
            )
            await self.job.update()
            await anyio.sleep(self.heartbeat)


# decorator to perform a heartbeat in the background while a function is running
def monitored_job(func: Any):  # type: ignore
    """Monitor job.

    Decorator to specify a function as a monitored job.

    Args:
        func (_type_): _description_

    Returns:
        _type_: _description_
    """

    @wraps(func)
    async def with_heartbeat(*args, **kwargs):  # type: ignore
        context = args[0]
        job = context["job"]
        heartbeat = PeriodicHeartbeat(job)
        try:
            await heartbeat.start(func(*args, **kwargs))
        finally:
            await heartbeat.stop()

    return with_heartbeat


if threading.current_thread() is not threading.main_thread():
    atexit.unregister(_exit_function)


def run_worker() -> None:
    """Run a worker."""
    logger = log.get_logger()
    logger.info("Starting working pool")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    worker_kwargs: dict[str, Any] = {
        "functions": [(make_service_callback.__qualname__, make_service_callback)],
    }
    worker_kwargs["before_process"] = log.worker.before_process
    worker_kwargs["after_process"] = log.worker.after_process

    worker_instance = create_worker_instance(**worker_kwargs)
    loop = asyncio.new_event_loop()
    if settings.worker.WEB_ENABLED:
        try:
            import aiohttp.web  # pyright:ignore[reportMissingImports] # pylint: disable=import-outside-toplevel,import-error
            from saq.web import create_app  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise MissingDependencyError("aiohttp", "saq") from e
        if TYPE_CHECKING:
            from aiohttp.web_app import (  # pyright:ignore[reportMissingImports] # pylint: disable=import-outside-toplevel
                Application,
            )

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
    workers = await redis_client.keys(f"{queue.namespace('stats')}:*")
    return len(workers)
