from __future__ import annotations

from typing import Any

import msgspec

__all__ = ("BaseStruct", "CamelizedBaseStruct", "Message")


class BaseStruct(msgspec.Struct):
    """Base msgspec Struct with unset-filtering dictionary export."""

    def to_dict(self) -> dict[str, Any]:
        """Convert populated struct fields to a plain dictionary.

        Returns:
            Dictionary of field names to values, excluding ``msgspec.UNSET`` fields.
        """
        return {f: getattr(self, f) for f in self.__struct_fields__ if getattr(self, f, None) != msgspec.UNSET}


class CamelizedBaseStruct(BaseStruct, rename="camel"):
    """Camel-cased msgspec Struct for HTTP API payloads."""


class Message(CamelizedBaseStruct):
    """Simple human-readable status message payload."""

    message: str
