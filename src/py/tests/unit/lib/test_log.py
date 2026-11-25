from __future__ import annotations

from app.lib.log import (
    EventFilter,
    add_google_cloud_attributes,
    is_tty,
    stdlib_json_serializer,
    stdlib_logger_processors,
    structlog_json_serializer,
    structlog_processors,
)


def test_is_tty() -> None:
    assert isinstance(is_tty(), bool)


def test_structlog_json_serializer() -> None:
    event_dict = {"event": "test", "level": "info"}
    result = structlog_json_serializer(event_dict)
    assert isinstance(result, bytes)
    assert b"test" in result


def test_stdlib_json_serializer() -> None:
    event_dict = {"event": "test", "level": "info"}
    result = stdlib_json_serializer(event_dict)
    assert isinstance(result, str)
    assert "test" in result


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


def test_structlog_processors_json() -> None:
    processors = structlog_processors(as_json=True)
    assert len(processors) > 0
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
