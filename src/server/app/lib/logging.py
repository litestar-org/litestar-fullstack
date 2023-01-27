"""Log configuration.

Adds `getLogger` function and re-exports `starlite-saqlalchemy` log
config for convenience.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from starlite_saqlalchemy.log import config

if TYPE_CHECKING:
    from structlog import BoundLogger as Logger

__all__ = ["getLogger", "config"]


def getLogger(name: str | None = None, **kwargs: Any) -> "Logger":  # noqa: N802
    """Return a configured logger for the given name.

    Args:
        name (str, optional): _description_. Defaults to "None".

    Returns:
        Logger: A configured logger instance
    """
    return structlog.getLogger(name, **kwargs)  # type: ignore
