"""Logging utilities.

``msgspec_json_renderer()``
    A JSON Renderer for structlog using msgspec.

    Msgspec doesn't have an API consistent with the stdlib's ``json`` module,
    which is required for structlog's ``JSONRenderer``.

``EventFilter``
    A structlog processor that removes keys from the log event if they exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.lib.serialization import _msgspec_json_encoder

__all__ = ["EventFilter", "msgspec_json_renderer"]


if TYPE_CHECKING:
    from collections.abc import Iterable

    from structlog.typing import EventDict, WrappedLogger


def msgspec_json_renderer(event_dict: EventDict, **_: Any) -> bytes:
    """Structlog processor that uses `msgspec` for JSON encoding.

    Args:
         event_dict (): The data to be logged.

    Returns:
        The log event encoded to JSON by msgspec.
    """
    return _msgspec_json_encoder.encode(event_dict)


def msgspec_json_str_renderer(event_dict: EventDict, **_: Any) -> str:
    """Structlog processor that uses `msgspec` for JSON encoding.

    Args:
         event_dict (): The data to be logged.

    Returns:
        The log event encoded to JSON by msgspec as a string
    """
    return _msgspec_json_encoder.encode(event_dict).decode("utf-8")


class EventFilter:
    """Remove keys from the log event.

    Add an instance to the processor chain.

    .. code-block:: python
        :caption: Examples

        structlog.configure(
            ...,
            processors=[
                ...,
                EventFilter(["color_message"]),
                ...,
            ],
        )

    """

    def __init__(self, filter_keys: Iterable[str]) -> None:
        """Initialize the EventFilter.

        Args:
            filter_keys: Iterable of string keys to be excluded from the log event.
        """
        self.filter_keys = filter_keys

    def __call__(self, _: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
        """Receive the log event, and filter keys.

        Args:
            _ ():
            __ ():
            event_dict (): The data to be logged.

        Returns:
            The log event with any key in `self.filter_keys` removed.
        """
        for key in self.filter_keys:
            event_dict.pop(key, None)
        return event_dict
