from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.lib.log import (
    EventFilter,
    StructlogMiddleware,
    add_google_cloud_attributes,
    after_exception_hook_handler,
    is_tty,
    stdlib_logger_processors,
    structlog_json_serializer,
    structlog_processors,
)

pytestmark = pytest.mark.anyio

if TYPE_CHECKING:
    from litestar.types import Scope


def test_is_tty() -> None:
    # This might vary based on environment, but we can check it runs
    assert isinstance(is_tty(), bool)


def test_structlog_json_serializer() -> None:
    event_dict = {"event": "test", "level": "info"}
    result = structlog_json_serializer(event_dict)
    assert isinstance(result, bytes)
    assert b"test" in result


def test_add_google_cloud_attributes() -> None:
    event_dict = {"event": "test", "level": "info", "logger": "app"}
    result = add_google_cloud_attributes(None, "info", event_dict)
    assert result["severity"] == "info"
    assert result["python_logger"] == "app"
    assert "logger" not in result


def test_event_filter() -> None:
    filter_keys = ["secret", "token"]
    event_dict = {"event": "test", "secret": "123", "token": "abc", "other": "keep"}
    ef = EventFilter(filter_keys)
    result = ef(None, "info", event_dict)
    assert "secret" not in result
    assert "token" not in result
    assert result["other"] == "keep"


async def test_structlog_middleware() -> None:
    app = AsyncMock()
    middleware = StructlogMiddleware(app)
    scope = cast("Scope", {"type": "http"})
    receive = MagicMock()
    send = MagicMock()

    with patch("structlog.contextvars.clear_contextvars") as mock_clear:
        await middleware(scope, receive, send)
        mock_clear.assert_called_once()
        app.assert_called_once_with(scope, receive, send)


def test_after_exception_hook_handler() -> None:
    exc = ValueError("test")
    scope = cast("Scope", {"type": "http"})
    with patch("app.lib.log.bind_contextvars") as mock_bind:
        after_exception_hook_handler(exc, scope)
        mock_bind.assert_called_once()


def test_structlog_processors_json() -> None:
    processors = structlog_processors(as_json=True)
    assert len(processors) > 0
    # Check if JSONRenderer is the last one (usually)
    assert any("JSONRenderer" in str(p) for p in processors)


def test_structlog_processors_console() -> None:
    processors = structlog_processors(as_json=False)
    assert len(processors) > 0
    assert any("ConsoleRenderer" in str(p) for p in processors)


def test_stdlib_logger_processors_json() -> None:
    processors = stdlib_logger_processors(as_json=True)
    assert len(processors) > 0


def test_stdlib_logger_processors_console() -> None:
    processors = stdlib_logger_processors(as_json=False)
    assert len(processors) > 0
