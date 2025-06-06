# Backend Architecture

## Overview

The backend is built on Litestar, a modern ASGI framework that provides high performance, full async support, and excellent developer experience. The architecture follows a layered approach with clear separation of concerns.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer (Routes)                    │
│         HTTP Request/Response, Authentication           │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                          │
│          Business Logic, Orchestration                  │
├─────────────────────────────────────────────────────────┤
│                Repository Layer                         │
│            Data Access Patterns                         │
├─────────────────────────────────────────────────────────┤
│                  Model Layer                            │
│           SQLAlchemy ORM Models                         │
├─────────────────────────────────────────────────────────┤
│                Database Layer                           │
│            PostgreSQL + Redis                           │
└─────────────────────────────────────────────────────────┘
```

## Service Layer Pattern

### ⚠️ Critical: Inner Repository Pattern

All services MUST follow the Advanced Alchemy pattern with an inner `Repo` class:

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m

class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""
        model_type = m.User

    repository_type = Repo
    
    # Custom service attributes
    default_role = "USER"
    match_fields = ["email"]  # Fields for get_or_create operations

    async def to_model_on_create(
        self, 
        data: service.ModelDictT[m.User]
    ) -> service.ModelDictT[m.User]:
        """Transform data before creating model."""
        return await self._populate_model(data)

    async def to_model_on_update(
        self, 
        data: service.ModelDictT[m.User]
    ) -> service.ModelDictT[m.User]:
        """Transform data before updating model."""
        return await self._populate_model(data)

    async def _populate_model(
        self, 
        data: service.ModelDictT[m.User]
    ) -> service.ModelDictT[m.User]:
        """Handle special field processing like password hashing."""
        data = service.schema_dump(data)
        if service.is_dict(data) and (password := data.pop("password", None)):
            data["hashed_password"] = await crypt.get_password_hash(password)
        return data

    async def authenticate(self, username: str, password: str) -> m.User:
        """Custom business logic method."""
        db_obj = await self.get_one_or_none(email=username)
        if db_obj is None:
            raise PermissionDeniedException("Invalid credentials")
        if not await crypt.verify_password(password, db_obj.hashed_password):
            raise PermissionDeniedException("Invalid credentials")
        return db_obj
```

### Service Methods

Services provide both inherited and custom methods:

#### Inherited Methods (from Advanced Alchemy)
- `get(id)` - Get by primary key
- `get_one(**filters)` - Get single record with filters
- `get_one_or_none(**filters)` - Get or return None
- `list(**filters)` - List with optional filtering
- `create(data)` - Create new record
- `update(data)` - Update existing record
- `upsert(data)` - Create or update
- `delete(id)` - Delete by primary key
- `delete_many(**filters)` - Bulk delete

#### Custom Methods
Add business logic methods specific to your domain:

```python
async def verify_email(self, user_id: UUID, token: str) -> m.User:
    """Verify user's email address."""
    # Custom business logic here
    
async def assign_team_role(
    self, 
    user_id: UUID, 
    team_id: UUID, 
    role: str
) -> m.TeamMember:
    """Assign user to team with role."""
    # Complex orchestration logic
```

## Database Models

### SQLAlchemy 2.0 Patterns

All models use modern SQLAlchemy 2.0 syntax with full type annotations:

```python
from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from advanced_alchemy.base import UUIDAuditBase

class User(UUIDAuditBase):
    """User account model with audit fields."""
    
    __tablename__ = "user_account"
    
    # Required fields with type annotations
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True
    )
    
    # Profile fields
    name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    
    # Status flags with defaults
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    
    # Timestamps
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
    
    # Relationships with loading strategies
    teams: Mapped[list["TeamMember"]] = relationship(
        lazy="selectin",
        back_populates="user"
    )
    roles: Mapped[list["UserRole"]] = relationship(
        lazy="selectin",
        back_populates="user"
    )
    
    # Composite indexes for performance
    __table_args__ = (
        Index("ix_user_email_active", "email", "is_active"),
    )
```

### Base Classes from Advanced Alchemy

- **`UUIDAuditBase`** - UUID primary key + created_at/updated_at
- **`UUIDBase`** - Just UUID primary key
- **`AuditColumns`** - Just audit fields
- **`SlugKey`** - Slug-based lookups
- **`UniqueMixin`** - Unique constraint validation

### Relationship Patterns

