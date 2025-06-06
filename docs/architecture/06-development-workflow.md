# Development Workflow

## Overview

This guide covers the essential commands, workflows, and practices for developing with the Litestar Fullstack SPA. From initial setup to deployment, you'll find everything needed for productive development.

## Initial Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- uv (Python package manager)

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd litestar-fullstack-spa

# 2. Install dependencies
make install

# 3. Setup environment
cp .env.local.example .env

# 4. Start infrastructure
make start-infra

# 5. Run migrations
uv run app database upgrade

# 6. Start development server
uv run app run
```

Your application is now running at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/schema

## Key Commands

### Makefile Commands

The Makefile provides convenient shortcuts for common tasks:

```bash
# Development
make install          # Fresh installation (destroys existing env)
make start-infra      # Start PostgreSQL + Redis containers
make stop-infra       # Stop infrastructure containers
make run              # Start development server

# Code Quality
make lint             # Run all linting (pre-commit, mypy, pyright)
make test             # Run Python unit tests
make test-all         # Run all tests including integration
make check-all        # Run all checks (lint + test + coverage)

# Frontend
make types            # Generate TypeScript types from OpenAPI
make frontend-dev     # Start frontend dev server only
make frontend-build   # Build frontend for production

# Database
make migrations       # Create new migration
make migrate          # Apply migrations
make reset-db         # Reset database (WARNING: destroys data)
```

### CLI Commands

The application provides a CLI for various tasks:

```bash
# Database commands
uv run app database                    # Show all database commands
uv run app database upgrade            # Apply migrations
uv run app database downgrade          # Rollback migrations
uv run app database make-migrations    # Create new migration
uv run app database show               # Show current revision

# User management
uv run app users                       # Show user commands
uv run app users create-superuser      # Create admin user
uv run app users list                  # List all users
uv run app users promote --email user@example.com  # Make superuser

# Development server
uv run app run                         # Start all services
uv run app run --host 0.0.0.0          # Bind to all interfaces
uv run app run --reload                # Auto-reload on changes
uv run app run-worker                  # Run worker only
uv run app run-server                  # Run server only

# Schema export
uv run app export-openapi-schema       # Export OpenAPI schema
uv run app export-typescript-types     # Generate TS types
```

## Development Environment

### Environment Variables

Configure your `.env` file based on the template:

```bash
# Application
APP_ENV=local
APP_SECRET_KEY=your-secret-key-here
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (development with Mailhog)
EMAIL_DELIVERY_METHOD=smtp
EMAIL_SMTP_HOST=localhost
EMAIL_SMTP_PORT=1025
EMAIL_SMTP_USE_TLS=false
EMAIL_FROM_ADDRESS=dev@example.com
EMAIL_FROM_NAME="Dev App"

# Authentication
AUTH_REQUIRE_EMAIL_VERIFICATION=false
AUTH_ENABLE_2FA=false
AUTH_PASSWORD_MIN_LENGTH=8

# Frontend
VITE_API_URL=http://localhost:8000
VITE_APP_NAME="Litestar App"
```

### Docker Development

#### Starting Services

```bash
# Start all infrastructure
docker-compose -f tools/deploy/docker/docker-compose.yml up -d

# Start specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: destroys data)
docker-compose down -v
```

#### Using Mailhog for Email Testing

```bash
# Start Mailhog
docker run -d \
  --name mailhog \
  -p 1025:1025 \
  -p 8025:8025 \
  mailhog/mailhog

# Access Mailhog UI
open http://localhost:8025

# Configure in .env
EMAIL_SMTP_HOST=localhost
EMAIL_SMTP_PORT=1025
```

## Database Workflows

### Creating Migrations

```bash
# 1. Make model changes in db/models/

# 2. Generate migration
uv run app database make-migrations "Add user preferences"

