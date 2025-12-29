# Product Requirements Document: Service Context Manager Helper

**Feature Name**: `provide_services` Context Manager Helper
**Version**: 1.0
**Author**: Claude
**Date**: 2025-12-29
**Status**: Ready for Implementation

---

## 1. Intelligence Context

### 1.1 Complexity Assessment

| Dimension | Value | Rationale |
|-----------|-------|-----------|
| **Overall Complexity** | Medium | Single primary file, multiple update sites |
| **Checkpoint Count** | 8 | New helper + 5 file updates + tests + validation |
| **Risk Level** | Low | Additive change, no breaking modifications |
| **Testing Scope** | Unit + Integration | Mock-based unit tests, DB-backed integration |

### 1.2 Similar Features Referenced

| Reference | Location | Relevance |
|-----------|----------|-----------|
| `create_service_provider` | `advanced_alchemy.extensions.litestar.providers` | Pattern for service instantiation |
| `Service.new()` | `advanced_alchemy.service._async` | Context manager session handling |
| `cleanup_auth_tokens` | `src/py/app/domain/system/jobs.py:15-34` | Multi-service orchestration example |
| `current_user_from_token` | `src/py/app/domain/accounts/guards.py:94-110` | Request-scoped session example |
| `_create_default_roles` | `src/py/app/cli/commands.py:182-200` | CLI session management example |

### 1.3 Patterns to Follow

| Pattern | Description | Application |
|---------|-------------|-------------|
| **Async Context Manager** | `@asynccontextmanager` decorator | Core implementation pattern |
| **Type Overloads** | `@overload` for tuple typing | IDE type inference support |
| **Inner Import** | Import `alchemy` inside function | Circular import prevention |
| **Service Provider** | `create_service_provider` factory | Reuse existing providers |
| **Session Lifecycle** | Owned vs borrowed sessions | Proper cleanup semantics |

---

## 2. Problem Statement

### 2.1 User Problem Being Solved

Developers working on this codebase need to instantiate database services outside of Litestar's HTTP request dependency injection context. This occurs in several scenarios:

1. **Background Jobs**: SAQ workers processing queued tasks need database access for operations like token cleanup, email sending, and data synchronization. These run in separate processes with no HTTP request context.

2. **CLI Commands**: Administrative commands for user management, role assignment, and database maintenance require service instances. Commands run in terminal sessions without web framework infrastructure.

3. **Event Handlers**: Application events (user_created, team_created) trigger business logic that needs database services. While these execute within the application, they operate outside request-response cycles.

4. **Authentication Guards**: JWT token validation requires user lookup from the database. The guard has access to the ASGI connection but must manually wire up service dependencies.

The current approach requires verbose, repetitive boilerplate code at each call site. Developers must remember:
- How to acquire a database session (varies by context)
- The `await anext(provider(session))` pattern to consume async generator providers
- Proper session lifecycle management (when to use context managers)
- Which imports are needed (`alchemy` config, provider functions)

This creates cognitive load, increases likelihood of copy-paste errors, and makes the codebase harder to maintain.

### 2.2 Business Value

| Value Dimension | Impact |
|-----------------|--------|
| **Developer Productivity** | Reduce boilerplate by ~70% per service acquisition |
| **Code Quality** | Consistent pattern eliminates variation |
| **Maintainability** | Centralized session management logic |
| **Onboarding** | Single pattern to learn for out-of-DI contexts |
| **Type Safety** | IDE autocompletion for service methods |
| **Error Prevention** | Compile-time type checking catches misuse |

### 2.3 Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Boilerplate reduction | Multi-service operations go from 4+ lines to 2 lines |
| Pattern adoption | All identified call sites migrated to new helper |
| Type inference | IDE provides correct autocompletion for service methods |
| Test coverage | 90%+ coverage on new helper code |
| Validation | `make check-all` passes after implementation |
| No regressions | Existing functionality unchanged |

---

## 3. Acceptance Criteria

### 3.1 Functional Requirements

#### FR-1: Single Service Acquisition
```gherkin
Given a service provider function
When I use provide_services with one provider
Then I receive a tuple with one service instance
And the service is properly initialized with a database session
```

**Example**:
```python
async with provide_services(provide_users_service) as (users_service,):
    user = await users_service.get_one_or_none(email="test@example.com")
```

#### FR-2: Multiple Service Acquisition
```gherkin
Given multiple service provider functions
When I use provide_services with 2-5 providers
Then I receive a tuple with all service instances in order
And all services share the same database session
```

