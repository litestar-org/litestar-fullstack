from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from saq.types import QueueInfo

from . import dependencies
from .base import Job, Queue, Worker

__all__ = ["SAQConfig", "SAQPlugin"]


if TYPE_CHECKING:
    from typing import Any

    from litestar import Litestar
    from litestar.config.app import AppConfig

T = TypeVar("T")


@dataclass
class SAQConfig(Generic[T]):
    """SAQ Configuration."""

    queues_dependency_key: str = field(default="task_queues")
    """Key to use for storing dependency information in litestar."""
    job_timeout: int = 10
    """Max time a job can run for, in seconds.

    Set to `0` for no timeout.
    """
    job_heartbeat: int = 0
    """Max time a job can survive without emitting a heartbeat. `0` to disable.

    `job.update()` will trigger a heartbeat.
    """
    job_retries: int = 10
    """Max attempts for any job."""
    job_ttl: int = 600
    """Lifetime of available job information, in seconds.

    0: indefinite
    -1: disabled (no info retained)
    """
    job_retry_delay: float = 1.0
    """Seconds to delay before retrying a job."""
    job_retry_backoff: bool | float = 60
    """If true, use exponential backoff for retry delays.

    - The first retry will have whatever retry_delay is.
    - The second retry will have retry_delay*2. The third retry will have retry_delay*4. And so on.
    - This always includes jitter, where the final retry delay is a random number between 0 and the calculated retry delay.
    - If retry_backoff is set to a number, that number is the maximum retry delay, in seconds."
    """
    worker_concurrency: int = 10
    """The number of concurrent jobs allowed to execute per worker.

    Default is set to 10.
    """
    worker_processes: int = 1
    """The number of worker processes to spawn.

    Default is set to 1.
    """
    web_enabled: bool = False
    """If true, the worker admin UI is launched on worker startup.."""

    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {"Queue": Queue, "Worker": Worker, "QueueInfo": QueueInfo, "Job": Job}

    async def on_shutdown(self, app: Litestar) -> None:
        """Disposes of the SAQ Workers.

        Args:
            app: The ``Litestar`` instance.

        Returns:
            None
        """


class SAQPlugin(InitPluginProtocol, _slots_base.SlotsBase):
    """SAQ plugin."""

    __slots__ = ()

    def __init__(self, config: SAQConfig) -> None:
        """Initialize ``SAQPlugin``.

        Args:
            config: configure and start SAQ.
        """
        self._config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """
        app_config.dependencies.update(
            {
                self._config.queues_dependency_key: Provide(dependency=dependencies.provide_queues),
            }
        )
        app_config.on_shutdown.append(self._config.on_shutdown)
        app_config.signature_namespace.update(self._config.signature_namespace)
        return app_config
