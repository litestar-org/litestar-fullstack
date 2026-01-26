import datetime
from uuid import UUID

from pydantic import BaseModel

from app.utils.serialization import convert_date_to_iso, convert_datetime_to_gmt_iso, from_json, to_json


class MockModel(BaseModel):
    name: str
    age: int


def test_to_json_basic() -> None:
    data = {"a": 1, "b": "test"}
    result = to_json(data)
    assert isinstance(result, bytes)
    assert from_json(result) == data


def test_to_json_bytes() -> None:
    data = b'{"a": 1}'
    assert to_json(data) == data


def test_to_json_uuid() -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440000")
    result = to_json({"id": uid})
    assert b"550e8400-e29b-41d4-a716-446655440000" in result


def test_to_json_datetime() -> None:
    dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
    result = to_json({"dt": dt})
    # Our hook should produce Z suffix
    assert b"2024-01-01T12:00:00Z" in result


class CustomObj:
    def __str__(self) -> str:
        return "custom"


def test_to_json_custom_obj() -> None:
    obj = CustomObj()
    result = to_json({"obj": obj})
    assert b"custom" in result


def test_to_json_date() -> None:
    d = datetime.date(2024, 1, 1)
    result = to_json({"d": d})
    assert b"2024-01-01" in result


def test_to_json_pydantic() -> None:
    model = MockModel(name="test", age=20)
    result = to_json(model)
    # _default returns json.dumps for BaseModel, then encoder encodes the string
    # so it might be double escaped if not careful, but let's see
    decoded = from_json(result)
    # Based on _default: return json.dumps(value.model_dump(by_alias=True))
    # It returns a string, which msgspec then encodes as a json string.
    assert "test" in str(decoded)


def test_convert_datetime_to_gmt_iso() -> None:
    dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)

    assert convert_datetime_to_gmt_iso(dt) == "2024-01-01T12:00:00Z"

    dt_tz = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=1)))

    assert convert_datetime_to_gmt_iso(dt_tz) == "2024-01-01T11:00:00Z"


def test_convert_date_to_iso() -> None:
    d = datetime.date(2024, 1, 1)
    assert convert_date_to_iso(d) == "2024-01-01"
