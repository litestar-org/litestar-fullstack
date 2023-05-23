from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.plugins import InitPluginProtocol

from .service import AiosqlQueryManager

__all__ = ["AioSQLConfig", "AioSQLPlugin"]


if TYPE_CHECKING:
    from typing import Any

    from litestar.config.app import AppConfig

T = TypeVar("T")


@dataclass
class AioSQLConfig(Generic[T]):
    """AioSQL Configuration."""

    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {"AiosqlQueryManager": AiosqlQueryManager}


class AioSQLPlugin(InitPluginProtocol, _slots_base.SlotsBase):
    """AioSQL plugin."""

    __slots__ = ()

    def __init__(self, config: AioSQLConfig) -> None:
        """Initialize ``AioSQLPlugin``.

        Args:
            config: configure and start AioSQL.
        """
        self._config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with AIOSQL.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """
        app_config.signature_namespace.update(self._config.signature_namespace)
        return app_config
