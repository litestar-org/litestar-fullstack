from __future__ import annotations

import logging
import re
import sys
from functools import lru_cache
from inspect import isawaitable
from typing import TYPE_CHECKING

import structlog
from litestar.data_extractors import ConnectionDataExtractor, ResponseDataExtractor
from litestar.enums import ScopeType
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.utils.empty import value_or_default
from litestar.utils.scope.state import ScopeState
from structlog.contextvars import bind_contextvars

from app.lib.exceptions import ApplicationError
from app.lib.settings import get_settings
from app.utils import serialization

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Literal

    from litestar.connection import Request
    from litestar.types.asgi_types import ASGIApp, Message, Receive, Scope, Send
    from structlog.types import EventDict, WrappedLogger
    from structlog.typing import Processor

LOGGER = structlog.getLogger()

HTTP_RESPONSE_START: Literal["http.response.start"] = "http.response.start"
HTTP_RESPONSE_BODY: Literal["http.response.body"] = "http.response.body"
REQUEST_BODY_FIELD: Literal["body"] = "body"

settings = get_settings()


@lru_cache
def is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


def structlog_json_serializer(value: EventDict, **_: Any) -> bytes:
    return serialization.to_json(value)


def stdlib_json_serializer(value: EventDict, **_: Any) -> str:  # pragma: no cover
    return serialization.to_json(value).decode("utf-8")


