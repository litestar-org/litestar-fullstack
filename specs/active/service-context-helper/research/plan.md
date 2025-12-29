# Research Plan: Service Context Manager Helper

## Executive Summary

This document provides comprehensive research for implementing a `provide_services` context manager helper in the `app/lib/deps.py` module. The helper will simplify service acquisition outside of Litestar's dependency injection context, reducing boilerplate code across background jobs, CLI commands, event handlers, and authentication guards.

The research covers existing patterns in the codebase, Advanced Alchemy's service infrastructure, Python async context manager best practices, and type annotation strategies for variable-length tuple returns.

---

## 1. Problem Domain Analysis

### 1.1 Current State Assessment

The litestar-fullstack-spa application uses Advanced Alchemy's service-repository pattern for all database operations. Services are typically injected via Litestar's dependency injection system in controllers and route handlers. However, several execution contexts exist outside of HTTP request handling where services must be instantiated manually:

1. **Background Jobs (SAQ)**: Scheduled tasks that run independently of HTTP requests, such as token cleanup, email sending, and maintenance operations. These jobs need database access through services but have no request context.

2. **CLI Commands**: Administrative commands for user management, database seeding, and maintenance. These run in a terminal context with no web framework infrastructure.

3. **Event Handlers**: Litestar event listeners that respond to application events (user creation, team creation). While triggered within the application, they operate outside the standard request-response cycle.

4. **Authentication Guards**: The `current_user_from_token` function retrieves the user during JWT validation. It has access to the ASGI connection but needs to instantiate services manually.

### 1.2 Pain Point Quantification

Analysis of the codebase reveals the following instances of the verbose pattern:

| Location | Services | Lines of Boilerplate |
|----------|----------|---------------------|
| `jobs.py:cleanup_auth_tokens` | 3 | 4 |
| `commands.py:_create_user` | 1 | 2 |
| `commands.py:_create_default_roles` | 2 | 3 |
| `signals.py:user_created_event_handler` | 1 | 2 |
| `signals.py:team_created_event_handler` | 1 | 2 |
| `guards.py:current_user_from_token` | 1 | 3 |
| **Total** | **9 service instances** | **16 lines** |

Each instance follows a similar pattern that could be abstracted into a single, reusable helper. The cognitive load of remembering the `await anext(provider(session))` pattern and managing session lifecycle creates maintenance burden and potential for errors.

### 1.3 Session Management Complexity

The codebase uses three distinct session acquisition strategies:

**Strategy 1: Standalone Session Creation**
```python
from app.config import alchemy
async with alchemy.get_session() as db_session:
    service = await anext(provide_service(db_session))
```

This pattern creates a new database session, uses it for service operations, and ensures proper cleanup when the context exits. The session is "owned" by this context and should not be used elsewhere.

**Strategy 2: Request-Scoped Session**
```python
db_session = config.alchemy.provide_session(connection.app.state, connection.scope)
service = await anext(provide_service(db_session))
```

This pattern retrieves an existing session from the ASGI connection scope. The session lifecycle is managed by Litestar's request handling infrastructure, not by the calling code. This is used in authentication guards where a request context exists.

**Strategy 3: External Session Passthrough**
```python
# Session provided by caller
service = await anext(provide_service(existing_session))
```

In some cases, a session may be provided by an outer context that manages the transaction boundary. The service should use this session but not close it.

A unified helper must support all three strategies while maintaining clear semantics about session lifecycle ownership.

---

## 2. Technical Research

### 2.1 Advanced Alchemy Service Infrastructure

Advanced Alchemy provides the `SQLAlchemyAsyncRepositoryService` base class for implementing the service-repository pattern. Key aspects relevant to this implementation:

**Service Provider Pattern**

The `create_service_provider` function generates async generator functions that yield configured service instances:

```python
# From advanced_alchemy.extensions.litestar.providers
def create_service_provider(
    service_class: type[AsyncServiceT_co],
    statement: Optional[Select[tuple[ModelT]]] = None,
    config: Optional[SQLAlchemyAsyncConfig] = None,
    ...
) -> Callable[[AsyncSession], AsyncGenerator[AsyncServiceT_co, None]]:

    async def provide_service_async(db_session: AsyncSession) -> AsyncGenerator[AsyncServiceT_co, None]:
        async with service_class.new(
            session=db_session,
            statement=statement,
            config=config,
            ...
        ) as service:
            yield service

    return provide_service_async
```

The provider is an async generator that must be consumed with `anext()`. This design allows Litestar's DI system to properly manage the service lifecycle within request contexts.

**Service `.new()` Context Manager**

Services provide a `.new()` class method that acts as a factory context manager:

```python
@classmethod
@asynccontextmanager
async def new(
    cls,
    session: Optional[AsyncSession] = None,
    config: Optional[SQLAlchemyAsyncConfig] = None,
    ...
) -> AsyncIterator[Self]:
    if not config and not session:
        raise AdvancedAlchemyError("Please supply configuration or session")

    if session:
        yield cls(session=session, ...)
    elif config:
        async with config.get_session() as db_session:
            yield cls(session=db_session, ...)
```