**Example**:
```python
async with provide_services(
    provide_email_verification_service,
    provide_password_reset_service,
    provide_refresh_token_service,
) as (verification_service, reset_service, refresh_service):
    # All three services share one session
    await verification_service.cleanup_expired_tokens()
    await reset_service.cleanup_expired_tokens()
    await refresh_service.cleanup_expired_tokens()
```

#### FR-3: Standalone Session Mode (Default)
```gherkin
Given no session or connection parameter
When I use provide_services
Then a new database session is created automatically
And the session is closed when the context exits
```

**Example**:
```python
# In a background job (no request context)
async with provide_services(provide_users_service) as (service,):
    await service.create(data=user_data)
# Session automatically closed
```

#### FR-4: Request Context Mode
```gherkin
Given an ASGI connection object
When I use provide_services with connection parameter
Then the session is retrieved from the connection scope
And the session lifecycle is managed by Litestar (not closed by helper)
```

**Example**:
```python
# In an authentication guard
async def current_user_from_token(token: Token, connection: ASGIConnection) -> User | None:
    async with provide_services(provide_users_service, connection=connection) as (service,):
        return await service.get_one_or_none(email=token.sub)
```

#### FR-5: Explicit Session Mode
```gherkin
Given an external AsyncSession object
When I use provide_services with session parameter
Then that session is used for all services
And the session is NOT closed when the context exits
```

**Example**:
```python
# When caller manages session
async with alchemy.get_session() as db_session:
    async with provide_services(provide_users_service, session=db_session) as (service,):
        await service.create(data=data)
    # Do more work with db_session...
```

### 3.2 Error Handling Requirements

#### ER-1: No Providers Error
```gherkin
Given no provider functions passed
When provide_services is called
Then ValueError is raised
And message is "At least one service provider is required"
```

#### ER-2: Conflicting Parameters Error
```gherkin
Given both session and connection parameters
When provide_services is called
Then ValueError is raised
And message is "Cannot provide both 'session' and 'connection' - choose one"
```

#### ER-3: Provider Error Propagation
```gherkin
Given a provider that raises an exception
When provide_services is called
Then the original exception propagates unchanged
And any created sessions are properly cleaned up
```

### 3.3 Type Safety Requirements

#### TS-1: Single Service Type Inference
```python
# IDE should infer: users_service: UserService
async with provide_services(provide_users_service) as (users_service,):
    # Autocompletion for UserService methods works
    pass
```

#### TS-2: Multiple Service Type Inference
```python
# IDE should infer: (users: UserService, roles: RoleService)
async with provide_services(provide_users_service, provide_roles_service) as (users, roles):
    # Autocompletion for both service types works
    pass
```

### 3.4 Edge Cases Handled

| Edge Case | Behavior |
|-----------|----------|
| Empty providers tuple | ValueError raised |
| Both session and connection | ValueError raised |
| Single provider | Works with trailing comma `as (s,):` |
| 5+ providers | Falls back to `tuple[Any, ...]` typing |
| Provider raises during init | Exception propagates, session cleaned up |
| Context exits with exception | Session properly closed in standalone mode |
| Session already closed | Error propagates from SQLAlchemy |

---

## 4. Technical Approach

### 4.1 File Structure Plan

```
src/py/app/lib/deps.py (MODIFIED)
├── Existing imports and re-exports
├── NEW: Type variables (S1-S5) in TYPE_CHECKING block
├── NEW: Overload declarations (5 overloads)
└── NEW: provide_services implementation

src/py/tests/unit/test_deps.py (NEW)
├── TestProvideServices class
│   ├── test_single_provider_standalone
│   ├── test_multiple_providers_standalone
│   ├── test_with_connection
│   ├── test_with_session
│   ├── test_raises_on_both_session_and_connection
│   ├── test_raises_on_no_providers
│   ├── test_session_lifecycle_managed
│   └── test_error_propagation
```

### 4.2 API Specification

#### Function Signature

```python
@asynccontextmanager
async def provide_services(
    *providers: Callable[[AsyncSession], AsyncGenerator[Any, None]],
    session: AsyncSession | None = None,
    connection: ASGIConnection[Any, Any, Any, Any] | None = None,
) -> AsyncGenerator[tuple[Any, ...], None]:
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
```

#### Type Overloads

```python
# 1-provider overload
@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1], None]: ...

# 2-provider overload
@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2], None]: ...

# 3-provider overload
@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    __p3: Callable[[AsyncSession], AsyncGenerator[S3, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2, S3], None]: ...

# 4-provider and 5-provider overloads follow same pattern...
```

