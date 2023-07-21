from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.plugins import InitPluginProtocol

from app.contrib.vite.config import ViteTemplateConfig
from app.contrib.vite.template_engine import ViteTemplateEngine

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

    from app.contrib.vite.config import ViteConfig

T = TypeVar("T")


class VitePlugin(InitPluginProtocol, _slots_base.SlotsBase):
    """Vite plugin."""

    __slots__ = ()

    def __init__(self, config: ViteConfig) -> None:
        """Initialize ``Vite``.

        Args:
            config: configure and start Vite.
        """
        self._config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with Vite.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """
        app_config.template_config = ViteTemplateConfig(  # type: ignore[assignment]
            directory=self._config.templates_dir,
            engine=ViteTemplateEngine,
            config=self._config,
        )
        return app_config