```python
class Team(UUIDAuditBase):
    """Team model with relationships."""
    
    # One-to-many
    members: Mapped[list["TeamMember"]] = relationship(
        lazy="selectin",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    
    # Many-to-many through association
    tags: Mapped[list["Tag"]] = relationship(
        secondary="team_tag",
        lazy="selectin",
        back_populates="teams"
    )
```

## API DTOs with msgspec

### ⚠️ Critical: Always Use msgspec.Struct

All API request/response bodies MUST use `msgspec.Struct`:

```python
import msgspec
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from uuid import UUID

# Base struct with common options
class BaseStruct(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """Base class for all DTOs."""
    pass

# Request DTOs
class UserCreate(BaseStruct):
    """User creation request."""
    email: str
    password: str
    name: str | None = None

class UserUpdate(BaseStruct):
    """User update request."""
    name: str | None = None
    email: str | None = None

# Response DTOs
class UserRead(BaseStruct):
    """User response."""
    id: UUID
    email: str
    name: str | None = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    
class UserList(BaseStruct):
    """Paginated user list."""
    items: list[UserRead]
    total: int
    page: int
    page_size: int
```

### Naming Conventions

- **Create** - For creation requests (`UserCreate`)
- **Update** - For update requests (`UserUpdate`)
- **Read** - For single responses (`UserRead`)
- **List** - For collection responses (`UserList`)
- **Payload** - For generic requests (`LoginPayload`)
- **Response** - For generic responses (`LoginResponse`)

## Route Controllers

Controllers handle HTTP concerns and delegate to services:

```python
from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.params import Parameter
from uuid import UUID

from app.schemas import UserCreate, UserRead, UserUpdate
from app.services import UserService
from app.server.deps import provide_users_service

@Controller(
    path="/api/users",
    guards=[requires_active_user],
    dependencies={"users_service": Provide(provide_users_service)},
)
class UserController:
    """User management endpoints."""
    
    @get(
        "/{user_id:uuid}",
        operation_id="GetUser",
        description="Get user by ID",
    )
    async def get_user(
        self,
        user_id: UUID,
        users_service: UserService,
    ) -> UserRead:
        """Get user details."""
        db_obj = await users_service.get(user_id)
        return UserRead.from_orm(db_obj)
    
    @post(
        "/",
        operation_id="CreateUser",
        guards=[requires_superuser],
    )
    async def create_user(
        self,
        data: UserCreate,
        users_service: UserService,
    ) -> UserRead:
        """Create new user."""
        db_obj = await users_service.create(data.model_dump())
        return UserRead.from_orm(db_obj)
    
    @put(
        "/{user_id:uuid}",
        operation_id="UpdateUser",
    )
    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
        users_service: UserService,
        current_user: User,
    ) -> UserRead:
        """Update user."""
        # Authorization check
        if user_id != current_user.id and not current_user.is_superuser:
            raise PermissionDeniedException()
        
        db_obj = await users_service.update(
            item_id=user_id,
            data=data.model_dump(exclude_unset=True)
        )
        return UserRead.from_orm(db_obj)
```

## Dependency Injection

### Service Providers

Configure services with loading strategies:

```python
# server/deps.py
from app.lib.deps import create_service_provider
from sqlalchemy.orm import selectinload, joinedload, load_only

provide_users_service = create_service_provider(
    UserService,
    load=[
        # Eager load relationships
        selectinload(m.User.roles).options(
            joinedload(m.UserRole.role, innerjoin=True)
        ),
        selectinload(m.User.teams).options(
            joinedload(m.TeamMember.team, innerjoin=True).options(
                load_only(m.Team.name, m.Team.slug)
            ),
        ),
    ],
    # Ensure unique results
    uniquify=True,
    # Custom error messages
    error_messages={
        "duplicate_key": "This email is already registered.",
        "integrity": "User operation failed.",
        "not_found": "User not found.",
    },
)
```

### Using Dependencies in Routes

```python
@Controller(
    dependencies={
        "users_service": Provide(provide_users_service),
        "teams_service": Provide(provide_teams_service),
    }
)
class TeamMemberController:
    """Team member management."""
    
    @post("/teams/{team_id:uuid}/members")
    async def add_member(
        self,
        team_id: UUID,
        data: AddMemberRequest,
        users_service: UserService,
        teams_service: TeamService,
    ) -> TeamMemberRead:
        """Add member to team."""
        # Services are injected automatically
```

## Async Patterns

