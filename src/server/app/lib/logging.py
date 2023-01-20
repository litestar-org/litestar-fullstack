"""Logging configuration."""
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from structlog import BoundLogger as Logger

__all__ = ["getLogger"]


def getLogger(name: str | None = None) -> "Logger":  # noqa: N802
    """Returns a configured logger for the given name.

    Args:
        name (str, optional): _description_. Defaults to "dbma".

    Returns:
        Logger: A configured logger instance
    """
    return structlog.getLogger(name)  # type: ignore
