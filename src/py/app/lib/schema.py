"""Base structs and constrained field types shared by API schemas."""

from __future__ import annotations

from typing import Annotated, Any

import msgspec

__all__ = ("BaseStruct", "CamelizedBaseStruct", "Email", "Message", "Name", "Phone", "Username")

Email = Annotated[
    str,
    msgspec.Meta(
        max_length=254,
        pattern=r"^[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$",
        description="Email address",
    ),
]
Name = Annotated[
    str,
    msgspec.Meta(
        min_length=1,
        max_length=100,
        pattern=r"^(?=.*\S)[a-zA-ZÀ-ÿĀ-žА-я\u4e00-\u9fff\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\s'\-\.]+$",
        description="Human name (1-100 characters, not only spaces)",
    ),
]
Username = Annotated[
    str,
    msgspec.Meta(
        min_length=3,
        max_length=30,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
        description="Username (3-30 lowercase letters, digits, hyphens, or underscores)",
    ),
]
Phone = Annotated[
    str,
    msgspec.Meta(
        max_length=20,
        pattern=r"^\+?(?:[\s().-]*[0-9]){7,15}[\s().-]*$",
        description="Phone number (7-15 digits, optionally with a leading + and separators)",
    ),
]


class BaseStruct(msgspec.Struct):
    """Base msgspec Struct with unset-filtering dictionary export."""

    def to_dict(self) -> dict[str, Any]:
        """Convert populated struct fields to a plain dictionary.

        Returns:
            Dictionary of field names to values, excluding ``msgspec.UNSET`` fields.
        """
        return {
            name: getattr(self, name) for name in self.__struct_fields__ if getattr(self, name, None) != msgspec.UNSET
        }


class CamelizedBaseStruct(BaseStruct, rename="camel"):
    """Camel-cased msgspec Struct for HTTP API payloads."""


class Message(CamelizedBaseStruct):
    """Simple human-readable status message payload."""

    message: str
