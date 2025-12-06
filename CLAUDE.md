# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Setup

```bash
make install                    # Fresh installation (Python + Node)
cp .env.local.example .env      # Setup environment
make start-infra                # Start PostgreSQL + Redis + MailHog
uv run app run                  # Start all services (SAQ, Vite, Litestar)
```

### Critical Development Commands

```bash
make types                      # ALWAYS run after backend schema changes
make lint                       # Run all linting (Python + JS)
make test                       # Run Python tests
make check-all                  # Run ALL checks before commit

# Testing
uv run pytest src/py/tests/integration/test_email_verification.py -xvs  # Single test
make test-coverage              # With coverage
make test-all                   # All tests including integration

# Database
app database upgrade            # Apply migrations
app database make-migrations    # Create new migration
```

## Architecture Overview

### Backend (Litestar + SQLAlchemy)

**Service Pattern with Inner Repository** - Always use this pattern:

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m

class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Service for user operations."""
    
    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        """User repository."""
        model_type = m.User
    
    repository_type = Repo
    
    # Custom service methods here
```

**msgspec Schema Pattern** - NEVER use dicts or Pydantic:

```python
import msgspec

class UserCreate(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """User creation payload."""
    email: str
    password: str
    name: str | None = None
```

**Key Architectural Decisions:**

- **msgspec.Struct** for ALL API DTOs (performance + validation)
- **Service/Repository pattern** for ALL database operations
- **Advanced Alchemy base classes** (UUIDAuditBase) for models
- **JWT authentication** with email verification, password reset, 2FA/TOTP
- **OAuth integration** via Google OAuth (frontend pending)
- **SAQ** for background tasks with Redis
- **Granian** as ASGI server with uvloop

### Frontend (React + Vite + TanStack)

- **React 19** with TypeScript
- **TanStack Router** for routing
- **TanStack Query** for data fetching
- **TanStack Form** with Zod validation
- **Tailwind CSS v4** with Radix UI components
- **Auto-generated API client** from OpenAPI schema

### Project Structure

```
src/py/app/
├── db/models/          # SQLAlchemy models (use Mapped[] typing)
├── schemas/            # msgspec.Struct DTOs
├── services/           # Business logic (inner Repo pattern)
├── server/routes/      # Litestar controllers
└── lib/                # Core utilities

src/js/src/
├── components/         # React components
├── routes/             # TanStack Router pages
├── lib/api/            # Auto-generated from OpenAPI
└── hooks/              # React hooks
```

## Development Workflow

### Adding New Features

1. Create/update SQLAlchemy models in `db/models/`
2. Run `app database make-migrations`
3. Create msgspec schemas in `schemas/`
4. Implement service with inner Repo pattern in `services/`
5. Add controller routes in `server/routes/`
6. Register routes in `routes/__init__.py`
7. Update `signature_namespace` if adding new schemas
8. **Run `make types`** to generate TypeScript client
9. Implement frontend in React

### Before Every Commit

1. `make lint` - Fix all linting issues
2. `make test` - Ensure tests pass
3. `make check-all` - Final validation

## Testing Guidelines

- Use pytest functions (not classes) unless instructed otherwise
- Group and parameterize test cases for efficiency
- Integration tests in `src/py/tests/integration/`
- Unit tests in `src/py/tests/unit/`

## Development Infrastructure

### MailHog (Email Testing)

- Web UI: <http://localhost:18025>
- SMTP: localhost:11025
- Access: `make mailhog`
- All dev emails are caught here

## Critical Rules

**ALWAYS:**

- Run `make types` after schema changes
- Use msgspec.Struct for DTOs
- Use service/repository pattern
- Type all function signatures
- Handle async operations correctly

**NEVER:**

- Use raw dicts for API responses
- Access DB sessions directly
- Skip running tests
- Commit without `make check-all`
- Create files unless necessary
- Add comments/emojis unless requested