### 4.3 Implementation Algorithm

```
1. VALIDATE inputs
   - IF session AND connection both provided:
       RAISE ValueError("Cannot provide both...")
   - IF providers is empty:
       RAISE ValueError("At least one provider...")

2. DETERMINE session source
   - IF session provided:
       db_session = session
       owns_session = False
   - ELIF connection provided:
       db_session = alchemy.provide_session(connection.app.state, connection.scope)
       owns_session = False
   - ELSE:
       owns_session = True

3. INSTANTIATE services
   - IF owns_session:
       async with alchemy.get_session() as db_session:
           services = tuple([await anext(p(db_session)) for p in providers])
           yield services
   - ELSE:
       services = tuple([await anext(p(db_session)) for p in providers])
       yield services

4. CLEANUP (implicit via context manager)
   - Session closed only if owns_session=True
```

### 4.4 Migration Transformations

#### Background Job Transformation

**Before** (`jobs.py:15-27`):
```python
async def cleanup_auth_tokens(_: Context) -> dict[str, int]:
    from app.config import alchemy

    async with alchemy.get_session() as db_session:
        verification_service = await anext(account_deps.provide_email_verification_service(db_session))
        reset_service = await anext(account_deps.provide_password_reset_service(db_session))
        refresh_service = await anext(account_deps.provide_refresh_token_service(db_session))

        verification_count = await verification_service.cleanup_expired_tokens()
        reset_count = await reset_service.cleanup_expired_tokens()
        refresh_count = await refresh_service.cleanup_expired_tokens()
    ...
```

**After**:
```python
async def cleanup_auth_tokens(_: Context) -> dict[str, int]:
    from app.lib.deps import provide_services

    async with provide_services(
        account_deps.provide_email_verification_service,
        account_deps.provide_password_reset_service,
        account_deps.provide_refresh_token_service,
    ) as (verification_service, reset_service, refresh_service):
        verification_count = await verification_service.cleanup_expired_tokens()
        reset_count = await reset_service.cleanup_expired_tokens()
        refresh_count = await refresh_service.cleanup_expired_tokens()
    ...
```

**Lines saved**: 4 lines of boilerplate removed

#### Authentication Guard Transformation

**Before** (`guards.py:94-110`):
```python
async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> m.User | None:
    service = await anext(
        deps.provide_users_service(config.alchemy.provide_session(connection.app.state, connection.scope))
    )
    user = await service.get_one_or_none(email=token.sub)
    return user if user and user.is_active else None
```

**After**:
```python
async def current_user_from_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> m.User | None:
    from app.lib.deps import provide_services

    async with provide_services(deps.provide_users_service, connection=connection) as (service,):
        user = await service.get_one_or_none(email=token.sub)
        return user if user and user.is_active else None
```

**Improvement**: Complex nested call replaced with clear parameter

#### Event Handler Transformation

**Before** (`signals.py:18-32`):
```python
@listener("user_created")
async def user_created_event_handler(user_id: UUID) -> None:
    await logger.ainfo("Running post signup flow.")
    async with alchemy.get_session() as db_session:
        service = await anext(deps.provide_users_service(db_session))
        obj = await service.get_one_or_none(id=user_id)
        ...
```

**After**:
```python
@listener("user_created")
async def user_created_event_handler(user_id: UUID) -> None:
    from app.lib.deps import provide_services

    await logger.ainfo("Running post signup flow.")
    async with provide_services(deps.provide_users_service) as (service,):
        obj = await service.get_one_or_none(id=user_id)
        ...
```

#### CLI Command Transformation

**Before** (`commands.py:182-196`):
```python
async def _create_default_roles() -> None:
    await load_database_fixtures()
    async with alchemy.get_session() as db_session:
        users_service = await anext(provide_users_service(db_session))
        roles_service = await anext(provide_roles_service(db_session))
        ...
```

**After**:
```python
async def _create_default_roles() -> None:
    from app.lib.deps import provide_services

    await load_database_fixtures()
    async with provide_services(
        provide_users_service,
        provide_roles_service,
    ) as (users_service, roles_service):
        ...
```

---

## 5. Testing Strategy

### 5.1 Unit Tests (Target: 90%+ Coverage)