# 3. Review generated migration
cat src/py/app/db/migrations/versions/*_add_user_preferences.py

# 4. Apply migration
uv run app database upgrade

# 5. Test rollback (optional)
uv run app database downgrade -1
uv run app database upgrade
```

### Database Management

```bash
# Check current revision
uv run app database show

# Upgrade to latest
uv run app database upgrade head

# Downgrade one revision
uv run app database downgrade -1

# Upgrade to specific revision
uv run app database upgrade abc123

# Generate SQL for review
uv run app database upgrade --sql
```

## API Development

### Adding New Endpoints

1. **Create Schema** (if needed):
```python
# schemas/products.py
import msgspec
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

class ProductCreate(msgspec.Struct):
    name: str
    price: float
    description: str | None = None

class ProductRead(msgspec.Struct):
    id: UUID
    name: str
    price: float
    description: str | None = None
```

2. **Create Service**:
```python
# services/_products.py
class ProductService(service.SQLAlchemyAsyncRepositoryService[m.Product]):
    class Repo(repository.SQLAlchemyAsyncRepository[m.Product]):
        model_type = m.Product
    
    repository_type = Repo
```

3. **Create Controller**:
```python
# server/routes/product.py
@Controller(path="/api/products")
class ProductController:
    @post("/", operation_id="CreateProduct")
    async def create_product(
        self,
        data: ProductCreate,
        products_service: ProductService,
    ) -> ProductRead:
        db_obj = await products_service.create(data.model_dump())
        return ProductRead.from_orm(db_obj)
```

4. **Register Route**:
```python
# server/routes/__init__.py
from app.server.routes.product import ProductController
__all__ = (..., "ProductController")

# server/core.py
app_config.route_handlers.extend([
    routes.ProductController,
])
```

5. **Generate Types**:
```bash
make types
```

### Testing API Endpoints

```bash
# Using httpie
http POST localhost:8000/api/products \
  name="Test Product" \
  price=99.99 \
  Authorization:"Bearer $TOKEN"

# Using curl
curl -X POST http://localhost:8000/api/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 99.99}'

# View OpenAPI docs
open http://localhost:8000/schema/swagger
```

## Frontend Development

### Component Development

1. **Create Component**:
```bash
# Create new component file
touch src/js/src/components/products/product-list.tsx
```

2. **Implement Component**:
```typescript
// components/products/product-list.tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function ProductList() {
  const { data, isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products.listProducts(),
  });
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div className="grid gap-4">
      {data?.items.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

3. **Add Route**:
```typescript
// routes/_app/products.tsx
import { createFileRoute } from "@tanstack/react-router";
import { ProductList } from "@/components/products/product-list";

export const Route = createFileRoute("/_app/products")({
  component: ProductList,
});
```

### Frontend Commands

```bash
# Development
cd src/js
npm run dev           # Start dev server
npm run build         # Build for production
npm run preview       # Preview production build

# Code quality
npm run lint          # Run Biome linter
npm run lint:fix      # Fix linting issues
npm run type-check    # Run TypeScript checks

# Type generation
npm run generate-types  # Generate from OpenAPI
```

## Testing Workflows

### Backend Testing

```bash
# Run all tests
make test-all

# Run specific test file
uv run pytest src/py/tests/unit/test_services/test_users.py

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run integration tests only
uv run pytest src/py/tests/integration/

# Run with verbose output
uv run pytest -vv

# Run specific test
uv run pytest -k "test_user_creation"
```

### Frontend Testing

```bash
cd src/js

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- TeamCard.test.tsx
```

### Writing Tests

#### Backend Test Example
```python
# tests/unit/test_services/test_products.py
import pytest
from app.services import ProductService

@pytest.mark.asyncio
async def test_create_product(products_service: ProductService):
    """Test product creation."""
    data = {
        "name": "Test Product",
        "price": 99.99,
        "description": "A test product"
    }
    
    product = await products_service.create(data)
    
    assert product.name == "Test Product"
    assert product.price == 99.99
```

#### Frontend Test Example
```typescript
// __tests__/components/ProductCard.test.tsx
import { render, screen } from "@testing-library/react";
import { ProductCard } from "@/components/products/product-card";

test("renders product information", () => {
  const product = {
    id: "123",
    name: "Test Product",
    price: 99.99,
  };
  
  render(<ProductCard product={product} />);
  
  expect(screen.getByText("Test Product")).toBeInTheDocument();
  expect(screen.getByText("$99.99")).toBeInTheDocument();
});
```

## Code Quality

### Pre-commit Hooks

The project uses pre-commit for code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Linting and Formatting

```bash
# Python
uv run ruff check .          # Check for issues
uv run ruff check . --fix    # Auto-fix issues
uv run ruff format .         # Format code

# TypeScript
cd src/js
npm run lint                 # Check and fix issues

# Type checking
uv run mypy .                # Python type checking
npm run type-check           # TypeScript checking
```

## Debugging

### Backend Debugging

```python
# Add breakpoint in code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
breakpoint()

# Or use VS Code launch.json
{
  "name": "Python: Litestar",
  "type": "python",
  "request": "launch",
  "module": "app",
  "args": ["run", "--debug"],
  "justMyCode": false
}
```

### Frontend Debugging

```typescript
// Use React Developer Tools
// Install browser extension

// Add debugger statement
debugger;

// Or use VS Code debugging
{
  "name": "Chrome",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:5173",
  "webRoot": "${workspaceFolder}/src/js/src"
}
```

### Logging

```python
# Backend logging
import structlog
logger = structlog.get_logger()

logger.info("Processing request", user_id=user.id, action="create")
logger.error("Failed to process", error=str(e), **context)

# Configure log level in .env
APP_LOG_LEVEL=DEBUG
```

## Deployment Preparation

### Building for Production

```bash
# 1. Build frontend
cd src/js
npm run build

# 2. Run production checks
make check-all

# 3. Build Docker image
docker build -f tools/deploy/docker/run/Dockerfile -t myapp:latest .

# 4. Test production build
docker run -p 8000:8000 myapp:latest
```

### Production Configuration

```bash
# Production .env
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# Use strong secret key
APP_SECRET_KEY=$(openssl rand -hex 32)

# Enable security features
AUTH_REQUIRE_EMAIL_VERIFICATION=true
AUTH_ENABLE_2FA=true
AUTH_PASSWORD_MIN_LENGTH=12
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

#### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
uv run app database show

# Reset database
make reset-db
```

#### Type Generation Fails
```bash
# Ensure backend is running
uv run app run-server

# Manually export schema
uv run app export-openapi-schema

# Generate types
cd src/js && npm run generate-types
```

## Best Practices

### Development Tips

1. **Always run `make types`** after API changes
2. **Use meaningful commit messages** following conventional commits
3. **Write tests** for new features
4. **Document complex logic** with comments
5. **Review generated migrations** before applying

### Performance Tips

1. **Use database indexes** for frequently queried fields
2. **Implement pagination** for large datasets
3. **Cache expensive operations** with Redis
4. **Optimize bundle size** with code splitting
5. **Profile queries** in development with `DATABASE_ECHO=true`

## Next Steps

Now that you understand the development workflow:

1. Review [Best Practices](07-best-practices.md) for coding standards
2. Start building features!
3. Contribute to the project

---

*This workflow guide covers the essential commands and practices for productive development. Following these patterns ensures smooth collaboration and high-quality code.*