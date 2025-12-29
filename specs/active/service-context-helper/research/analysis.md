# Pattern Analysis: Service Context Manager Helper

## Complexity Assessment

**Complexity Level**: Medium (8 checkpoints)

**Rationale**:
- Modifies 1 primary file (`deps.py`) with new helper
- Updates 5 existing files to use the new pattern
- Requires new unit test file
- Type overloads add complexity but are contained
- No database changes, no API changes, no frontend changes

---

## Similar Implementations Found

### 1. Advanced Alchemy's `create_service_provider`

**File**: `advanced_alchemy.extensions.litestar.providers` (external package)

**Pattern**: Factory function that returns an async generator for service instantiation.

```python
def create_service_provider(
    service_class: type[Union["AsyncServiceT_co", "SyncServiceT_co"]],
    /,
    statement: "Optional[Select[tuple[ModelT]]]" = None,
    config: "Optional[Union[SQLAlchemyAsyncConfig, SQLAlchemySyncConfig]]" = None,
    ...
) -> Callable[..., Union["AsyncGenerator[AsyncServiceT_co, None]", ...]]:
```

**Key Insight**: The provider is an async generator that must be consumed with `anext()`.

---

### 2. Service `.new()` Context Manager

**File**: `advanced_alchemy.service._async` (external package)

**Pattern**: Class method context manager that handles session creation.

```python
@classmethod
@asynccontextmanager
async def new(
    cls,
    session: Optional[AsyncSession] = None,
    config: Optional[SQLAlchemyAsyncConfig] = None,
    ...
) -> AsyncIterator[Self]:
    if session:
        yield cls(session=session, ...)
    elif config:
        async with config.get_session() as db_session:
            yield cls(session=db_session, ...)
```

**Key Insight**: Session can come from config auto-creation or be passed explicitly.

---

### 3. Current Usage in `jobs.py`

**File**: `src/py/app/domain/system/jobs.py:15-34`

**Pattern**: Manual session management with multiple `anext()` calls.

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

    result = {...}
```

**Pain Points**:
- 4 lines of boilerplate per function
- Session management mixed with service instantiation
- Easy to forget `await anext()` pattern

---

### 4. Current Usage in `guards.py`

**File**: `src/py/app/domain/accounts/guards.py:94-110`

**Pattern**: Request-scoped session from connection.

```python
async def current_user_from_token(token: Token, connection: ASGIConnection[...]) -> m.User | None:
    service = await anext(
        deps.provide_users_service(config.alchemy.provide_session(connection.app.state, connection.scope))
    )
    user = await service.get_one_or_none(email=token.sub)
    return user if user and user.is_active else None
```

**Pain Points**:
- Complex nested call: `anext(provider(config.alchemy.provide_session(state, scope)))`
- Session source differs from standalone contexts
- Hard to read and maintain

---

### 5. Current Usage in CLI Commands

**File**: `src/py/app/cli/commands.py:103-106, 182-196`

**Pattern**: CLI context with explicit session management.

```python
async def _create_user(...) -> None:
    async with alchemy.get_session() as db_session:
        users_service = await anext(provide_users_service(db_session))
        user = await users_service.create(data=obj_in.to_dict(), auto_commit=True)

async def _create_default_roles() -> None:
    async with alchemy.get_session() as db_session:
        users_service = await anext(provide_users_service(db_session))
        roles_service = await anext(provide_roles_service(db_session))
        ...
```

**Pain Points**:
- Same boilerplate repeated in multiple CLI commands
- Session scope management duplicated

---

## Patterns to Follow

### Async Context Manager Pattern

From Python's `contextlib.asynccontextmanager`:

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def provide_services(...) -> AsyncGenerator[tuple[Any, ...], None]:
    # Setup
    async with alchemy.get_session() as db_session:
        services = [await anext(p(db_session)) for p in providers]
        yield tuple(services)
    # Cleanup (handled by session context manager)
```

### Type Overload Pattern

For proper IDE typing with variable-length tuple returns:

```python
from typing import overload, TypeVar

S1 = TypeVar("S1", bound=SQLAlchemyAsyncRepositoryService[Any])
S2 = TypeVar("S2", bound=SQLAlchemyAsyncRepositoryService[Any])

@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    /,
    **kwargs,
) -> AsyncGenerator[tuple[S1], None]: ...

@overload
@asynccontextmanager
async def provide_services(
    __p1: Callable[[AsyncSession], AsyncGenerator[S1, None]],
    __p2: Callable[[AsyncSession], AsyncGenerator[S2, None]],
    /,
    **kwargs,
) -> AsyncGenerator[tuple[S1, S2], None]: ...
```

### Session Source Pattern

Three session acquisition strategies:

1. **Standalone**: `alchemy.get_session()` - creates and manages session
2. **Request**: `alchemy.provide_session(state, scope)` - gets session from request scope
3. **Explicit**: `session=existing` - uses provided session, no lifecycle management

---

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Helper function | `provide_*` prefix | `provide_services` |
| Type variables | Single letter + number | `S1`, `S2`, `S3` |
| Private params | Double underscore prefix | `__p1`, `__p2` |
| Error messages | Full sentence, lowercase | `"Cannot provide both..."` |

---

## Error Handling

| Scenario | Response |
|----------|----------|
| No providers given | `ValueError("At least one service provider is required")` |
| Both session and connection | `ValueError("Cannot provide both 'session' and 'connection' - choose one")` |
| Provider instantiation fails | Propagate original exception |

---

## Session Lifecycle Rules

| Source | Managed By | Cleanup |
|--------|------------|---------|
| `alchemy.get_session()` | `provide_services` | Yes - closes on exit |
| `alchemy.provide_session()` | Litestar | No - request-scoped |
| `session=` parameter | Caller | No - externally owned |
