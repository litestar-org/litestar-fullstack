import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from app.utils import env


@pytest.mark.parametrize(
    ("key", "env_value", "default", "expected_value", "type_hint"),
    [
        # Basic types - Env var set
        ("TEST_STR", "hello", "default", "hello", env._UNSET),
        ("TEST_INT", "123", 0, 123, env._UNSET),
        ("TEST_BOOL_TRUE1", "True", False, True, env._UNSET),
        ("TEST_BOOL_TRUE2", "true", False, True, env._UNSET),
        ("TEST_BOOL_TRUE3", "1", False, True, env._UNSET),
        ("TEST_BOOL_TRUE4", "yes", False, True, env._UNSET),
        ("TEST_BOOL_FALSE1", "False", True, False, env._UNSET),
        ("TEST_BOOL_FALSE2", "no", True, False, env._UNSET),
        ("TEST_BOOL_FALSE3", "0", True, False, env._UNSET),
        ("TEST_PATH", "/tmp/test", Path("/default"), Path("/tmp/test"), env._UNSET),  # noqa: S108
        # List types - Env var set
        ("TEST_LIST_STR_COMMA", "a, b, c", [], ["a", "b", "c"], env._UNSET),
        ("TEST_LIST_STR_JSON", '["x", "y", "z"]', [], ["x", "y", "z"], env._UNSET),
        ("TEST_LIST_PATH_COMMA", "/a, /b, /c", [], [Path("/a"), Path("/b"), Path("/c")], env._UNSET),
        ("TEST_LIST_PATH_JSON", '["/x", "/y", "/z"]', [], [Path("/x"), Path("/y"), Path("/z")], env._UNSET),
        # Basic types - Env var not set (use default)
        ("TEST_STR_DEFAULT", None, "default_val", "default_val", env._UNSET),
        ("TEST_INT_DEFAULT", None, 999, 999, env._UNSET),
        ("TEST_BOOL_DEFAULT", None, True, True, env._UNSET),
        ("TEST_PATH_DEFAULT", None, Path("/default/path"), Path("/default/path"), env._UNSET),
        ("TEST_LIST_STR_DEFAULT", None, ["d1", "d2"], ["d1", "d2"], env._UNSET),
        ("TEST_LIST_PATH_DEFAULT", None, [Path("/d1"), Path("/d2")], [Path("/d1"), Path("/d2")], env._UNSET),
        ("TEST_NONE_DEFAULT", None, None, None, env._UNSET),
        # Type hint usage
        ("TEST_HINT_STR", "123", 0, "123", str),  # Default is int, hint is str
        ("TEST_HINT_INT", "456", "0", 456, int),  # Default is str, hint is int
        ("TEST_HINT_BOOL", "true", "false", True, bool),  # Default is str, hint is bool
        ("TEST_HINT_PATH", "/hint/path", "/default", Path("/hint/path"), Path),  # Default is str, hint is Path
        ("TEST_HINT_LIST_STR", "a,b", [], ["a", "b"], list[str]),
        ("TEST_HINT_LIST_PATH", "/a,/b", [], [Path("/a"), Path("/b")], list[Path]),
        ("TEST_HINT_DEFAULT_USED", None, "default_hint", "default_hint", str),  # Env not set, use default with hint
    ],
)
def test_get_config_val(key: str, env_value: str | None, default: Any, expected_value: Any, type_hint: Any) -> None:
    """Test get_config_val function with various inputs and types."""
    env_vars = {key: env_value} if env_value is not None else {}
    with patch.dict(os.environ, env_vars, clear=True):
        result = env.get_config_val(key, default=default, type_hint=type_hint)
        assert result == expected_value
        # Check type consistency, especially important for lists/paths
        if expected_value is not None:
            assert type(result) is type(expected_value)
            if isinstance(expected_value, list) and expected_value:
                assert type(result[0]) is type(expected_value[0])


@pytest.mark.parametrize(
    ("key", "env_value", "default", "expected_error_msg"),
    [
        ("INVALID_LIST_JSON", '[a,b"', [], "is not a valid list representation."),
        ("INVALID_LIST_PATH_JSON", '["/a","/b"', [], "is not a valid list representation."),
    ],
)
def test_get_config_val_raises(key: str, env_value: str, default: Any, expected_error_msg: str) -> None:
    """Test that get_config_val raises ValueError for invalid list formats."""
    with patch.dict(os.environ, {key: env_value}, clear=True), pytest.raises(ValueError, match=expected_error_msg):
        env.get_config_val(key, default=default)


@pytest.mark.parametrize(
    ("key", "env_value", "default", "expected_value", "type_hint"),
    [
        # Test cases similar to test_get_config_val, focusing on the callable aspect
        ("GET_ENV_STR", "from_env", "default_str", "from_env", env._UNSET),
        ("GET_ENV_INT", "789", 0, 789, env._UNSET),
        ("GET_ENV_BOOL", "false", True, False, env._UNSET),
        ("GET_ENV_DEFAULT", None, "using_default", "using_default", env._UNSET),
        ("GET_ENV_HINT", "99", "0", 99, int),
    ],
)
def test_get_env(key: str, env_value: str | None, default: Any, expected_value: Any, type_hint: Any) -> None:
    """Test get_env returns a callable that correctly retrieves the value."""
    env_vars = {key: env_value} if env_value is not None else {}
    with patch.dict(os.environ, env_vars, clear=True):
        config_callable = env.get_env(key, default=default, type_hint=type_hint)
        assert callable(config_callable)
        result = config_callable()  # type: ignore[no-untyped-call]
        assert result == expected_value
        if expected_value is not None:
            assert type(result) is type(expected_value)
