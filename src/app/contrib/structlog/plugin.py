from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.data_extractors import (  # noqa: TCH002
    RequestExtractorField,
    ResponseExtractorField,
)
from litestar.plugins import InitPluginProtocol

from . import configure, default_processors
from .controller import BeforeSendHandler, LoggingMiddleware

__all__ = ["StructLogConfig", "StructLogPlugin"]


if TYPE_CHECKING:
    from typing import Any

    from litestar.config.app import AppConfig
    from litestar.logging.config import LoggingConfig

T = TypeVar("T")


@dataclass
class StructLogConfig(Generic[T]):
    """StructLog Configuration."""

    logging_config: LoggingConfig
    """Litestar Logging config."""
    # https://stackoverflow.com/a/1845097/6560549
    exclude_paths: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    http_event: str = "HTTP"
    """Log event name for logs from Litestar handlers."""
    include_compressed_body: bool = False
    """Include 'body' of compressed responses in log output."""
    level: int = 20
    """Stdlib log levels.

    Only emit logs at this level, or higher.
    """
    obfuscate_cookies: set[str] = field(default_factory=lambda: {"session"})
    """Request cookie keys to obfuscate."""
    obfuscate_headers: set[str] = field(
        default_factory=lambda: {"Authorization", "X-API-KEY", "X-Serverless-Authorization"}
    )
    """Request header keys to obfuscate."""

    request_fields: list[RequestExtractorField] = field(
        default_factory=lambda: [
            "path",
            "method",
            "headers",
            "cookies",
            "query",
            "path_params",
            "body",
        ]
    )
    """Attributes of the [Request][litestar.connection.request.Request] to be
    logged."""
    response_fields: list[ResponseExtractorField] = field(
        default_factory=lambda: [
            "status_code",
            "cookies",
            "headers",
            "body",
        ]
    )
    """Attributes of the [Response][litestar.response.Response] to be
    logged."""
    """Log event name for logs from SAQ worker."""


    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {}


class StructLogPlugin(InitPluginProtocol, _slots_base.SlotsBase):
    """StructLog plugin."""

    __slots__ = ()

    def __init__(self, config: StructLogConfig) -> None:
        """Initialize ``StructLogPlugin``.

        Args:
            config: configure and start StructLog.
        """
        self._config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """
        app_config.before_send.append(BeforeSendHandler())
        app_config.middleware.append(LoggingMiddleware)
        app_config.logging_config = self._config.logging_config
        app_config.on_startup.append(configure(default_processors))  # type: ignore[arg-type]
        app_config.signature_namespace.update(self._config.signature_namespace)
        return app_config