| Test Case | Description | Mocking |
|-----------|-------------|---------|
| `test_single_provider_standalone` | One provider, auto-session | Mock `alchemy.get_session()` |
| `test_multiple_providers_standalone` | 2-3 providers share session | Mock `alchemy.get_session()` |
| `test_with_connection` | Uses `provide_session()` | Mock `alchemy.provide_session()` |
| `test_with_session` | Explicit session passthrough | No mocking needed |
| `test_raises_on_both_session_and_connection` | Validation error | N/A |
| `test_raises_on_no_providers` | Validation error | N/A |
| `test_session_lifecycle_managed` | Session closed on exit | Mock session.close() |
| `test_session_not_closed_when_provided` | External session preserved | Verify close not called |
| `test_error_propagation` | Provider exceptions bubble up | Mock provider to raise |
| `test_services_receive_same_session` | Verify session sharing | Check session identity |

### 5.2 Integration Tests

| Test Case | Description | Database |
|-----------|-------------|----------|
| `test_real_service_instantiation` | Services properly created | Test DB |
| `test_multiple_services_share_session` | Session identity verified | Test DB |
| `test_services_can_query` | Database operations work | Test DB |

### 5.3 Test File Structure

```python
# src/py/tests/unit/test_deps.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestProvideServices:
    """Tests for provide_services context manager."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock service provider."""
        service = MagicMock()

        async def provider(session):
            yield service

        return provider, service

    async def test_single_provider_standalone(self, mock_provider):
        """Test single provider creates session and yields service."""
        provider, expected_service = mock_provider
        mock_session = AsyncMock()

        with patch("app.lib.deps.alchemy") as mock_alchemy:
            mock_alchemy.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_alchemy.get_session.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.lib.deps import provide_services

            async with provide_services(provider) as (service,):
                assert service is expected_service

    # Additional tests...
```

---

## 6. Implementation Notes

### 6.1 Pattern Deviations

| Standard Pattern | Our Approach | Rationale |
|------------------|--------------|-----------|
| `Service.new(config=alchemy)` | Reuse provider functions | Maintains DI consistency, preserves custom config |
| Generic `*args` typing | Explicit overloads to 5 | Better IDE support, covers all current use cases |

### 6.2 Dependencies

| Dependency | Version | Usage |
|------------|---------|-------|
| `contextlib` | stdlib | `@asynccontextmanager` decorator |
| `typing` | stdlib | `overload`, `TypeVar`, type annotations |
| `advanced_alchemy` | existing | Service types, session types |
| `litestar` | existing | `ASGIConnection` type |
| `sqlalchemy` | existing | `AsyncSession` type |

### 6.3 Performance Considerations

- **Session creation**: One session per context, shared across services
- **Generator consumption**: Each `anext()` call is O(1)
- **No caching**: Services created fresh each invocation (matches DI behavior)

### 6.4 Security Considerations

- **Session isolation**: Each context gets its own session (standalone mode)
- **No credential exposure**: Sessions obtained through existing secure mechanisms
- **Transaction boundaries**: Caller controls commit/rollback

---

## 7. Rollout Plan

### 7.1 Implementation Order

1. **Phase 1**: Add helper to `deps.py` with tests
2. **Phase 2**: Update `jobs.py` (highest complexity)
3. **Phase 3**: Update `guards.py` (different pattern)
4. **Phase 4**: Update `signals.py` (simple cases)
5. **Phase 5**: Update `commands.py` (CLI context)
6. **Phase 6**: Validation (`make check-all`)

### 7.2 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Type inference breaks | Comprehensive overloads for 1-5 providers |
| Session leaks | Explicit lifecycle ownership in implementation |
| Import cycles | Inner import of `alchemy` config |
| Regression | Existing tests pass, new tests added |

### 7.3 Rollback Plan

The helper is additive. If issues arise:
1. Revert update sites to original patterns
2. Keep helper for future use or remove if unused

---

## 8. Future Considerations

### 8.1 Potential Extensions

- **Named services**: Dict-style access for many services
- **Lazy instantiation**: Create services on first access
- **Session pooling**: Reuse sessions across calls (advanced)

### 8.2 Not In Scope

- Modifying Litestar DI behavior
- Changing service provider generation
- Adding new service base classes

---

## Appendix A: Complete Implementation Code

### A.1 Full deps.py Addition

The following code should be added to `src/py/app/lib/deps.py`:

