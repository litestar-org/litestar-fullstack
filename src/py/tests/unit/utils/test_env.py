import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.utils.env import get_config_val


def test_get_config_val_basic() -> None:
    with patch.dict(os.environ, {"STR_VAL": "hello", "INT_VAL": "123", "BOOL_VAL": "true"}):
        assert get_config_val("STR_VAL", default="") == "hello"
        assert get_config_val("INT_VAL", default=0) == 123
        assert get_config_val("BOOL_VAL", default=False) is True
        assert get_config_val("MISSING", default="default") == "default"


def test_get_config_val_path() -> None:
    with patch.dict(os.environ, {"PATH_VAL": "/tmp/test"}):
        result = get_config_val("PATH_VAL", default=Path("/tmp"))
        assert isinstance(result, Path)
        assert str(result) == "/tmp/test"


def test_get_config_val_list_json() -> None:
    with patch.dict(os.environ, {"LIST_VAL": '["a", "b", "c"]'}):
        result = get_config_val("LIST_VAL", default=[], type_hint=list[str])
        assert result == ["a", "b", "c"]


def test_get_config_val_list_comma() -> None:
    with patch.dict(os.environ, {"LIST_VAL": "a,b,c"}):
        result = get_config_val("LIST_VAL", default=[], type_hint=list[str])
        assert result == ["a", "b", "c"]


def test_get_config_val_dict_json() -> None:
    with patch.dict(os.environ, {"DICT_VAL": '{"a": 1, "b": 2}'}):
        result = get_config_val("DICT_VAL", default={}, type_hint=dict[str, str])
        assert result == {"a": "1", "b": "2"}


def test_get_config_val_dict_comma() -> None:
    with patch.dict(os.environ, {"DICT_VAL": "a=1,b=2"}):
        result = get_config_val("DICT_VAL", default={}, type_hint=dict[str, str])
        assert result == {"a": "1", "b": "2"}


def test_get_config_val_invalid_list() -> None:
    with (
        patch.dict(os.environ, {"INVALID_LIST": "[a,b"}),
        pytest.raises(ValueError, match="not a valid list representation"),
    ):
        get_config_val("INVALID_LIST", default=[], type_hint=list[str])


def test_get_config_val_invalid_dict() -> None:
    with (
        patch.dict(os.environ, {"INVALID_DICT": "a"}),
        pytest.raises(TypeError, match="not a valid dict representation"),
    ):
        get_config_val("INVALID_DICT", default={}, type_hint=dict[str, str])
