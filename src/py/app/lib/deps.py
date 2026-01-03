"""Application dependency providers generators.

This module contains functions to create dependency providers for services and filters.

You should not have modify this module very often and should only be invoked under normal usage.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, overload

from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_dependencies,
    create_service_provider,
)

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from saq import Queue
    from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
S = TypeVar("S", bound="_ServiceWithSession")


class _ServiceWithSession(Protocol):
    def __init__(self, *, session: AsyncSession) -> None: ...

# Type alias for cleaner overload signatures
ServiceProvider = Callable[["AsyncSession"], AsyncGenerator[T, None]]

__all__ = (
    "CompositeServiceMixin",
    "create_filter_dependencies",
    "create_service_dependencies",
    "create_service_provider",
    "get_task_queue",
    "provide_services",
)


async def get_task_queue() -> Queue:
    """Get Queues

    Returns:
        dict[str,Queue]: A list of queues
    """
    from app.server import plugins

    task_queues = plugins.saq.get_queue("background-tasks")
    await task_queues.connect()

    return task_queues


# Overloads for 1-5 providers - Python's type system requires this for proper inference
# (Similar to how asyncio.gather handles variadic typing)
@overload
def provide_services(
    p1: ServiceProvider[T1],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AbstractAsyncContextManager[tuple[T1]]: ...
@overload
def provide_services(
    p1: ServiceProvider[T1],
    p2: ServiceProvider[T2],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AbstractAsyncContextManager[tuple[T1, T2]]: ...
@overload
def provide_services(
    p1: ServiceProvider[T1],
    p2: ServiceProvider[T2],
    p3: ServiceProvider[T3],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AbstractAsyncContextManager[tuple[T1, T2, T3]]: ...
@overload
def provide_services(
    p1: ServiceProvider[T1],
    p2: ServiceProvider[T2],
    p3: ServiceProvider[T3],
    p4: ServiceProvider[T4],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AbstractAsyncContextManager[tuple[T1, T2, T3, T4]]: ...
@overload
def provide_services(
    p1: ServiceProvider[T1],
    p2: ServiceProvider[T2],
    p3: ServiceProvider[T3],
    p4: ServiceProvider[T4],
    p5: ServiceProvider[T5],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AbstractAsyncContextManager[tuple[T1, T2, T3, T4, T5]]: ...


@asynccontextmanager
async def provide_services(
    *providers: Callable[[AsyncSession], AsyncGenerator[Any, None]],
    session: AsyncSession | None = None,
    connection: ASGIConnection[Any, Any, Any, Any] | None = None,
) -> AsyncIterator[tuple[Any, ...]]:
    """Provide multiple services sharing the same database session.

    This context manager simplifies acquiring services outside of Litestar's
    dependency injection context (background jobs, CLI commands, event handlers,
    and authentication guards).

    Args:
        *providers: One or more service provider functions created via
            ``create_service_provider()``. Each provider should accept an
            AsyncSession and yield a service instance.
        session: Optional pre-existing database session. If provided, the
            session lifecycle is NOT managed by this context manager. The
            caller is responsible for session cleanup.
        connection: Optional ASGI connection for request-scoped contexts.
            Used in authentication guards to obtain the session from the
            request scope via ``alchemy.provide_session()``.

    Yields:
        A tuple of instantiated services, matching the order of providers
        passed as arguments.

    Raises:
        ValueError: If both ``session`` and ``connection`` are provided,
            or if no providers are given.

    Examples:
        Standalone context (jobs, CLI, events) - auto-creates session::

            async with provide_services(
                provide_email_verification_service,
                provide_password_reset_service,
            ) as (verification_service, reset_service):
                await verification_service.cleanup_expired_tokens()
                await reset_service.cleanup_expired_tokens()

        Request context (guards) - uses connection-scoped session::

            async with provide_services(
                provide_users_service,
                connection=connection,
            ) as (users_service,):
                user = await users_service.get_one_or_none(email=token.sub)

        Explicit session - caller manages lifecycle::

            async with alchemy.get_session() as db_session:
                async with provide_services(
                    provide_users_service,
                    session=db_session,
                ) as (users_service,):
                    await users_service.create(data=user_data)
                # Additional operations with db_session...
    """
    from app.config import alchemy

    # Validate inputs
    if session is not None and connection is not None:
        msg = "Cannot provide both 'session' and 'connection' - choose one"
        raise ValueError(msg)

    if not providers:
        msg = "At least one service provider is required"
        raise ValueError(msg)

    # Route to appropriate session source
    if session is not None:
        # External session provided - don't manage lifecycle
        services = tuple([await anext(provider(session)) for provider in providers])
        yield services
    elif connection is not None:
        # Request context - get session from connection scope (lifecycle managed by Litestar)
        db_session = alchemy.provide_session(connection.app.state, connection.scope)
        services = tuple([await anext(provider(db_session)) for provider in providers])
        yield services
    else:
        # Standalone context - create and manage session lifecycle
        async with alchemy.get_session() as db_session:
            services = tuple([await anext(provider(db_session)) for provider in providers])
            yield services


class CompositeServiceMixin:
    """Mixin for services that orchestrate multiple repositories.

    Provides lazy instantiation of dependent services that share
    the parent service's database session.

    Example:
        ```python
        from app.lib.deps import CompositeServiceMixin

        class UserService(CompositeServiceMixin, SQLAlchemyAsyncRepositoryService[m.User]):
            @property
            def oauth_accounts(self) -> UserOAuthAccountService:
                return self._get_service(UserOAuthAccountService)

            async def authenticate_oauth_user(self, ...) -> m.User:
                await self.oauth_accounts.create_or_update_oauth_account(...)
        ```
    """

    _service_cache: dict[type, Any]

    def _get_service(self, service_cls: type[S]) -> S:
        """Get or create a dependent service instance.

        Args:
            service_cls: The service class to instantiate.

        Returns:
            Cached service instance sharing this service's session.
        """
        if not hasattr(self, "_service_cache"):
            self._service_cache = {}

        if service_cls not in self._service_cache:
            self._service_cache[service_cls] = service_cls(session=self.repository.session)  # type: ignore[arg-type]

        return self._service_cache[service_cls]