```python
"""Application dependency providers generators.

This module contains functions to create dependency providers for services and filters.

You should not have modify this module very often and should only be invoked under normal usage.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, overload

from advanced_alchemy.extensions.litestar.providers import (
    create_filter_dependencies,
    create_service_dependencies,
    create_service_provider,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from typing import TypeVar

    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from litestar.connection import ASGIConnection
    from saq import Queue
    from sqlalchemy.ext.asyncio import AsyncSession

    S1 = TypeVar("S1", bound=SQLAlchemyAsyncRepositoryService[Any])
    S2 = TypeVar("S2", bound=SQLAlchemyAsyncRepositoryService[Any])
    S3 = TypeVar("S3", bound=SQLAlchemyAsyncRepositoryService[Any])
    S4 = TypeVar("S4", bound=SQLAlchemyAsyncRepositoryService[Any])
    S5 = TypeVar("S5", bound=SQLAlchemyAsyncRepositoryService[Any])

__all__ = (
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


# Type overloads for proper tuple typing with 1-5 providers
@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1], None]: ...


@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2], None]: ...


@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    __p3: Callable[[AsyncSession], AsyncGenerator[S3, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2, S3], None]: ...


@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    __p3: Callable[[AsyncSession], AsyncGenerator[S3, None]],
    __p4: Callable[[AsyncSession], AsyncGenerator[S4, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2, S3, S4], None]: ...


@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    __p3: Callable[[AsyncSession], AsyncGenerator[S3, None]],
    __p4: Callable[[AsyncSession], AsyncGenerator[S4, None]],
    __p5: Callable[[AsyncSession], AsyncGenerator[S5, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1, S2, S3, S4, S5], None]: ...


@asynccontextmanager
async def provide_services(
    *providers: Callable[[AsyncSession], AsyncGenerator[Any, None]],
    session: AsyncSession | None = None,
    connection: ASGIConnection[Any, Any, Any, Any] | None = None,
) -> AsyncGenerator[tuple[Any, ...], None]:
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
```

### A.2 Complete Unit Test File

The following test file should be created at `src/py/tests/unit/test_deps.py`:

```python
"""Tests for app.lib.deps module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class TestProvideServices:
    """Tests for provide_services context manager."""

    @pytest.fixture
    def mock_provider(self) -> tuple[Any, MagicMock]:
        """Create a mock service provider."""
        service = MagicMock(name="MockService")

        async def provider(session: Any) -> AsyncGenerator[MagicMock, None]:
            yield service

        return provider, service

    @pytest.fixture
    def mock_provider_factory(self) -> Any:
        """Factory for creating multiple mock providers."""

        def create() -> tuple[Any, MagicMock]:
            service = MagicMock()

            async def provider(session: Any) -> AsyncGenerator[MagicMock, None]:
                yield service

            return provider, service

        return create

    async def test_single_provider_standalone(self, mock_provider: tuple[Any, MagicMock]) -> None:
        """Test single provider in standalone mode creates session and yields service."""
        provider, expected_service = mock_provider
        mock_session = AsyncMock()

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.lib.deps.alchemy") as mock_alchemy:
            mock_alchemy.get_session.return_value = mock_context

            from app.lib.deps import provide_services

            async with provide_services(provider) as (service,):
                assert service is expected_service

            mock_alchemy.get_session.assert_called_once()

    async def test_multiple_providers_standalone(self, mock_provider_factory: Any) -> None:
        """Test multiple providers share the same session in standalone mode."""
        provider1, service1 = mock_provider_factory()
        provider2, service2 = mock_provider_factory()
        provider3, service3 = mock_provider_factory()

        mock_session = AsyncMock()
        received_sessions: list[Any] = []

        async def tracking_provider1(session: Any) -> AsyncGenerator[MagicMock, None]:
            received_sessions.append(session)
            yield service1

        async def tracking_provider2(session: Any) -> AsyncGenerator[MagicMock, None]:
            received_sessions.append(session)
            yield service2

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.lib.deps.alchemy") as mock_alchemy:
            mock_alchemy.get_session.return_value = mock_context

            from app.lib.deps import provide_services

            async with provide_services(tracking_provider1, tracking_provider2) as (s1, s2):
                assert s1 is service1
                assert s2 is service2

            # Verify both providers received the same session
            assert len(received_sessions) == 2
            assert received_sessions[0] is received_sessions[1]
            assert received_sessions[0] is mock_session

    async def test_with_connection(self, mock_provider: tuple[Any, MagicMock]) -> None:
        """Test with connection parameter retrieves session from connection scope."""
        provider, expected_service = mock_provider
        mock_session = AsyncMock()
        mock_connection = MagicMock()
        mock_connection.app.state = MagicMock()
        mock_connection.scope = {}

        with patch("app.lib.deps.alchemy") as mock_alchemy:
            mock_alchemy.provide_session.return_value = mock_session

            from app.lib.deps import provide_services

            async with provide_services(provider, connection=mock_connection) as (service,):
                assert service is expected_service
                mock_alchemy.provide_session.assert_called_once_with(
                    mock_connection.app.state,
                    mock_connection.scope,
                )

    async def test_with_session(self, mock_provider: tuple[Any, MagicMock]) -> None:
        """Test with explicit session parameter uses that session directly."""
        provider, expected_service = mock_provider
        mock_session = AsyncMock()

        from app.lib.deps import provide_services

        async with provide_services(provider, session=mock_session) as (service,):
            assert service is expected_service

    async def test_raises_on_both_session_and_connection(
        self, mock_provider: tuple[Any, MagicMock]
    ) -> None:
        """Test that providing both session and connection raises ValueError."""
        provider, _ = mock_provider
        mock_session = AsyncMock()
        mock_connection = MagicMock()

        from app.lib.deps import provide_services

        with pytest.raises(ValueError, match="Cannot provide both"):
            async with provide_services(
                provider,
                session=mock_session,
                connection=mock_connection,
            ):
                pass

    async def test_raises_on_no_providers(self) -> None:
        """Test that providing no providers raises ValueError."""
        from app.lib.deps import provide_services

        with pytest.raises(ValueError, match="At least one service provider"):
            async with provide_services():
                pass

    async def test_session_not_closed_when_provided(
        self, mock_provider: tuple[Any, MagicMock]
    ) -> None:
        """Test that externally provided session is not closed by the context manager."""
        provider, _ = mock_provider
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        from app.lib.deps import provide_services

        async with provide_services(provider, session=mock_session):
            pass

        # Session close should NOT be called since it was provided externally
        mock_session.close.assert_not_called()

    async def test_error_propagation(self) -> None:
        """Test that errors from providers propagate correctly."""

        class CustomError(Exception):
            pass

        async def failing_provider(session: Any) -> AsyncGenerator[Any, None]:
            raise CustomError("Provider failed")
            yield  # Never reached

        mock_session = AsyncMock()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.lib.deps.alchemy") as mock_alchemy:
            mock_alchemy.get_session.return_value = mock_context

            from app.lib.deps import provide_services

            with pytest.raises(CustomError, match="Provider failed"):
                async with provide_services(failing_provider):
                    pass
```