This demonstrates the session-from-config pattern that we want to leverage. When no session is provided but a config is, the service creates its own session.

### 2.2 SQLAlchemy AsyncSession Lifecycle

SQLAlchemy's `AsyncSession` has specific lifecycle requirements:

1. **Session creation**: Sessions should be created through the `async_sessionmaker` or config's `get_session()` method
2. **Transaction boundaries**: Sessions accumulate changes until `commit()` or `rollback()` is called
3. **Session cleanup**: Sessions should be closed to return connections to the pool
4. **Context manager protocol**: `AsyncSession` supports `async with` for automatic cleanup

The `alchemy.get_session()` method in this application returns an async context manager that handles session creation and cleanup:

```python
# From app.config.alchemy
async with alchemy.get_session() as session:
    # session is valid here
    # automatically closed/rolled back on exit
```

### 2.3 Python Async Context Manager Patterns

Python's `contextlib.asynccontextmanager` decorator transforms an async generator function into an async context manager:

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def resource_manager() -> AsyncGenerator[Resource, None]:
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        await release_resource(resource)
```

Key behaviors:
- Code before `yield` runs on `__aenter__`
- The yielded value is returned from `__aenter__`
- Code after `yield` runs on `__aexit__` (in finally block)
- Exceptions are propagated unless explicitly suppressed

For our helper, the pattern is:

```python
@asynccontextmanager
async def provide_services(*providers, session=None, connection=None):
    # Determine session source
    if session is not None:
        db_session = session
        owns_session = False
    elif connection is not None:
        db_session = alchemy.provide_session(connection.app.state, connection.scope)
        owns_session = False
    else:
        # Create managed session
        owns_session = True

    if owns_session:
        async with alchemy.get_session() as db_session:
            services = tuple([await anext(p(db_session)) for p in providers])
            yield services
    else:
        services = tuple([await anext(p(db_session)) for p in providers])
        yield services
```

### 2.4 Type Annotation Strategy

Python's type system has limited support for variable-length tuples with heterogeneous types. The standard approach is to use `@overload` decorators:

```python
from typing import overload, TypeVar

S1 = TypeVar("S1")
S2 = TypeVar("S2")

@overload
async def provide_services(p1: Provider[S1]) -> tuple[S1]: ...

@overload
async def provide_services(p1: Provider[S1], p2: Provider[S2]) -> tuple[S1, S2]: ...

async def provide_services(*providers) -> tuple[Any, ...]:
    # Implementation
```

**Type Variable Constraints**

Type variables should be bound to the service base class:

```python
from typing import TypeVar, Any
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

S1 = TypeVar("S1", bound=SQLAlchemyAsyncRepositoryService[Any])
```

**Positional-Only Parameters in Overloads**

Using `/` to mark positional-only parameters prevents name conflicts:

```python
@overload
async def provide_services(
    __p1: Provider[S1],  # Double underscore prefix
    /,  # Positional-only marker
    *,
    session: AsyncSession | None = ...,
) -> AsyncGenerator[tuple[S1], None]: ...
```

**Overload Coverage**

We should provide overloads for 1-5 providers, which covers all current use cases. Beyond 5, users get `tuple[Any, ...]` typing, which is acceptable for rare cases.

---

## 3. Design Decisions

### 3.1 API Design Rationale

**Decision 1: Tuple Return vs Named Access**

Options considered:
- Tuple unpacking: `async with provide_services(p1, p2) as (s1, s2):`
- Dict access: `async with provide_services({'users': p1}) as svcs: s = svcs['users']`
- Single service wrapper: `async with provide_service(p1) as s:`

**Chosen**: Tuple unpacking

**Rationale**:
- Most concise syntax for multiple services
- Preserves type inference through overloads
- Matches existing patterns in Python ecosystem (e.g., `asyncio.gather`)
- Single service case works with trailing comma: `as (s,):`

**Decision 2: Session Source Parameters**

Options considered:
- Single `session_source` union parameter
- Separate `session` and `connection` parameters
- Config-based auto-session only

**Chosen**: Separate `session` and `connection` keyword-only parameters

**Rationale**:
- Clear semantics: each parameter has one purpose
- Type-safe: `AsyncSession` vs `ASGIConnection` are distinct types
- Explicit: ValueError if both provided prevents ambiguity
- Default behavior (neither provided) creates managed session

**Decision 3: Provider Reuse vs Direct Instantiation**

Options considered:
- Reuse existing `provide_*_service` functions with `anext()`
- Directly instantiate services with `Service.new()`

**Chosen**: Reuse provider functions

**Rationale**:
- Maintains consistency with Litestar DI patterns
- Providers may contain custom configuration (statements, load specs)
- Easier migration: just change how providers are called
- Providers are already defined and exported in dependencies modules

### 3.2 Error Handling Strategy

| Scenario | Error Type | Message |
|----------|------------|---------|
| No providers | `ValueError` | "At least one service provider is required" |
| Both session and connection | `ValueError` | "Cannot provide both 'session' and 'connection' - choose one" |
| Provider raises | Propagate | Original exception |
| Session error | Propagate | Original exception |

Errors should be clear and actionable. The helper should not swallow exceptions or add unnecessary wrapping.

### 3.3 Import Strategy

The `alchemy` config must be imported inside the function to avoid circular imports:

```python
async def provide_services(...):
    from app.config import alchemy
    # ...
