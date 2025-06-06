# CLAUDE.md - Development Quick Reference

This file provides essential guidance for Claude Code when working with the Litestar Fullstack SPA project. For comprehensive architecture documentation, see `docs/architecture/`.

## 🚀 Quick Commands

```bash
# Setup
make install                    # Fresh installation
cp .env.local.example .env      # Setup environment  
make start-infra                # Start PostgreSQL + Redis
uv run app run                  # Start all services

# Development
make types                      # Generate TypeScript types (ALWAYS after schema changes!)
make lint                       # Run all linting
make check-all                  # Run all checks before commit
make test                       # Run Python tests

# Database
app database upgrade            # Run migrations
app database make-migrations    # Create new migration
```

## 🎯 Critical Development Rules

### ALWAYS

- Run `make types` after ANY backend schema changes
- Run `make lint` after code changes
- Run `make check-all` before committing
- Use msgspec.Struct for ALL API DTOs (NEVER raw dicts or Pydantic)
- Use the inner `Repo` pattern for services
- Use Advanced Alchemy base classes (UUIDAuditBase)
- Type all function signatures properly
- Handle async operations correctly

### NEVER

- Create files unless absolutely necessary
- Create documentation files unless explicitly requested
- Use raw dicts for API responses
- Access database sessions directly (use services)
- Commit without running tests
- Add comments unless requested
- Use emojis unless requested

## 📁 Quick Structure Reference

```
src/py/app/
├── db/models/          # SQLAlchemy models (use Mapped[])
├── schemas/            # msgspec.Struct DTOs (API contracts)
├── services/           # Business logic (inner Repo pattern)
├── server/routes/      # Litestar controllers
└── lib/                # Core utilities

src/js/src/
├── components/         # React components
├── routes/             # TanStack Router pages
├── lib/api/            # Auto-generated client
└── hooks/              # React hooks
```

## 🔥 Service Pattern (Copy This!)

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

## 🔐 Current Authentication Features

- JWT-based authentication
- Email verification (with tokens)
- Password reset flow (with security tracking)
- 2FA/TOTP support (configurable)
- OAuth Google Integration (backend complete, frontend pending)
- Rate limiting on sensitive operations
- Configurable security requirements

## 📝 Schema Pattern (Copy This!)

```python
import msgspec

class UserCreate(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
    """User creation payload."""
    email: str
    password: str
    name: str | None = None
```

## 🚨 Common Pitfalls to Avoid

1. **Forgetting `make types`** - Frontend will have type errors
2. **Using dict instead of msgspec.Struct** - Performance and validation issues
3. **Direct DB access** - Always use service repositories
4. **Blocking operations in async** - Use async/await properly
5. **Not running tests** - Breaks in CI/CD

## 🧪 Testing Commands

```bash
# Run specific test
uv run pytest src/py/tests/integration/test_email_verification.py -xvs

# Run with coverage
make test-coverage

# Run integration tests
make test-all
```

## 🔄 Workflow Reminders

1. **New Feature Flow:**
   - Create/update models
   - Run `app database make-migrations`
   - Create msgspec schemas
   - Implement service with inner Repo
   - Add controller routes
   - Register in `routes/__init__.py`
   - Update `signature_namespace` if needed
   - Run `make types`
   - Implement frontend

2. **Before Every Commit:**
   - `make lint`
   - `make test`
   - `make check-all`

## 📊 Current Work Context

- Email verification: ✅ Implemented
- Password reset: ✅ Implemented  
- 2FA/TOTP: ✅ Implemented (configurable)
- OAuth: Backend ✅ | Frontend ❌ | Tests ❌
- Production validation: Backend 70% ✅ | Frontend ❌ | Tests ❌
- Rate limiting: ✅ Basic implementation

For detailed patterns and examples, see `docs/architecture/`.
