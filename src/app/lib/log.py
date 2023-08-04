"""All the logging config and things are in here."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import structlog
from litestar.logging.config import LoggingConfig

from app.contrib.structlog import configure, default_processors, stdlib_processors
from app.lib import settings

if TYPE_CHECKING:
    from typing import Any

    from structlog import BoundLogger


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
        "sqlalchemy.pool": {
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