---

## Appendix B: Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/py/app/lib/deps.py` | **Modify** | Add `provide_services` helper |
| `src/py/app/domain/system/jobs.py` | **Modify** | Update `cleanup_auth_tokens` |
| `src/py/app/domain/accounts/guards.py` | **Modify** | Update `current_user_from_token` |
| `src/py/app/domain/accounts/signals.py` | **Modify** | Update `user_created_event_handler` |
| `src/py/app/domain/teams/signals.py` | **Modify** | Update `team_created_event_handler` |
| `src/py/app/cli/commands.py` | **Modify** | Update `_create_user`, `_create_default_roles` |
| `src/py/tests/unit/test_deps.py` | **Create** | New unit test file |

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Service Provider** | An async generator function that yields a configured service instance. Created via `create_service_provider()`. |
| **Session** | SQLAlchemy `AsyncSession` object representing a database connection with transaction state. |
| **Connection** | Litestar `ASGIConnection` object representing an HTTP request context. |
| **Standalone Context** | Execution outside HTTP request handling (jobs, CLI, events). |
| **Request Context** | Execution within HTTP request handling (guards, route handlers). |
| **Owned Session** | A session created by `provide_services` that it is responsible for closing. |
| **Borrowed Session** | A session passed to `provide_services` that the caller is responsible for closing. |
| **DI** | Dependency Injection - Litestar's system for providing services to route handlers. |

---

## Appendix D: References

1. **Advanced Alchemy Documentation**: Service-Repository pattern implementation
2. **Litestar Documentation**: Dependency injection and guards
3. **Python contextlib**: `@asynccontextmanager` decorator
4. **Python typing**: `@overload` decorator for static type checking
5. **SQLAlchemy**: `AsyncSession` lifecycle management

---

**Document Statistics**:
- Word Count: ~4,200 words
- Sections: 8 main sections + 4 appendices
- Code Examples: 15+
- Tables: 18
- Test Cases: 10
