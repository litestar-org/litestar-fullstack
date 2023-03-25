# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
from typing import Any
from uuid import UUID

import msgspec
from asyncpg.pgproto import pgproto
from pydantic import BaseModel

__all__ = [
    "convert_datetime_to_gmt",
    "convert_string_to_camel_case",
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


def convert_string_to_camel_case(string: str) -> str:
    """Convert a string to camel case.

    Args:
        string (str): The string to convert

    Returns:
        str: The string converted to camel case
    """
    return "".join(word if index == 0 else word.capitalize() for index, word in enumerate(string.split("_")))
