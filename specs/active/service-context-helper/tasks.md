# Implementation Tasks: Service Context Manager Helper

**Feature**: `provide_services` Context Manager
**Complexity**: Medium (8 checkpoints)
**Estimated Tasks**: 12

---

## Phase 1: Core Implementation

### Task 1: Add Type Definitions to deps.py
**File**: `src/py/app/lib/deps.py`
**Action**: Add TYPE_CHECKING block with type variables

```python
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from typing import TypeVar

    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from litestar.connection import ASGIConnection
    from sqlalchemy.ext.asyncio import AsyncSession

    S1 = TypeVar("S1", bound=SQLAlchemyAsyncRepositoryService[Any])
    S2 = TypeVar("S2", bound=SQLAlchemyAsyncRepositoryService[Any])
    S3 = TypeVar("S3", bound=SQLAlchemyAsyncRepositoryService[Any])
    S4 = TypeVar("S4", bound=SQLAlchemyAsyncRepositoryService[Any])
    S5 = TypeVar("S5", bound=SQLAlchemyAsyncRepositoryService[Any])
```

- [ ] Add imports to TYPE_CHECKING block
- [ ] Define S1-S5 type variables

---

### Task 2: Add Type Overloads to deps.py
**File**: `src/py/app/lib/deps.py`
**Action**: Add 5 overload declarations for proper typing

- [ ] Add 1-provider overload
- [ ] Add 2-provider overload
- [ ] Add 3-provider overload
- [ ] Add 4-provider overload
- [ ] Add 5-provider overload

---

### Task 3: Implement provide_services Function
**File**: `src/py/app/lib/deps.py`
**Action**: Add the main implementation

- [ ] Add `@asynccontextmanager` decorator
- [ ] Implement validation (no providers, both session/connection)
- [ ] Implement session source routing (standalone, connection, explicit)
- [ ] Implement service instantiation via `anext()`
- [ ] Add comprehensive docstring with examples

---

### Task 4: Update __all__ Exports
**File**: `src/py/app/lib/deps.py`
**Action**: Export new function

- [ ] Add `"provide_services"` to `__all__` tuple

---

## Phase 2: Update Existing Code

### Task 5: Update jobs.py
**File**: `src/py/app/domain/system/jobs.py`
**Function**: `cleanup_auth_tokens`

**Before**:
```python
async with alchemy.get_session() as db_session:
    verification_service = await anext(account_deps.provide_email_verification_service(db_session))
    reset_service = await anext(account_deps.provide_password_reset_service(db_session))
    refresh_service = await anext(account_deps.provide_refresh_token_service(db_session))
```

**After**:
```python
async with provide_services(
    account_deps.provide_email_verification_service,
    account_deps.provide_password_reset_service,
    account_deps.provide_refresh_token_service,
) as (verification_service, reset_service, refresh_service):
```

- [ ] Update imports (remove `alchemy`, add `provide_services`)
- [ ] Replace session context with `provide_services`
- [ ] Test job still works

---

### Task 6: Update guards.py
**File**: `src/py/app/domain/accounts/guards.py`
**Function**: `current_user_from_token`

**Before**:
```python
service = await anext(
    deps.provide_users_service(config.alchemy.provide_session(connection.app.state, connection.scope))
)
user = await service.get_one_or_none(email=token.sub)
return user if user and user.is_active else None
```

**After**:
```python
async with provide_services(deps.provide_users_service, connection=connection) as (service,):
    user = await service.get_one_or_none(email=token.sub)
    return user if user and user.is_active else None
```

- [ ] Add import for `provide_services`
- [ ] Replace nested call with context manager
- [ ] Test authentication still works

---

### Task 7: Update accounts/signals.py
**File**: `src/py/app/domain/accounts/signals.py`
**Function**: `user_created_event_handler`

- [ ] Update imports
- [ ] Replace session context with `provide_services`
- [ ] Test event handler works

---

### Task 8: Update teams/signals.py
**File**: `src/py/app/domain/teams/signals.py`
**Function**: `team_created_event_handler`

- [ ] Update imports
- [ ] Replace session context with `provide_services`
- [ ] Test event handler works

---

### Task 9: Update commands.py
**File**: `src/py/app/cli/commands.py`
**Functions**: `_create_user`, `_create_default_roles`

- [ ] Update `_create_user` function
- [ ] Update `_create_default_roles` function
- [ ] Test CLI commands work

---

## Phase 3: Testing

### Task 10: Create Unit Tests
**File**: `src/py/tests/unit/test_deps.py` (NEW)

- [ ] Create test file with TestProvideServices class
- [ ] Add test_single_provider_standalone
- [ ] Add test_multiple_providers_standalone
- [ ] Add test_with_connection
- [ ] Add test_with_session
- [ ] Add test_raises_on_both_session_and_connection
- [ ] Add test_raises_on_no_providers
- [ ] Add test_session_lifecycle_managed
- [ ] Add test_error_propagation
- [ ] Verify 90%+ coverage on deps.py

---

### Task 11: Run Test Suite
**Command**: `make test`

- [ ] Run `make test`
- [ ] Fix any failing tests
- [ ] Verify no regressions

---

## Phase 4: Validation

### Task 12: Final Validation
**Command**: `make check-all`

- [ ] Run `make lint` and fix issues
- [ ] Run `make check-all`
- [ ] Verify all checks pass

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. Core | 1-4 | Add helper to deps.py |
| 2. Update | 5-9 | Migrate existing code |
| 3. Testing | 10-11 | Unit tests and validation |
| 4. Validation | 12 | Final checks |

**Total Tasks**: 12
**Complexity**: Medium

---

## Execution Checklist

```
[ ] Phase 1: Core Implementation
    [ ] Task 1: Type definitions
    [ ] Task 2: Type overloads
    [ ] Task 3: Implementation
    [ ] Task 4: Exports

[ ] Phase 2: Update Existing Code
    [ ] Task 5: jobs.py
    [ ] Task 6: guards.py
    [ ] Task 7: accounts/signals.py
    [ ] Task 8: teams/signals.py
    [ ] Task 9: commands.py

[ ] Phase 3: Testing
    [ ] Task 10: Unit tests
    [ ] Task 11: Run tests

[ ] Phase 4: Validation
    [ ] Task 12: make check-all
```
