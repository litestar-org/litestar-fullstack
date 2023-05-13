from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from saq.types import QueueInfo

from app.lib.worker import Job, Queue, Worker, dependencies

__all__ = ["SAQConfig", "SAQPlugin"]


if TYPE_CHECKING:
    from typing import Any

    from litestar import Litestar
    from litestar.config.app import AppConfig

T = TypeVar("T")


@dataclass
class SAQConfig(Generic[T]):
    """SAQ Configuration."""

    queues_dependency_key: str = "task_queues"

    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {"Queue": Queue, "Worker": Worker, "QueueInfo": QueueInfo, "Job": Job}

    async def on_shutdown(self, app: Litestar) -> None:
        """Disposes of the SQLAlchemy engine.

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
