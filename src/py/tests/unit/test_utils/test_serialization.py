import datetime
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.utils import serialization


class SimpleModel(BaseModel):
    key: str
    value: int


class NonSerializable:
    def __str__(self) -> str:
        msg = "Cannot serialize this object"
        raise TypeError(msg)


@pytest.mark.parametrize(
    ("value", "expected_output"),
    [
        (SimpleModel(key="test", value=123), '{"key": "test", "value": 123}'),
        (uuid4(), lambda v: isinstance(v, str) and len(v) == 36),  # Check if it's a UUID string
        (datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.UTC), "2023-01-01T12:00:00Z"),
        (datetime.datetime(2023, 1, 1, 12, 0, 0), "2023-01-01T12:00:00Z"),  # Naive datetime  # noqa: DTZ001
        (datetime.date(2023, 1, 1), "2023-01-01"),
        ("simple string", "simple string"),
        (123, "123"),
        (123.45, "123.45"),
        (True, "True"),
        (None, "None"),  # Note: msgspec might handle None differently, but _default should return "None"
    ],
)
def test_default_encoder_hook(value: Any, expected_output: Any) -> None:
    """Test the _default hook for msgspec encoder."""
    result = serialization._default(value)
    if callable(expected_output):
        assert expected_output(result)
    else:
        assert result == expected_output


def test_default_encoder_hook_raises() -> None:
    """Test that _default raises TypeError for non-serializable objects."""
    with pytest.raises(TypeError):
        serialization._default(NonSerializable())


@pytest.mark.parametrize(
    ("value", "expected_json_fragment"),
    [
        ({"a": 1, "b": "test"}, b'{"a":1,"b":"test"}'),
        ([1, "a", True], b'[1,"a",true]'),
        (SimpleModel(key="data", value=42), b'"{\\"key\\": \\"data\\", \\"value\\": 42}"'),  # Encodes model dump str
        (uuid4(), lambda v: b'"' in v and len(v) == 38),  # Check for quoted UUID string bytes
        (datetime.datetime(2024, 5, 1, 10, 30, 0, tzinfo=datetime.UTC), b'"2024-05-01T10:30:00Z"'),
        (datetime.date(2024, 5, 1), b'"2024-05-01"'),
        ("a string", b'"a string"'),
        (1234, b"1234"),
        (56.78, b"56.78"),
        (True, b"true"),
        (None, b"null"),  # msgspec encodes None as null
        (b"already bytes", b"already bytes"),  # Should return bytes directly
    ],
)
def test_to_json(value: Any, expected_json_fragment: bytes | Callable[[bytes], bool]) -> None:
    """Test the to_json function."""
    encoded = serialization.to_json(value)
    assert isinstance(encoded, bytes)
    if callable(expected_json_fragment):
        assert expected_json_fragment(encoded)
    # Using contains check because exact output might vary slightly (e.g., dict order)
    # For primitives and known structures, we can be more exact.
    elif isinstance(value, (dict, list, str, int, float, bool, bytes, type(None))):
        assert encoded == expected_json_fragment
    else:
        # For complex types handled by _default, check fragment presence
        assert expected_json_fragment in encoded


@pytest.mark.parametrize(
    ("json_input", "expected_value"),
    [
        (b'{"a":1,"b":"test"}', {"a": 1, "b": "test"}),
        (b'[1,"a",true]', [1, "a", True]),
        (b'"a string"', "a string"),
        (b"1234", 1234),
        (b"56.78", 56.78),
        (b"true", True),
        (b"null", None),
        ('{"c": null}', {"c": None}),  # Test with string input
    ],
)
def test_from_json(json_input: bytes | str, expected_value: Any) -> None:
    """Test the from_json function."""
    decoded = serialization.from_json(json_input)
    assert decoded == expected_value


@pytest.mark.parametrize(
    ("dt_input", "expected_iso"),
    [
        (datetime.datetime(2023, 10, 26, 14, 30, 5, tzinfo=datetime.UTC), "2023-10-26T14:30:05Z"),
        (datetime.datetime(2023, 10, 26, 14, 30, 5), "2023-10-26T14:30:05Z"),  # Naive  # noqa: DTZ001
        (
            datetime.datetime(2023, 10, 26, 10, 30, 5, tzinfo=datetime.timezone(datetime.timedelta(hours=-4))),
            "2023-10-26T14:30:05Z",
        ),  # Different timezone
    ],
)
def test_convert_datetime_to_gmt_iso(dt_input: datetime.datetime, expected_iso: str) -> None:
    """Test convert_datetime_to_gmt_iso."""
    assert serialization.convert_datetime_to_gmt_iso(dt_input) == expected_iso


@pytest.mark.parametrize(
    ("date_input", "expected_iso"),
    [
        (datetime.date(2023, 10, 26), "2023-10-26"),
        (datetime.date(1999, 1, 1), "1999-01-01"),
    ],
)
def test_convert_date_to_iso(date_input: datetime.date, expected_iso: str) -> None:
    """Test convert_date_to_iso."""
    assert serialization.convert_date_to_iso(date_input) == expected_iso