### Concurrent Operations

```python
async def get_user_dashboard(self, user_id: UUID) -> DashboardData:
    """Get dashboard data with concurrent queries."""
    # Run multiple queries concurrently
    user, teams, notifications = await asyncio.gather(
        self.users_service.get(user_id),
        self.teams_service.list(user_id=user_id),
        self.notifications_service.count_unread(user_id),
    )
    
    return DashboardData(
        user=user,
        teams=teams,
        unread_count=notifications,
    )
```

### Async Context Managers

```python
async def process_large_dataset(self) -> None:
    """Process data in chunks."""
    async with self.repository.session() as session:
        # Stream results
        async for chunk in self.repository.stream_in_chunks(100):
            await self.process_chunk(chunk)
```

## Error Handling

### Custom Exceptions

```python
# lib/exceptions.py
from litestar.exceptions import HTTPException

class ApplicationException(HTTPException):
    """Base application exception."""
    status_code = 500

class ClientException(ApplicationException):
    """Client error (4xx)."""
    status_code = 400

class PermissionDeniedException(ApplicationException):
    """Permission denied (403)."""
    status_code = 403
    detail = "Permission denied"

class ResourceNotFoundException(ApplicationException):
    """Resource not found (404)."""
    status_code = 404
    detail = "Resource not found"
```

### Exception Handling in Services

```python
async def get_team_member(
    self, 
    team_id: UUID, 
    user_id: UUID
) -> TeamMember:
    """Get team member with proper error handling."""
    member = await self.repository.get_one_or_none(
        team_id=team_id,
        user_id=user_id,
    )
    
    if member is None:
        raise ResourceNotFoundException(
            detail=f"Member {user_id} not found in team {team_id}"
        )
    
    return member
```

## Performance Optimization

### Query Optimization

```python
# Avoid N+1 queries with proper loading
users = await self.repository.list(
    User.is_active == True,
    load=[
        selectinload(User.teams),
        selectinload(User.roles),
    ],
)

# Use specific columns when needed
team_names = await self.repository.list(
    load_only=[Team.id, Team.name],
)
```

### Caching with Redis

```python
from app.lib.cache import cache

async def get_user_permissions(self, user_id: UUID) -> list[str]:
    """Get user permissions with caching."""
    cache_key = f"permissions:{user_id}"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Compute permissions
    permissions = await self._compute_permissions(user_id)
    
    # Cache for 5 minutes
    await cache.set(cache_key, permissions, ttl=300)
    
    return permissions
```

## Background Tasks

### Using SAQ for Job Queues

```python
# server/jobs/email.py
from app.lib.worker import job

@job("send_email")
async def send_welcome_email(user_id: str) -> None:
    """Send welcome email in background."""
    user = await users_service.get(UUID(user_id))
    await email_service.send_welcome(user)

# Queue the job
await send_welcome_email.enqueue(str(user.id))
```

## Best Practices

### 1. Always Use Type Annotations

```python
async def create_team(
    self,
    name: str,
    owner_id: UUID,
    description: str | None = None,
) -> Team:
    """Create team with type safety."""
```

### 2. Transaction Management

```python
async def transfer_ownership(
    self, 
    team_id: UUID, 
    new_owner_id: UUID
) -> None:
    """Transfer team ownership in transaction."""
    async with self.repository.transaction():
        # All operations in same transaction
        team = await self.get(team_id)
        old_owner = await self.remove_member(team_id, team.owner_id)
        new_owner = await self.add_member(team_id, new_owner_id, "OWNER")
        team.owner_id = new_owner_id
        await self.repository.update(team)
```

### 3. Validation at Service Layer

```python
async def create_user(self, data: dict) -> User:
    """Create user with validation."""
    # Validate email format
    if not self._is_valid_email(data["email"]):
        raise ClientException("Invalid email format")
    
    # Check uniqueness
    existing = await self.get_one_or_none(email=data["email"])
    if existing:
        raise ClientException("Email already registered")
    
    # Create user
    return await self.repository.add(User(**data))
```

## Next Steps

Now that you understand the backend architecture:

1. Learn about [Authentication & Security](04-authentication-security.md)
2. Explore [Frontend Architecture](05-frontend-architecture.md)
3. Review [Development Workflow](06-development-workflow.md)

---

*The backend architecture prioritizes type safety, performance, and maintainability. Following these patterns ensures consistent, high-quality code across the application.*