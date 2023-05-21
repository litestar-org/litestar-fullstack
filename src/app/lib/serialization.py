import datetime
from typing import Any
from uuid import UUID

import msgspec
from asyncpg.pgproto import pgproto
from pydantic import BaseModel

__all__ = [
    "convert_datetime_to_gmt",
    "from_json",
    "from_msgpack",
    "to_json",
    "to_msgpack",
]


def _default(value: Any) -> str:
    if isinstance(value, BaseModel):
        return str(value.dict(by_alias=True))
    if isinstance(value, pgproto.UUID | UUID):
        return str(value)
    if isinstance(value, datetime.datetime):
        return convert_datetime_to_gmt(value)
    if isinstance(value, datetime.date):
        return convert_date_to_iso(value)
    try:
        val = str(value)
    except Exception as exc:  # noqa: BLE001
        raise TypeError from exc
    else:
        return val


_msgspec_json_encoder = msgspec.json.Encoder(enc_hook=_default)
_msgspec_json_decoder = msgspec.json.Decoder()
_msgspec_msgpack_encoder = msgspec.msgpack.Encoder(enc_hook=_default)
_msgspec_msgpack_decoder = msgspec.msgpack.Decoder()


def to_json(value: Any) -> bytes:
    """Encode json with the optimized msgspec package."""
    return _msgspec_json_encoder.encode(value)


def from_json(value: bytes | str) -> Any:
    """Decode to an object with the optimized msgspec package."""
    return _msgspec_json_decoder.decode(value)


def to_msgpack(value: Any) -> bytes:
    """Encode json with the optimized msgspec package."""
    return _msgspec_msgpack_encoder.encode(value)


def from_msgpack(value: bytes) -> Any:
    """Decode to an object with the optimized msgspec package."""
    return _msgspec_msgpack_decoder.decode(value)


def convert_datetime_to_gmt(dt: datetime.datetime) -> str:
    """Handle datetime serialization for nested timestamps."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=datetime.UTC)
    return dt.isoformat().replace("+00:00", "Z")


def convert_date_to_iso(dt: datetime.date) -> str:
    """Handle date serialization for nested dates."""
    return dt.isoformat()
