---
description: Testing workflow with 90%+ coverage target
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Testing Workflow

Testing feature: **$ARGUMENTS**

## Pre-Testing Verification

1. Verify implementation exists for the feature
2. Load task list from `specs/active/{slug}/tasks.md`
3. Identify all files that need tests

---

## Testing Protocol

### Step 1: Identify Test Targets

Find all files modified for this feature:

```bash
git diff --name-only main... | grep -E "\.py$"
```

Or check recovery.md for list of modified files.

### Step 2: Create Test Structure

For each domain area, create test files:

```
src/py/tests/
├── unit/
│   └── test_{domain}/
│       ├── test_services.py
│       └── test_schemas.py
└── integration/
    └── test_{feature}.py
```

### Step 3: Write Unit Tests

**Testing Guidelines (from CLAUDE.md):**

- Use pytest functions (not classes)
- Group and parameterize test cases
- Use `@pytest.mark.asyncio` for async tests
- Use polyfactory for test data

**Service Test Pattern:**

```python
import pytest
from polyfactory.factories import TypedDictFactory
from app.domain.{domain}.services import {Feature}Service

@pytest.mark.asyncio
async def test_{feature}_create(db_session):
    """Test creating a {feature}."""
    service = {Feature}Service(session=db_session)
    data = {"field": "value"}

    result = await service.create(data)

    assert result.field == "value"
    assert result.id is not None


@pytest.mark.asyncio
async def test_{feature}_get_by_id(db_session):
    """Test getting {feature} by ID."""
    service = {Feature}Service(session=db_session)
    created = await service.create({"field": "value"})

    result = await service.get(created.id)

    assert result.id == created.id


@pytest.mark.asyncio
async def test_{feature}_not_found(db_session):
    """Test {feature} not found raises exception."""
    from uuid import uuid4
    from advanced_alchemy.exceptions import NotFoundError

    service = {Feature}Service(session=db_session)

    with pytest.raises(NotFoundError):
        await service.get(uuid4())
```

**Schema Test Pattern:**

```python
import pytest
from app.domain.{domain}.schemas import {Feature}Create

def test_{feature}_create_schema_valid():
    """Test valid schema creation."""
    schema = {Feature}Create(field="value")
    assert schema.field == "value"


def test_{feature}_create_schema_to_dict():
    """Test schema to_dict method."""
    schema = {Feature}Create(field="value")
    result = schema.to_dict()
    assert isinstance(result, dict)
    assert result["field"] == "value"
```

### Step 4: Write Integration Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{feature}_api_create(client: AsyncClient, auth_headers: dict):
    """Test creating {feature} via API."""
    response = await client.post(
        "/api/{features}",
        json={"field": "value"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["field"] == "value"


@pytest.mark.asyncio
async def test_{feature}_api_list(client: AsyncClient, auth_headers: dict):
    """Test listing {features} via API."""
    response = await client.get(
        "/api/{features}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Step 5: Run Tests with Coverage

```bash
# Run all tests
make test

# Run specific test file
uv run pytest src/py/tests/unit/test_{domain}/test_services.py -xvs

# Run with coverage
make test-coverage

# Check coverage for modified files
uv run pytest --cov=app.domain.{domain} --cov-report=term-missing
```

### Step 6: Verify Coverage Target

**Target: 90%+ coverage for modified modules**

```bash
# Generate coverage report
uv run pytest --cov=app --cov-report=html

# Check specific module coverage
uv run pytest --cov=app.domain.{domain} --cov-fail-under=90
```

### Step 7: Test Edge Cases

Ensure tests cover:

- [ ] Happy path
- [ ] Invalid input validation
- [ ] Not found scenarios
- [ ] Permission denied scenarios
- [ ] Duplicate entry handling
- [ ] Empty list/data scenarios
- [ ] Pagination (if applicable)
- [ ] Filtering (if applicable)

---

## Quality Gates

```bash
# All tests must pass
make test

# Linting must pass
make lint

# Type checking must pass
make check-all
```

---

## Automatic Review Trigger

After all tests pass with 90%+ coverage:

```
/review {slug}
```

---

## Troubleshooting

### Test Discovery Issues

```bash
# Check test discovery
uv run pytest --collect-only

# Verbose test run
uv run pytest -xvs
```

### Database Issues

```bash
# Reset test database
make test-db-reset

# Check migrations
app database upgrade
```

### Async Test Issues

Ensure tests use:
```python
@pytest.mark.asyncio
async def test_async_function():
    ...
```

And check `conftest.py` has proper fixtures.
