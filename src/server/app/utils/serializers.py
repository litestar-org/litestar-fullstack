from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import msgspec
from asyncpg.pgproto import pgproto
from pydantic import BaseModel


def _default(value: Any) -> str:
    if isinstance(value, BaseModel):
        return str(value.dict(by_alias=False))
    if isinstance(value, pgproto.UUID):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    raise TypeError()


_msgspec_json_encoder = msgspec.json.Encoder(enc_hook=_default)
_msgspec_json_decoder = msgspec.json.Decoder()


def serialize_object(value: Any) -> bytes:
    """Encodes json with the optimized msgspec package."""
    return _msgspec_json_encoder.encode(value)


def deserialize_object(value: bytes | str) -> Any:
    """Decodes to an object with the optimized msgspec package.

    orjson.dumps returns bytearray, so you can't pass it directly as
    json_serializer
    """
    return _msgspec_json_decoder.decode(value)


def convert_datetime_to_gmt(dt: datetime) -> str:
    """Handles datetime serialization for nested timestamps in.

    models/dataclasses.
    """
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def convert_string_to_camel_case(string: str) -> str:
    """Converts a string to camel case.

    Args:
        string (str): The string to convert

    Returns:
        str: The string converted to camel case
    """
    return "".join(word if index == 0 else word.capitalize() for index, word in enumerate(string.split("_")))
