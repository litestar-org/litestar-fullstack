"""Application exception types and their translation into HTTP error responses."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

from advanced_alchemy.exceptions import DuplicateKeyError, IntegrityError
from litestar.exceptions import (
    ClientException,
    HTTPException,
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.exceptions.responses import (
    create_debug_response as _create_debug_response,  # pyright: ignore[reportUnknownVariableType]
)
from litestar.plugins.problem_details import ProblemDetailsException
from litestar.repository.exceptions import ConflictError, NotFoundError, RepositoryError
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.connection import Request
    from litestar.response import Response

__all__ = ("ApplicationError", "AuthorizationError")


class ApplicationError(Exception):
    """Base exception type for the lib's custom exception types."""

    detail: str

    def __init__(self, *args: Any, detail: str = "") -> None:
        """Initialize ``ApplicationError``.

        Args:
            *args: Messages, converted to :class:`str` before passing to :class:`Exception`. The first one
                becomes ``detail`` when ``detail`` is not given.
            detail: detail of the exception.
        """
        messages = [str(message) for message in args if message]
        if not detail:
            if messages:
                detail, *messages = messages
            elif hasattr(self, "detail"):
                detail = self.detail
        self.detail = detail
        super().__init__(*messages)

    def __repr__(self) -> str:
        if self.detail:
            return f"{self.__class__.__name__} - {self.detail}"
        return self.__class__.__name__

    def __str__(self) -> str:
        return " ".join((*self.args, self.detail)).strip()


class ApplicationClientError(ApplicationError):
    """Base exception type for client errors."""


class AuthorizationError(ApplicationClientError):
    """A user tried to do something they shouldn't have."""


def create_debug_response(request: Request[Any, Any, Any], exc: Exception) -> Response[Any]:
    return cast("Callable[[Any, Exception], Response[Any]]", _create_debug_response)(request, exc)


def to_problem_details(exc: HTTPException) -> ProblemDetailsException:
    """Describe an HTTP error as the RFC 9457 problem every error response of the application carries.

    ``title`` is the reason phrase of the status and ``detail`` is the human-readable message. A mapping in
    ``extra`` becomes top-level members of the problem. The message of a 500 is replaced by the reason
    phrase so internal failures are not disclosed.

    Returns:
        Problem details exception whose response is ``application/problem+json``.
    """
    title = HTTPStatus(exc.status_code).phrase
    return ProblemDetailsException(
        status_code=exc.status_code,
        title=title,
        detail=title if exc.status_code == HTTP_500_INTERNAL_SERVER_ERROR else exc.detail,
        extra=exc.extra,
        headers=exc.headers,
    )


def exception_to_http_response(request: Request[Any, Any, Any], exc: Exception) -> Response[Any]:
    """Translate an application or repository exception into its problem details response.

    Args:
        request: The request that experienced the exception.
        exc: Exception raised during handling of the request.

    Returns:
        Problem details response for the matching HTTP status, or the debug page in debug mode for
        anything other than not-found and authorization errors.
    """
    http_exc: type[HTTPException]
    if isinstance(exc, NotFoundError):
        http_exc = NotFoundException
    elif isinstance(exc, ConflictError | RepositoryError | IntegrityError | DuplicateKeyError):
        http_exc = _HTTPConflictException
    elif isinstance(exc, AuthorizationError):
        http_exc = PermissionDeniedException
    elif isinstance(exc, ApplicationClientError):
        http_exc = ClientException
    else:
        http_exc = InternalServerException
    if request.app.debug and http_exc not in {PermissionDeniedException, NotFoundException}:
        return create_debug_response(request, exc)
    detail = getattr(exc, "detail", "") or (str(exc.__cause__) if exc.__cause__ else str(exc))
    return to_problem_details(http_exc(detail=detail)).to_response(request)


class _HTTPConflictException(HTTPException):
    """Request conflict with the current state of the target resource."""

    status_code = HTTP_409_CONFLICT
