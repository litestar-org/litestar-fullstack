---
description: Explore and understand codebase patterns
allowed-tools: Read, Glob, Grep, Bash, Task, mcp__pal__analyze
---

# Codebase Exploration

Exploring: **$ARGUMENTS**

## Exploration Modes

Based on your query, select the appropriate mode:

### Mode 1: Architecture Overview

For questions like "How is the project structured?" or "What's the architecture?"

```bash
# Project structure
tree -L 3 -I "node_modules|__pycache__|.venv|.git" src/

# Backend domains
ls src/py/app/domain/

# Frontend structure
ls src/js/src/
```

### Mode 2: Pattern Discovery

For questions like "How do services work?" or "How are schemas defined?"

1. Find examples:
```bash
# Find all services
find src/py/app/domain -name "services" -type d

# Find all schemas
find src/py/app/domain -name "schemas.py"

# Find all controllers
find src/py/app/domain -name "controllers" -type d
```

2. Read representative examples:
- Service: `src/py/app/domain/accounts/services/_user.py`
- Schema: `src/py/app/domain/accounts/schemas.py`
- Model: `src/py/app/db/models/user.py`
- Controller: `src/py/app/domain/accounts/controllers/`

### Mode 3: Feature Location

For questions like "Where is X implemented?" or "How does Y work?"

```bash
# Search for feature keywords
grep -r "keyword" src/py/app/ --include="*.py" | head -20

# Find related files
find src/ -name "*keyword*" -type f
```

### Mode 4: Dependency Analysis

For questions like "What uses X?" or "What does Y depend on?"

```bash
# Find imports of a module
grep -r "from app.domain.accounts" src/py/ --include="*.py"

# Find usages of a class
grep -r "UserService" src/py/ --include="*.py"
```

### Mode 5: Deep Analysis

For complex questions requiring multi-step analysis, use the `mcp__pal__analyze` tool:

```python
mcp__pal__analyze(
    step="Analyzing {topic}",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    findings="Initial observations...",
    analysis_type="architecture",  # or "performance", "security", "quality"
    relevant_files=["src/py/app/..."]
)
```

---

## Common Exploration Queries

### Backend Architecture

**Q: How do API routes work?**
- Entry point: `src/py/app/server/routes/__init__.py`
- Controllers: `src/py/app/domain/*/controllers/`
- Route registration in `server/core.py`

**Q: How does authentication work?**
- JWT handling: `src/py/app/domain/accounts/`
- Guards: `src/py/app/domain/accounts/guards.py`
- Dependencies: `src/py/app/domain/accounts/dependencies.py`

**Q: How do database models work?**
- Models: `src/py/app/db/models/`
- Base class: `UUIDAuditBase` from `advanced_alchemy`
- Migrations: `src/py/app/db/migrations/`

**Q: How do services work?**
- Pattern: Inner Repository in service class
- Example: `src/py/app/domain/accounts/services/_user.py`
- Base: `SQLAlchemyAsyncRepositoryService`

### Frontend Architecture

**Q: How does routing work?**
- TanStack Router: `src/js/src/routes/`
- Route tree: `src/js/src/routeTree.gen.ts` (auto-generated)

**Q: How does data fetching work?**
- TanStack Query hooks in `src/js/src/hooks/`
- API client in `src/js/src/lib/api/`

**Q: How are components organized?**
- Components: `src/js/src/components/`
- UI primitives: Radix UI based
- Styling: Tailwind CSS v4

### Testing

**Q: How do I write tests?**
- Unit tests: `src/py/tests/unit/`
- Integration tests: `src/py/tests/integration/`
- Fixtures: `src/py/tests/conftest.py`

### Configuration

**Q: Where is configuration?**
- Python config: `src/py/app/config.py`
- Settings: `src/py/app/lib/settings.py`
- Environment: `.env` files

---

## Quick Reference Commands

```bash
# Count lines of code
find src/py/app -name "*.py" | xargs wc -l | tail -1

# Find all async functions
grep -r "async def" src/py/app/ | wc -l

# List all database models
grep -r "class.*UUIDAuditBase" src/py/app/db/models/

# List all API routes
grep -r "@get\|@post\|@put\|@delete\|@patch" src/py/app/domain/

# Find all React components
find src/js/src/components -name "*.tsx" | head -20
```

---

## Pattern Documentation

After exploration, consider documenting findings in:
- `specs/guides/patterns/` - For reusable patterns
- `specs/guides/workflows/` - For workflow documentation
- `specs/guides/examples/` - For code examples
