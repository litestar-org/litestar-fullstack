# Litestar Framework Skill

Quick reference for Litestar patterns used in this project.

## Context7 Lookup

```python
mcp__context7__resolve-library-id(libraryName="litestar", query="...")
mcp__context7__query-docs(libraryId="/litestar-org/litestar", query="...")
```

## Project Files

- Controllers: `src/py/app/domain/*/controllers/`
- Route registration: `src/py/app/server/routes/__init__.py`
- Plugins: `src/py/app/server/plugins.py`
- Core setup: `src/py/app/server/core.py`

## Controller Pattern

```python
from litestar import Controller, get, post, put, patch, delete
from litestar.di import Provide
from litestar.params import Parameter, Dependency

class UserController(Controller):
    path = "/users"
    tags = ["Users"]
    dependencies = {"user_service": Provide(provide_user_service)}

    @get()
    async def list_users(
        self,
        user_service: UserService,
        limit: int = Parameter(ge=1, le=100, default=20),
        offset: int = Parameter(ge=0, default=0),
    ) -> list[User]:
        """List all users."""
        return await user_service.list(limit_offset=(limit, offset))

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_service: UserService,
        user_id: UUID,
    ) -> User:
        """Get user by ID."""
        return await user_service.get(user_id)

    @post()
    async def create_user(
        self,
        user_service: UserService,
        data: UserCreate,
    ) -> User:
        """Create a new user."""
        return await user_service.create(data.to_dict())

    @patch("/{user_id:uuid}")
    async def update_user(
        self,
        user_service: UserService,
        user_id: UUID,
        data: UserUpdate,
    ) -> User:
        """Update user."""
        return await user_service.update(user_id, data.to_dict())

    @delete("/{user_id:uuid}")
    async def delete_user(
        self,
        user_service: UserService,
        user_id: UUID,
    ) -> None:
        """Delete user."""
        await user_service.delete(user_id)
```

## Dependency Injection

```python
from litestar.di import Provide

# In controller
dependencies = {"service": Provide(provide_service)}

# Provider function
async def provide_service(db_session: AsyncSession) -> ServiceType:
    return ServiceType(session=db_session)
```

## Guards (Authentication/Authorization)

```python
from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler

async def requires_auth(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    """Guard that requires authentication."""
    if not connection.user:
        raise PermissionDeniedException("Authentication required")

# Usage in controller
@get(guards=[requires_auth])
async def protected_route(self) -> dict:
    ...
```

## Request/Response

```python
from litestar import Request
from litestar.response import Response

@post()
async def create_with_request(
    self,
    request: Request,
    data: CreateSchema,
) -> Response:
    # Access request data
    user = request.user
    headers = request.headers

    result = ...

    return Response(
        content=result,
        status_code=201,
        headers={"X-Custom": "value"},
    )
```

## Exception Handling

```python
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
    ClientException,
)

# Raise in handler
raise NotFoundException("User not found")
raise PermissionDeniedException("Access denied")
raise ClientException("Invalid input")
```

## Pagination

```python
from advanced_alchemy.service.pagination import OffsetPagination

@get()
async def list_paginated(
    self,
    service: Service,
    limit: int = 20,
    offset: int = 0,
) -> OffsetPagination[Schema]:
    return await service.list_and_count(limit_offset=(limit, offset))
```

## Route Registration

```python
# In routes/__init__.py
from litestar import Router

from .accounts import AccountController, UserController

__all__ = ["create_router"]

def create_router() -> Router:
    return Router(
        path="/api",
        route_handlers=[
            AccountController,
            UserController,
        ],
    )
```
