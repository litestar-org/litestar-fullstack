# Pattern Library

This directory contains reusable patterns extracted from this codebase.

## How Patterns Are Captured

1. During implementation, new patterns are documented in the spec's `tmp/new-patterns.md`
2. During review, patterns are extracted to this directory
3. Future features consult this library first before implementing

## Pattern Categories

### Service Patterns

**Inner Repository Pattern** - All database operations use this:

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m

class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Service for user operations."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        """User repository."""
        model_type = m.User

    repository_type = Repo
    match_fields = ["email"]  # For upsert operations

    async def to_model_on_create(self, data):
        # Transform data before create
        return await self._populate_model(data)
```

### Schema Patterns

**msgspec Struct for DTOs** - Never use dicts or Pydantic:

```python
from app.schemas.base import CamelizedBaseStruct

class UserCreate(CamelizedBaseStruct, gc=False, array_like=True, omit_defaults=True):
    """User creation payload."""
    email: str
    password: str
    name: str | None = None
```

### Model Patterns

**UUIDAuditBase** - All models inherit from this:

```python
from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column

class User(UUIDAuditBase):
    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts"}

    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
```

### Controller Patterns

**Litestar Controllers** - Routes grouped by domain:

```python
from litestar import Controller, get, post
from litestar.di import Provide

class UserController(Controller):
    path = "/users"
    dependencies = {"user_service": Provide(provide_user_service)}

    @get()
    async def list_users(self, user_service: UserService) -> list[User]:
        return await user_service.list()
```

### Testing Patterns

**Function-based pytest tests**:

```python
import pytest
from polyfactory.factories import TypedDictFactory

@pytest.mark.asyncio
async def test_user_create(db_session):
    """Test user creation."""
    service = UserService(session=db_session)
    user = await service.create({"email": "test@example.com"})
    assert user.email == "test@example.com"
```

### Frontend Patterns

**TanStack Router pages** in `src/js/src/routes/`:

```typescript
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/users')({
  component: UsersPage,
})

function UsersPage() {
  return <div>Users</div>
}
```

**TanStack Query hooks**:

```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => api.getUsers(),
  })
}
```

## Using Patterns

Before implementing a feature:

1. Search this directory for similar patterns
2. Read the pattern documentation
3. Follow established conventions exactly
4. Only deviate with documented rationale
5. Add new patterns during the review phase
