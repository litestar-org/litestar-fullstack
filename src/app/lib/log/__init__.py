"""All the logging config and things are in here."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog
from starlite.logging.config import LoggingConfig

from app.lib import settings

from . import controller, worker
from .utils import EventFilter, msgspec_json_renderer

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from structlog import BoundLogger
    from structlog.types import Processor

__all__ = (
    "default_processors",
    "config",
    "configure",
    "controller",
    "worker",
)


default_processors = [
    structlog.contextvars.merge_contextvars,
    controller.drop_health_logs,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

stdlib_processors = [
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.stdlib.add_log_level,
    structlog.stdlib.ExtraAdder(),
    EventFilter(["color_message"]),
    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
]

if sys.stderr.isatty() or "pytest" in sys.modules:  # pragma: no cover
    LoggerFactory: Any = structlog.WriteLoggerFactory
    console_processor = structlog.dev.ConsoleRenderer(
        colors=True,
        exception_formatter=structlog.dev.plain_traceback,
    )
    default_processors.extend([console_processor])
    stdlib_processors.append(console_processor)
else:
    LoggerFactory = structlog.BytesLoggerFactory
    default_processors.extend([structlog.processors.dict_tracebacks, msgspec_json_renderer])
    stdlib_processors.append(structlog.processors.dict_tracebacks)


def configure(processors: Sequence[Processor]) -> None:
    """Call to configure `structlog` on app startup.

    The calls to `structlog.get_logger()` in `controller.py` and
    `worker.py` return proxies to the logger that is eventually called
    after this configurator function has been called. Therefore, nothing
    should try to log via structlog before this is called.
    """
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=LoggerFactory(),
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.LEVEL),
    )


config = LoggingConfig(
    root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
    formatters={
        "standard": {"()": structlog.stdlib.ProcessorFormatter, "processors": stdlib_processors},
    },
    loggers={
        "uvicorn.access": {
            "propagate": False,
            "level": settings.log.UVICORN_ACCESS_LEVEL,
            "handlers": ["queue_listener"],
        },
        "uvicorn.error": {
            "propagate": False,
            "level": settings.log.UVICORN_ERROR_LEVEL,
            "handlers": ["queue_listener"],
        },
        "saq": {
            "propagate": False,
            "level": settings.log.SAQ_LEVEL,
            "handlers": ["queue_listener"],
        },
        "sqlalchemy.engine": {
            "propagate": False,
            "level": settings.log.SQLALCHEMY_LEVEL,
            "handlers": ["queue_listener"],
        },
    },
)
"""Pre-configured log config for application deps.

While we use structlog for internal app logging, we still want to ensure
that logs emitted by any of our dependencies are handled in a non-
blocking manner.
"""


def get_logger(*args: Any, **kwargs: Any) -> BoundLogger:
    """Return a configured logger for the given name.

    Returns:
        Logger: A configured logger instance
    """
    config.configure()
    configure(default_processors)  # type: ignore[arg-type]
    return structlog.getLogger(*args, **kwargs)  # type: ignore
