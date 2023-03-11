"""Log configuration.

Adds `getLogger` function and re-exports `starlite-saqlalchemy` log
config for convenience.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from starlite_saqlalchemy.log import config, configure, default_processors

if TYPE_CHECKING:
    from structlog import BoundLogger as Logger

__all__ = ["get_logger", "config", "configure", "default_processors"]


def get_logger(*args: Any, **kwargs: Any) -> Logger:
    """Return a configured logger for the given name.

    Returns:
        Logger: A configured logger instance
    """
    config.configure()
    configure(default_processors)  # type: ignore[arg-type]
    return structlog.getLogger(*args, **kwargs)  # type: ignore