def add_google_cloud_attributes(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Add additional formatting to the log message so that it is parsed on Google Cloud.

    Args:
        _: Wrapped logger object.
        __: Name of the wrapped method, e.g., "info", "warning", etc.
        event_dict: Current context with current event, e.g, `{"a": 42, "event": "foo"}`.

    Returns:
        `event_dict` for further processing if it does not represent a successful health check.
    """
    event_dict["severity"] = event_dict.get("level")
    event_dict["labels"] = None
    event_dict["resource"] = None
    if event_dict.get("logger"):
        event_dict["python_logger"] = event_dict.pop("logger")
    return event_dict


class EventFilter:
    """Remove keys from the log event.

    Add an instance to the processor chain.

    Examples:
        structlog.configure(
            ...,
            processors=[
                ...,
                EventFilter(["color_message"]),
                ...,
            ]
        )
    """

    def __init__(self, filter_keys: Iterable[str]) -> None:
        """Event filter.

        Args:
        filter_keys: Iterable of string keys to be excluded from the log event.
        """
        self.filter_keys = filter_keys

    def __call__(self, _: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
        """Receive the log event, and filter keys.

        Args:
            _ ():
            __ ():
            event_dict (): The data to be logged.

        Returns:
            The log event with any key in `self.filter_keys` removed.
        """
        for key in self.filter_keys:
            event_dict.pop(key, None)
        return event_dict


# This is so that it shows up properly in the litestar ui.  instead of reading `middleware_factory`, we use something that make sense.
def StructlogMiddleware(app: ASGIApp) -> ASGIApp:  # noqa: N802
    """Middleware to ensure that every request has a clean structlog context.

    Args:
        app: The previous ASGI app in the call chain.

    Returns:
        A new ASGI app that cleans the structlog contextvars.
    """

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        """Clean up structlog contextvars.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive handler.
            send: ASGI send handler.
        """
        structlog.contextvars.clear_contextvars()
        await app(scope, receive, send)

    return middleware


def after_exception_hook_handler(exc: Exception, _scope: Scope) -> None:
    """Binds `exc_info` key with exception instance as value to structlog
    context vars.

    This must be a coroutine so that it is not wrapped in a thread where we'll lose context.

    Args:
        exc: the exception that was raised.
        _scope: scope of the request
    """
    if isinstance(exc, ApplicationError):
        return
    if isinstance(exc, HTTPException) and exc.status_code < HTTP_500_INTERNAL_SERVER_ERROR:
        return
    bind_contextvars(exc_info=sys.exc_info())


class BeforeSendHandler:
    """Extraction of request and response data from connection scope."""

    __slots__ = (
        "do_log_request",
        "do_log_response",
        "exclude_paths",
        "include_compressed_body",
        "logger",
        "request_extractor",
        "response_extractor",
    )

    def __init__(self) -> None:
        """Configure the handler."""
        self.exclude_paths = re.compile(settings.log.EXCLUDE_PATHS)
        self.do_log_request = bool(settings.log.REQUEST_FIELDS)
        self.do_log_response = bool(settings.log.RESPONSE_FIELDS)
        self.include_compressed_body = settings.log.INCLUDE_COMPRESSED_BODY
        self.request_extractor = ConnectionDataExtractor(
            extract_body="body" in settings.log.REQUEST_FIELDS,
            extract_client="client" in settings.log.REQUEST_FIELDS,
            extract_content_type="content_type" in settings.log.REQUEST_FIELDS,
            extract_cookies="cookies" in settings.log.REQUEST_FIELDS,
            extract_headers="headers" in settings.log.REQUEST_FIELDS,
            extract_method="method" in settings.log.REQUEST_FIELDS,
            extract_path="path" in settings.log.REQUEST_FIELDS,
            extract_path_params="path_params" in settings.log.REQUEST_FIELDS,
            extract_query="query" in settings.log.REQUEST_FIELDS,
            extract_scheme="scheme" in settings.log.REQUEST_FIELDS,
            obfuscate_cookies=settings.log.OBFUSCATE_COOKIES,
            obfuscate_headers=settings.log.OBFUSCATE_HEADERS,
            parse_body=False,
            parse_query=False,
        )
        self.response_extractor = ResponseDataExtractor(
            extract_body="body" in settings.log.RESPONSE_FIELDS,
            extract_headers="headers" in settings.log.RESPONSE_FIELDS,
            extract_status_code="status_code" in settings.log.RESPONSE_FIELDS,
            obfuscate_cookies=settings.log.OBFUSCATE_COOKIES,
            obfuscate_headers=settings.log.OBFUSCATE_HEADERS,
        )

    async def __call__(self, message: Message, scope: Scope) -> None:
        """Receives ASGI response messages and scope, and logs per
        configuration.

        Args:
            message: ASGI response event.
            scope: ASGI connection scope.
        """
        if scope["type"] == ScopeType.HTTP and self.exclude_paths.findall(scope["path"]):
            return

        if message["type"] == HTTP_RESPONSE_START:
            scope["state"]["log_level"] = (
                logging.ERROR if message["status"] >= HTTP_500_INTERNAL_SERVER_ERROR else logging.INFO
            )
            scope["state"][HTTP_RESPONSE_START] = message
        # ignore intermediate content of streaming responses for now.
        elif message["type"] == HTTP_RESPONSE_BODY and message["more_body"] is False:
            scope["state"][HTTP_RESPONSE_BODY] = message
            try:
                if self.do_log_request:
                    await self.log_request(scope)
                if self.do_log_response:
                    await self.log_response(scope)
                await LOGGER.alog(
                    scope["state"]["log_level"],
                    f"{scope['method'] if scope['type'] == ScopeType.HTTP else scope['type']} {scope['path']}",
                )
            # RuntimeError: Expected ASGI message 'http.response.body', but got 'http.response.start'.
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
                # just in-case something in the context causes the error
                structlog.contextvars.clear_contextvars()
                await LOGGER.aerror("Error in logging before-send handler!", reason=f"{type(e).__name__}{e.args}")

    async def log_request(self, scope: Scope) -> None:
        """Handle extracting the request data and logging the message.

        Args:
            scope: The ASGI connection scope.
        """
        extracted_data = await self.extract_request_data(request=scope["app"].request_class(scope))  # pyright: ignore
        structlog.contextvars.bind_contextvars(**extracted_data)

    async def log_response(self, scope: Scope) -> None:
        """Handle extracting the response data and logging the message.

        Args:
            scope: The ASGI connection scope.
        """
        extracted_data = self.extract_response_data(scope=scope)
        structlog.contextvars.bind_contextvars(**extracted_data)

    async def extract_request_data(self, request: Request[Any, Any, Any]) -> dict[str, Any]:
        """Create a dictionary of values for the log.

        Args:
            request: A request instance.

        Raises:
            RuntimeError:

        Returns:
            An OrderedDict.
        """
        data: dict[str, Any] = {}
        extracted_data = self.request_extractor(connection=request)
        missing = object()
        for key in settings.log.REQUEST_FIELDS:
            value = extracted_data.get(key, missing)
            if value is missing:  # pragma: no cover
                continue
            if isawaitable(value):
                # Prevent Litestar from raising a RuntimeError
                # when trying to read an empty request body.
                try:
                    value = await value
                except RuntimeError:
                    if key != REQUEST_BODY_FIELD:
                        raise  # pragma: no cover
                    value = None
            data[key] = value
        return data

    def extract_response_data(self, scope: Scope) -> dict[str, Any]:
        """Extract data from the response.

        Args:
            scope: The ASGI connection scope.

        Returns:
            An OrderedDict.
        """
        data: dict[str, Any] = {}
        extracted_data = self.response_extractor(
            messages=(scope["state"][HTTP_RESPONSE_START], scope["state"][HTTP_RESPONSE_BODY]),
        )
        missing = object()
        connection_state = ScopeState.from_scope(scope)
        response_body_compressed = value_or_default(connection_state.response_compressed, False)
        for key in settings.log.RESPONSE_FIELDS:
            value = extracted_data.get(key, missing)
            if key == "body" and response_body_compressed and not self.include_compressed_body:
                continue
            if value is missing:  # pragma: no cover
                continue
            data[key] = value
        return data


def structlog_processors(as_json: bool) -> list[Processor]:
    """Set the default processors for structlog.

    Returns:
        An optional list of processors.
    """
    try:
        import structlog
        from structlog.dev import RichTracebackFormatter

        if as_json:
            return [
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.format_exc_info,
                add_google_cloud_attributes,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(serializer=structlog_json_serializer),
            ]
        return [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=RichTracebackFormatter(max_frames=1, show_locals=False, width=80)
            ),
        ]
    except ImportError:
        return []


def stdlib_logger_processors(as_json: bool) -> list[Processor]:
    """Set the default processors for structlog stdlib.

    Returns:
        An optional list of processors.
    """
    try:
        import structlog
        from structlog.dev import RichTracebackFormatter

        if as_json:
            return [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.stdlib.ExtraAdder(),
                EventFilter(["color_message"]),
                structlog.processors.EventRenamer("message"),
                add_google_cloud_attributes,
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(serializer=stdlib_json_serializer),
            ]
        return [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.ExtraAdder(),
            EventFilter(["color_message"]),
            EventFilter(["message"]),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=RichTracebackFormatter(max_frames=1, show_locals=False, width=80)
            ),
        ]
    except ImportError:
        return []
