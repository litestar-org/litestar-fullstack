from __future__ import annotations

import sys
from dataclasses import dataclass, field
from logging import getLevelName
from typing import TYPE_CHECKING, Generic, TypeVar

import structlog
from litestar.contrib.sqlalchemy.plugins import _slots_base
from litestar.data_extractors import (  # noqa: TCH002
    RequestExtractorField,
    ResponseExtractorField,
)
from litestar.logging.config import LoggingConfig
from litestar.plugins import InitPluginProtocol
from structlog.stdlib import ProcessorFormatter

from . import controller
from .controller import BeforeSendHandler, LoggingMiddleware
from .utils import EventFilter, msgspec_json_renderer

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from litestar.config.app import AppConfig
    from structlog.types import Processor

__all__ = ["StructLogConfig", "StructLogPlugin"]

ENABLE_TTY = bool(sys.stderr.isatty() or "pytest" in sys.modules)

T = TypeVar("T")


DEFAULT_PROCESSORS = [
    structlog.processors.add_log_level,
    structlog.contextvars.merge_contextvars,
    controller.drop_health_logs,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(["click", "rich", "rich_click", "saq"]),
]

STDLIB_PROCESSORS = [
    structlog.stdlib.add_log_level,
    EventFilter(["color_message"]),
    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]


@dataclass
class StructLogConfig(Generic[T]):
    """StructLog Configuration."""

    loggers: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "litestar": {"level": "INFO", "handlers": ["queue_listener"], "propagate": False},
        }
    )
    """Loggers"""
    default_processors: Sequence[Processor] = field(default_factory=lambda: DEFAULT_PROCESSORS)
    """default processors"""
    stdlib_processors: Sequence[Processor] = field(default_factory=lambda: STDLIB_PROCESSORS)
    """stdlib processors"""
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
    _logging_config: LoggingConfig | None = None

    @property
    def signature_namespace(self) -> dict[str, Any]:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        return {"LoggingConfig": LoggingConfig}

    @property
    def logging_config(self) -> LoggingConfig:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """
        if self._logging_config is None:
            self._logging_config = LoggingConfig(
                root={"level": getLevelName(self.level), "handlers": ["queue_listener"]},
                formatters={
                    "standard": {"()": ProcessorFormatter, "processors": self.stdlib_processors},
                },
                loggers=self.loggers,
            )
        return self._logging_config

    def configure(self, processors: Sequence[Processor] | None = None) -> None:
        """Call to configure `structlog` on app startup.

        The calls to `structlog.get_logger()` in `controller.py` and
        `worker.py` return proxies to the logger that is eventually called
        after this configurator function has been called. Therefore, nothing
        should try to log via structlog before this is called.
        """

        if ENABLE_TTY:  # pragma: no cover
            logger_factory: Any = structlog.WriteLoggerFactory
            console_processor = structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
            self.default_processors.extend([console_processor])
            self.stdlib_processors.extend([console_processor])
        else:
            logger_factory = structlog.BytesLoggerFactory
            self.default_processors.extend([msgspec_json_renderer])

        self.logging_config.configure()

        structlog.configure(
            cache_logger_on_first_use=True,
            logger_factory=logger_factory(),
            processors=processors if processors is not None else self.default_processors,
            wrapper_class=structlog.make_filtering_bound_logger(self.level),
        )


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
        app_config.before_send.append(BeforeSendHandler(config=self._config))
        app_config.middleware.append(LoggingMiddleware)
        app_config.logging_config = self._config.logging_config
        app_config.signature_namespace.update(self._config.signature_namespace)
        self._config.configure()
        return app_config

    def configure(self, processors: Sequence[Processor] | None = None) -> None:
        """Call to configure `structlog` on app startup."""
        self._config.configure()

    @property
    def logging_config(self) -> LoggingConfig:
        """Return the plugin's signature namespace.

        Returns:
            A string keyed dict of names to be added to the namespace for signature forward reference resolution.
        """

        return self._config.logging_config
