---
description: Pattern-guided implementation with quality gates
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs, mcp__pal__thinkdeep, mcp__pal__debug
---

# Pattern-Guided Implementation Workflow

Implementing feature: **$ARGUMENTS**

## Pre-Implementation Verification

**MANDATORY CHECKS:**

1. Verify PRD exists at `specs/active/{slug}/prd.md`
2. Load task list from `specs/active/{slug}/tasks.md`
3. Read patterns identified in PRD
4. Load MCP strategy from `.claude/mcp-strategy.md`

If PRD doesn't exist, STOP and run `/prd {feature}` first.

---

## Implementation Protocol

### Step 1: Load Intelligence Context

1. Read `specs/active/{slug}/prd.md` - Extract requirements
2. Read `specs/active/{slug}/tasks.md` - Get task list
3. Read similar implementations identified in PRD
4. Read `specs/guides/patterns/README.md` - Refresh pattern knowledge

### Step 2: Pattern Deep Dive

Before writing ANY code:

1. Read 3-5 similar implementations completely
2. Extract exact class structure from examples
3. Note all naming conventions
4. Understand error handling patterns
5. Check import patterns and dependencies

### Step 3: Implement Following Task List

For each task in `specs/active/{slug}/tasks.md`:

1. **Mark task as in-progress** in tasks.md
2. **Follow pattern exactly** from similar implementations
3. **Write code** matching project conventions
4. **Run tests** after each significant change:
   ```bash
   make test
   ```
5. **Run linting** to catch issues early:
   ```bash
   make lint
   ```
6. **Mark task complete** when verified

### Step 4: Pattern Compliance Checklist

Before marking any file complete:

- [ ] Follows service pattern with inner Repo class
- [ ] Uses CamelizedBaseStruct for schemas (not dicts or Pydantic)
- [ ] Models inherit from UUIDAuditBase
- [ ] Uses `Mapped[]` typing for all model fields
- [ ] Type hints on all function signatures
- [ ] Async operations handled correctly
- [ ] Error handling matches project patterns
- [ ] No raw dicts in API responses

### Step 5: Document New Patterns

If you discover new patterns during implementation:

Write to `specs/active/{slug}/tmp/new-patterns.md`:

```markdown
## New Pattern: {Pattern Name}

### Description
{What this pattern does}

### Example
```python
{Code example}
```

### When to Use
{Use cases}
```

### Step 6: Quality Gates

After implementation:

```bash
# Run all checks
make check-all

# Verify tests pass
make test

# Run linting
make lint

# Generate TypeScript client (if schemas changed)
make types
```

### Step 7: Update Recovery Guide

Update `specs/active/{slug}/recovery.md` with:
- Files modified
- Current progress
- Any issues encountered
- Next steps

---

## Automatic Agent Chain

After all implementation tasks are complete, automatically invoke the following agents **in sequence**:

### 1. Testing Agent

```bash
/test {slug}
```

Wait for testing to complete with 90%+ coverage.

### 2. Docs & Vision Agent (MANDATORY)

After tests pass, **ALWAYS** invoke:

```bash
/review {slug}
```

The docs-vision agent will:
- Enforce quality gates
- Extract new patterns to `specs/guides/patterns/`
- Update LLM guides (`CLAUDE.md`, `specs/guides/`) if patterns changed
- Update user-facing documentation (`docs/`, `README.md`) if applicable
- Archive the feature spec on approval

**This step is MANDATORY and must not be skipped.**

---

## Implementation Patterns Reference

### Creating a New Service

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m

class NewFeatureService(service.SQLAlchemyAsyncRepositoryService[m.NewFeature]):
    """Service for new feature operations."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.NewFeature]):
        """Repository."""
        model_type = m.NewFeature

    repository_type = Repo
    match_fields = ["unique_field"]
```

### Creating a New Schema

```python
from app.schemas.base import CamelizedBaseStruct

class NewFeatureCreate(CamelizedBaseStruct):
    """Create payload."""
    name: str
    description: str | None = None
```

### Creating a New Model

```python
from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column

class NewFeature(UUIDAuditBase):
    __tablename__ = "new_feature"

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
```

### Creating a Controller

```python
from litestar import Controller, get, post
from litestar.di import Provide

class NewFeatureController(Controller):
    path = "/new-features"
    dependencies = {"service": Provide(provide_new_feature_service)}

    @get()
    async def list(self, service: NewFeatureService) -> list[NewFeature]:
        return await service.list()

    @post()
    async def create(self, data: NewFeatureCreate, service: NewFeatureService) -> NewFeature:
        return await service.create(data.to_dict())
```

---

## Error Recovery

If implementation fails:

1. Check error message carefully
2. Run `mcp__pal__debug` for complex issues
3. Update recovery.md with issue details
4. Consult Context7 for library-specific solutions
5. Check similar implementations for patterns
