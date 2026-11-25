from __future__ import annotations

import sys
from functools import lru_cache
from typing import TYPE_CHECKING

import structlog
from advanced_alchemy.exceptions import DuplicateKeyError, ForeignKeyError, NotFoundError
from litestar.exceptions import HTTPException
from litestar.serialization import encode_json
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from structlog.dev import RichTracebackFormatter

from app.lib.exceptions import ApplicationClientError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from litestar.types import Logger, Scope
    from structlog.types import EventDict, WrappedLogger
    from structlog.typing import Processor

__all__ = (
    "EventFilter",
    "add_google_cloud_attributes",
    "is_tty",
    "log_server_error",
    "stdlib_json_serializer",
    "stdlib_logger_processors",
    "structlog_json_serializer",
    "structlog_processors",
)


@lru_cache
def is_tty() -> bool:
    """Return whether standard input/output streams are attached to a TTY."""
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


def structlog_json_serializer(value: EventDict, **_: Any) -> bytes:
    """Serialize a structlog event dict into UTF-8 JSON bytes.

    Returns:
        UTF-8 encoded JSON bytes for the event dictionary.
    """
    return encode_json(value)


def stdlib_json_serializer(value: EventDict, **_: Any) -> str:
    """Serialize a stdlib-bridged structlog event dict into a JSON string.

    Returns:
        JSON-formatted string for the event dictionary.
    """
    return encode_json(value).decode("utf-8")


def add_google_cloud_attributes(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Add Google Cloud structured logging fields to the event dictionary.

    Args:
        _: Wrapped logger object.
        __: Name of the wrapped log method.
        event_dict: Current log event dictionary.

    Returns:
        Updated event dictionary containing Cloud Logging severity and logger fields.
    """
    event_dict["severity"] = event_dict.get("level")
    event_dict["labels"] = None
    event_dict["resource"] = None
    if event_dict.get("logger"):
        event_dict["python_logger"] = event_dict.pop("logger")
    return event_dict


class EventFilter:
    """Remove specified keys from a structlog event dictionary."""

    __slots__ = ("filter_keys",)

    def __init__(self, filter_keys: Iterable[str]) -> None:
        """Initialize the event filter.

        Args:
            filter_keys: Iterable of event keys to strip.
        """
        self.filter_keys = tuple(filter_keys)

    def __call__(self, _: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
        """Strip configured keys from the log event dictionary.

        Args:
            _: Wrapped logger object.
            __: Name of the wrapped log method.
            event_dict: Current log event dictionary.

        Returns:
            Event dictionary without filtered keys.
        """
        for key in self.filter_keys:
            event_dict.pop(key, None)
        return event_dict


def structlog_processors(as_json: bool) -> list[Processor]:
    """Build structlog processors for JSON or interactive console rendering.

    Args:
        as_json: Whether to format log records as JSON.

    Returns:
        Ordered list of structlog processors.
    """
    if as_json:
        return [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            add_google_cloud_attributes,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(serializer=structlog_json_serializer),
        ]
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=RichTracebackFormatter(max_frames=1, show_locals=False, width=80),
        ),
    ]


def stdlib_logger_processors(as_json: bool) -> list[Processor]:
    """Build structlog ProcessorFormatter processors for stdlib logging.

    Args:
        as_json: Whether to format stdlib log records as JSON.

    Returns:
        Ordered list of stdlib-compatible structlog processors.
    """
    if as_json:
        return [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.ExtraAdder(),
            EventFilter(["color_message"]),
            structlog.processors.EventRenamer("message"),
            add_google_cloud_attributes,
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(serializer=stdlib_json_serializer),
        ]
    return [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        EventFilter(["color_message"]),
        EventFilter(["message"]),
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=RichTracebackFormatter(max_frames=1, show_locals=False, width=80),
        ),
    ]


def log_server_error(logger: Logger, scope: Scope, stack_trace: list[str]) -> None:
    """Log an uncaught exception with its stack trace, unless the client caused it.

    A client error is an ``HTTPException`` answering below 500, or one of the application and repository
    exceptions that ``exception_to_http_response`` always answers with a 4xx status. Litestar's own
    ``disable_stack_trace`` cannot express this, because it looks at the status code of the exception's
    class and misses a status passed when the exception is raised.

    Args:
        logger: Logger the application logs exceptions with.
        scope: Connection the exception was raised in.
        stack_trace: Formatted stack trace, unused because the logger formats the exception itself.
    """
    _ = stack_trace
    error = sys.exc_info()[1]
    if isinstance(error, HTTPException) and error.status_code < HTTP_500_INTERNAL_SERVER_ERROR:
        return
    if isinstance(error, ApplicationClientError | NotFoundError | DuplicateKeyError | ForeignKeyError):
        return
    logger.error("Uncaught exception", connection_type=scope["type"], path=scope["path"], exc_info=error)
