# Project Structure

## Overview

The Litestar Fullstack SPA follows a monorepo structure with clear separation between backend (Python) and frontend (JavaScript/TypeScript) code. This organization promotes maintainability and allows for independent scaling of components.

## Directory Layout

```
litestar-fullstack-spa/
├── src/                        # All source code
│   ├── py/                     # Python backend
│   │   ├── app/                # Main application package
│   │   └── tests/              # Python tests
│   └── js/                     # JavaScript/TypeScript frontend
│       ├── src/                # React application source
│       ├── public/             # Static assets
│       └── package.json        # Frontend dependencies
├── docs/                       # Documentation
│   ├── architecture/           # This documentation
│   └── api/                    # Auto-generated API docs
├── tools/                      # Build and deployment scripts
│   ├── deploy/                 # Deployment configurations
│   │   ├── docker/             # Docker files
│   │   └── k8s/                # Kubernetes manifests
│   └── *.py                    # Utility scripts
├── pyproject.toml              # Python project configuration
├── Makefile                    # Common development tasks
└── .env.local.example          # Environment variables template
```

## Backend Structure (src/py/app/)

### Core Application Components

```
app/
├── __init__.py                 # Package initialization
├── __main__.py                 # Entry point for CLI
├── config.py                   # Application configuration
├── cli/                        # Command-line interface
│   └── commands.py             # CLI command definitions
├── db/                         # Database layer
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py             # User model
│   │   ├── team.py             # Team model
│   │   └── ...                 # Other domain models
│   ├── migrations/             # Alembic migrations
│   │   ├── versions/           # Migration files
│   │   └── env.py              # Migration environment
│   └── fixtures/               # Initial data fixtures
├── schemas/                    # API DTOs (msgspec.Struct)
│   ├── accounts.py             # User-related schemas
│   ├── teams.py                # Team-related schemas
│   └── base.py                 # Base schema classes
├── services/                   # Business logic layer
│   ├── _users.py               # User service
│   ├── _teams.py               # Team service
│   └── ...                     # Other services
├── server/                     # Web server components
│   ├── routes/                 # API controllers
│   │   ├── access.py           # Authentication endpoints
│   │   ├── user.py             # User management
│   │   └── team.py             # Team management
│   ├── security.py             # Security configuration
│   ├── plugins.py              # Litestar plugins
│   └── asgi.py                 # ASGI application
└── lib/                        # Shared utilities
    ├── deps.py                 # Dependency injection
    ├── exceptions.py           # Custom exceptions
    ├── crypt.py                # Cryptography utilities
    └── settings.py             # Settings management
```

### Key Backend Patterns

#### 1. Models (db/models/)

SQLAlchemy 2.0 models with full type annotations:

```python
# db/models/user.py
from sqlalchemy.orm import Mapped, mapped_column
from advanced_alchemy.base import UUIDAuditBase

class User(UUIDAuditBase):
    """User account model."""
    __tablename__ = "user_account"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
```

#### 2. Schemas (schemas/)

msgspec.Struct for high-performance API serialization:

```python
# schemas/accounts.py
import msgspec

class UserCreate(msgspec.Struct):
    """User creation payload."""
    email: str
    password: str
    name: str | None = None
```

#### 3. Services (services/)

Business logic with repository pattern:

```python
# services/_users.py
from litestar.plugins.sqlalchemy import service, repository

class UserService(service.SQLAlchemyAsyncRepositoryService[User]):
    """Handles user operations."""

    class Repo(repository.SQLAlchemyAsyncRepository[User]):
        model_type = User

    repository_type = Repo
```

#### 4. Routes (server/routes/)

Litestar controllers for API endpoints:

```python
# server/routes/user.py
from litestar import Controller, get, post

@Controller(path="/api/users")
class UserController:
    @get("/{user_id:uuid}")
    async def get_user(self, user_id: UUID) -> UserRead:
        """Get user by ID."""
```

## Frontend Structure (src/js/)

### React Application Organization

