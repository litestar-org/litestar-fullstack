"""Logging config for the application.

Ensures that the app, sqlalchemy, saq and uvicorn loggers all log through the queue listener.

Adds a filter for health check route logs.
"""
from __future__ import annotations

import logging
import re
from inspect import isawaitable
from typing import TYPE_CHECKING

import structlog
from litestar.constants import SCOPE_STATE_RESPONSE_COMPRESSED
from litestar.data_extractors import ConnectionDataExtractor, ResponseDataExtractor
from litestar.enums import ScopeType
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_300_MULTIPLE_CHOICES,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.utils.scope import get_litestar_scope_state

from app.lib import constants, settings

__all__ = ["BeforeSendHandler", "drop_health_logs", "middleware_factory"]


if TYPE_CHECKING:
    from typing import Any, Literal

    from litestar.connection import Request
    from litestar.types.asgi_types import ASGIApp, Message, Receive, Scope, Send
    from structlog.types import EventDict, WrappedLogger

LOGGER = structlog.get_logger()

HTTP_RESPONSE_START: Literal["http.response.start"] = "http.response.start"
HTTP_RESPONSE_BODY: Literal["http.response.body"] = "http.response.body"
REQUEST_BODY_FIELD: Literal["body"] = "body"


def drop_health_logs(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Prevent logging of successful health checks.

    Args:
        _: Wrapped logger object.
        __: Name of the wrapped method, e.g., "info", "warning", etc.
        event_dict: Current context with current event, e.g, `{"a": 42, "event": "foo"}`.

    Returns:
        `event_dict` for further processing if it does not represent a successful health check.
    """
    is_http_log = event_dict["event"] == settings.log.HTTP_EVENT
    is_health_log = event_dict.get("request", {}).get("path") == constants.SYSTEM_HEALTH
    is_success_status = HTTP_200_OK <= event_dict.get("response", {}).get("status_code", 0) < HTTP_300_MULTIPLE_CHOICES
    if is_http_log and is_health_log and is_success_status:
        raise structlog.DropEvent
    return event_dict


def middleware_factory(app: ASGIApp) -> ASGIApp:
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
                await LOGGER.alog(scope["state"]["log_level"], settings.log.HTTP_EVENT)
            # RuntimeError: Expected ASGI message 'http.response.body', but got 'http.response.start'.
            except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-except
                # just in-case something in the context causes the error
                structlog.contextvars.clear_contextvars()
                await LOGGER.aerror("Error in logging before-send handler!", exc_info=exc)

    async def log_request(self, scope: Scope) -> None:
        """Handle extracting the request data and logging the message.

        Args:
            scope: The ASGI connection scope.

        Returns:
            None
        """
        extracted_data = await self.extract_request_data(request=scope["app"].request_class(scope))
        structlog.contextvars.bind_contextvars(request=extracted_data)

    async def log_response(self, scope: Scope) -> None:
        """Handle extracting the response data and logging the message.

        Args:
            scope: The ASGI connection scope.

        Returns:
            None
        """
        extracted_data = self.extract_response_data(scope=scope)
        structlog.contextvars.bind_contextvars(response=extracted_data)

    async def extract_request_data(self, request: Request) -> dict[str, Any]:
        """Create a dictionary of values for the log.

        Args:
            request: A [Request][litestar.connection.request.Request] instance.

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
        response_body_compressed = get_litestar_scope_state(scope, SCOPE_STATE_RESPONSE_COMPRESSED)
        for key in settings.log.RESPONSE_FIELDS:
            value = extracted_data.get(key, missing)
            if key == "body" and response_body_compressed and not self.include_compressed_body:
                continue
            if value is missing:  # pragma: no cover
                continue
            data[key] = value
        return data
