from datetime import datetime, timezone
from typing import Any, Union

import orjson
from asyncpg.pgproto import pgproto
from pydantic import SecretBytes


def serialize_object(value: Any) -> str:
    """
    Encodes json with the optimized ORJSON package

    orjson.dumps returns bytearray, so you can't pass it directly as json_serializer
    """

    def _serializer(value: Any) -> Any:
        if isinstance(value, pgproto.UUID):
            return str(value)
        if isinstance(value, SecretBytes):
            return value.get_secret_value().decode()
        raise TypeError

    return orjson.dumps(
        value,
        default=_serializer,
        option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY,
    ).decode()


def deserialize_object(value: Union[bytes, bytearray, memoryview, str, dict[str, Any]]) -> Any:
    """
    Decodes to an object with the optimized ORJSON package

    orjson.dumps returns bytearray, so you can't pass it directly as json_serializer

    """
    if isinstance(value, dict):
        return value
    return orjson.loads(value)


def convert_datetime_to_gmt(dt: datetime) -> str:
    """Handles datetime serialization for nested timestamps in models/dataclasses"""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def convert_string_to_camel_case(string: str) -> str:
    """Converts a string to camel case

    Args:
        string (str): The string to convert

    Returns:
        str: The string converted to camel case
    """
    return "".join(word if index == 0 else word.capitalize() for index, word in enumerate(string.split("_")))
