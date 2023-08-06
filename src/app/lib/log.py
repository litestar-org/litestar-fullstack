"""All the logging config and things are in here."""

from __future__ import annotations

from typing import TYPE_CHECKING

from structlog import getLogger

__all__ = ["get_logger"]


if TYPE_CHECKING:
    from typing import Any

    from structlog import BoundLogger


def get_logger(*args: Any, **kwargs: Any) -> BoundLogger:
    """Return a configured logger for the given name.

    Returns:
        Logger: A configured logger instance
    """
    return getLogger(*args, **kwargs)  # type: ignore