```
src/
├── components/                 # React components
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx          # Button component
│   │   ├── card.tsx            # Card component
│   │   └── ...                 # Other UI components
│   ├── auth/                   # Authentication components
│   │   ├── login.tsx           # Login form
│   │   └── signup.tsx          # Registration form
│   ├── teams/                  # Team management
│   └── admin/                  # Admin interfaces
├── routes/                     # TanStack Router pages
│   ├── __root.tsx              # Root layout
│   ├── _app.tsx                # Authenticated layout
│   ├── _public.tsx             # Public layout
│   └── index.tsx               # Route exports
├── lib/                        # Utilities and shared code
│   ├── api/                    # API client
│   │   ├── client.gen.ts       # Generated client
│   │   ├── types.gen.ts        # Generated types
│   │   └── index.ts            # API exports
│   ├── auth.ts                 # Auth utilities
│   └── utils.ts                # Helper functions
├── hooks/                      # Custom React hooks
│   ├── use-auth.ts             # Authentication hook
│   └── use-mobile.ts           # Responsive design
└── main.tsx                    # Application entry point
```

### Frontend Patterns

#### 1. Components Structure

Components follow a consistent pattern:

```typescript
// components/teams/team-list.tsx
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

export function TeamList() {
  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: () => api.teams.listTeams()
  });

  return (
    <div className="grid gap-4">
      {teams?.map(team => (
        <Card key={team.id}>
          {/* Team content */}
        </Card>
      ))}
    </div>
  );
}
```

#### 2. Route Organization

File-based routing with TanStack Router:

```
routes/
├── _app/                       # Authenticated routes
│   ├── teams.tsx               # /teams
│   └── teams/
│       ├── $teamId.tsx         # /teams/:teamId
│       └── new.tsx             # /teams/new
└── _public/                    # Public routes
    ├── login.tsx               # /login
    └── signup.tsx              # /signup
```

## Configuration Files

### Python Configuration (pyproject.toml)

```toml
[project]
name = "app"
dependencies = [
    "litestar[standard]>=2.0",
    "advanced-alchemy>=0.1",
    "msgspec>=0.18",
]

[tool.pytest.ini_options]
testpaths = ["src/py/tests"]

[tool.ruff]
target-version = "py311"
```

### Frontend Configuration

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "biome check --write"
  }
}
```

## Development Workflow Files

### Makefile

Common tasks automated:

```makefile
install:
	uv sync --frozen --all-extras

start-infra:
	docker-compose -f tools/deploy/docker/docker-compose.yml up -d

types:
	uv run app export-openapi-schema
	cd src/js && npm run generate-types

test:
	uv run pytest

lint:
	uv run pre-commit run --all-files
```

### Docker Development

```yaml
# tools/deploy/docker/docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Testing Structure

### Backend Tests

```
tests/
├── unit/                       # Unit tests
│   ├── test_services/          # Service tests
│   ├── test_models/            # Model tests
│   └── test_lib/               # Utility tests
└── integration/                # Integration tests
    ├── test_access.py          # Auth flow tests
    └── test_teams.py           # Team API tests
```

### Frontend Tests

```
src/__tests__/
├── components/                 # Component tests
├── hooks/                      # Hook tests
└── utils/                      # Utility tests
```

## Best Practices

### File Naming Conventions

- **Python**: Snake case (`user_service.py`)
- **TypeScript**: Kebab case (`user-list.tsx`)
- **Tests**: Prefix with `test_` (Python) or `.test.` (TypeScript)

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Python example
import asyncio
from datetime import datetime

from litestar import Controller
from sqlalchemy import select

from app.db import models
from app.services import UserService
```

```typescript
// TypeScript example
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
```

### Code Organization Tips

1. **Keep files focused** - Single responsibility per file
2. **Use consistent patterns** - Follow established conventions
3. **Colocate related code** - Group by feature, not file type
4. **Document complex logic** - Add comments for non-obvious code
5. **Extract reusable code** - Move to lib/ or hooks/

## Next Steps

Understanding the project structure helps you:

1. Navigate the codebase efficiently
2. Know where to add new features
3. Follow established patterns
4. Maintain consistency

Continue to [Backend Architecture](03-backend-architecture.md) for deep dive into service patterns and database design.

---

*This structure promotes scalability, maintainability, and developer productivity. Each directory has a clear purpose, making it easy to locate and organize code.*