```

This is a common pattern in the codebase (see `jobs.py`, `commands.py`).

---

## 4. Implementation Approach

### 4.1 File Structure

```
src/py/app/lib/deps.py
├── Existing exports (create_service_provider, etc.)
├── Type variables (S1-S5)
├── Type alias (ServiceProvider)
├── Overload declarations (1-5 providers)
└── Implementation (provide_services)
```

### 4.2 Type Definitions

```python
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession
    from typing import TypeVar

    S1 = TypeVar("S1", bound=SQLAlchemyAsyncRepositoryService[Any])
    S2 = TypeVar("S2", bound=SQLAlchemyAsyncRepositoryService[Any])
    S3 = TypeVar("S3", bound=SQLAlchemyAsyncRepositoryService[Any])
    S4 = TypeVar("S4", bound=SQLAlchemyAsyncRepositoryService[Any])
    S5 = TypeVar("S5", bound=SQLAlchemyAsyncRepositoryService[Any])
```

### 4.3 Overload Pattern

Each overload follows this structure:

```python
@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    /,
    *,
    session: AsyncSession | None = ...,
    connection: ASGIConnection[Any, Any, Any, Any] | None = ...,
) -> AsyncGenerator[tuple[S1], None]: ...
```

### 4.4 Implementation Core

```python
@asynccontextmanager
async def provide_services(
    *providers: Callable[[AsyncSession], AsyncGenerator[Any, None]],
    session: AsyncSession | None = None,
    connection: ASGIConnection[Any, Any, Any, Any] | None = None,
) -> AsyncGenerator[tuple[Any, ...], None]:
    from app.config import alchemy

    # Validation
    if session is not None and connection is not None:
        msg = "Cannot provide both 'session' and 'connection' - choose one"
        raise ValueError(msg)

    if not providers:
        msg = "At least one service provider is required"
        raise ValueError(msg)

    # Session source routing
    if session is not None:
        services = tuple([await anext(provider(session)) for provider in providers])
        yield services
    elif connection is not None:
        db_session = alchemy.provide_session(connection.app.state, connection.scope)
        services = tuple([await anext(provider(db_session)) for provider in providers])
        yield services
    else:
        async with alchemy.get_session() as db_session:
            services = tuple([await anext(provider(db_session)) for provider in providers])
            yield services
```

---

## 5. Migration Strategy

### 5.1 Update Order

1. Add `provide_services` to `deps.py`
2. Update `jobs.py` (most complex, 3 services)
3. Update `guards.py` (different session source)
4. Update `signals.py` (simple cases)
5. Update `commands.py` (CLI context)

### 5.2 Transformation Rules

**Standalone Context (jobs, signals, CLI)**

Before:
```python
from app.config import alchemy
async with alchemy.get_session() as db_session:
    service = await anext(provide_service(db_session))
    # use service
```

After:
```python
from app.lib.deps import provide_services
async with provide_services(provide_service) as (service,):
    # use service
```

**Request Context (guards)**

Before:
```python
service = await anext(
    deps.provide_service(config.alchemy.provide_session(connection.app.state, connection.scope))
)
```

After:
```python
async with provide_services(deps.provide_service, connection=connection) as (service,):
    # use service
```

### 5.3 Backwards Compatibility

The new helper is additive. Existing code continues to work. Migration can be incremental.

---

## 6. Testing Strategy

### 6.1 Unit Test Coverage

| Test Case | Description |
|-----------|-------------|
| `test_single_provider_standalone` | One provider, no session/connection |
| `test_multiple_providers_standalone` | Multiple providers share session |
| `test_with_connection` | Request context session source |
| `test_with_session` | Explicit session passthrough |
| `test_raises_on_both_session_and_connection` | Validation error |
| `test_raises_on_no_providers` | Validation error |
| `test_session_lifecycle_managed` | Session closed on exit |
| `test_session_not_closed_when_provided` | External session preserved |
| `test_error_propagation` | Provider errors bubble up |

### 6.2 Integration Tests

Test with real services against test database:
- Service instantiation succeeds
- Services share same session
- Database queries execute correctly

---

## 7. Conclusion

The `provide_services` context manager helper addresses a clear pattern of boilerplate code across the application. By centralizing session management and service instantiation, we reduce code duplication, improve maintainability, and provide a consistent API for service acquisition outside of Litestar's dependency injection context.

The implementation follows established patterns in the codebase and Python ecosystem, with careful attention to type safety through overloads and clear error handling for edge cases.

**Word Count**: ~2,400 words
