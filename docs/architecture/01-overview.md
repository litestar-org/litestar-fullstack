# Architecture Overview

## Introduction

The Litestar Fullstack SPA is a production-ready reference application demonstrating modern web development with a Python backend (Litestar) and React frontend. It showcases enterprise-grade patterns for authentication, team management, and comprehensive tooling.

## Tech Stack

### Backend Stack

- **[Litestar](https://litestar.dev/)** - Modern, fast, and production-ready ASGI framework
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** - Industry-standard ORM with async support
- **[Advanced Alchemy](https://github.com/litestar-org/advanced-alchemy)** - Enhanced patterns for SQLAlchemy
- **[PostgreSQL](https://www.postgresql.org/)** - Primary database for persistent storage
- **[Redis](https://redis.io/)** - Caching and session storage
- **[SAQ](https://github.com/tobymao/saq)** - Simple async job queue for background tasks
- **[msgspec](https://github.com/jcrist/msgspec)** - High-performance serialization

### Frontend Stack

- **[React 19](https://react.dev/)** - UI library with latest features
- **[Vite](https://vitejs.dev/)** - Lightning-fast build tool
- **[TanStack Router](https://tanstack.com/router)** - Type-safe routing
- **[TanStack Query](https://tanstack.com/query)** - Powerful data synchronization
- **[shadcn/ui](https://ui.shadcn.com/)** - High-quality UI components
- **[Tailwind CSS v4](https://tailwindcss.com/)** - Utility-first CSS framework
- **[TypeScript](https://www.typescriptlang.org/)** - Type safety throughout

### Infrastructure & Tools

- **[Docker](https://www.docker.com/)** - Containerization for consistent environments
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package management
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations
- **[OpenAPI](https://www.openapis.org/)** - API documentation and client generation
- **[Biome](https://biomejs.dev/)** - Fast linting and formatting

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (SPA)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   React 19  │  │  TanStack    │  │   shadcn/ui     │  │
│  │  Components │  │  Router/Query │  │   Components    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│                           │                                 │
│                    Auto-generated                           │
│                    TypeScript Client                        │
└───────────────────────────┬─────────────────────────────────┘
                           │
                      HTTPS API
                           │
┌───────────────────────────┴─────────────────────────────────┐
│                      Backend (Litestar)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Routes   │  │   Services   │  │   Repositories  │  │
│  │ Controllers │  │Business Logic│  │  Data Access    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                    │            │
│  ┌──────┴─────────────────┴────────────────────┴────────┐  │
│  │              SQLAlchemy + Advanced Alchemy           │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────┴─────┐ ┌─────┴─────┐
              │PostgreSQL │ │   Redis   │
              └───────────┘ └───────────┘
```

## Key Features

### Authentication & Security

- **JWT-based authentication** with secure token handling
- **Email verification** system with token management
- **Password reset** flow with security tracking
- **Two-Factor Authentication (2FA)** with TOTP support
- **Configurable security policies** per environment
- **Role-based access control** with guards

### Team Management

- **Multi-tenant architecture** with team isolation
- **Team invitations** with email notifications
- **Member management** with role assignments
- **File attachments** per team
- **Activity tracking** and audit logs

### Developer Experience

- **Full-stack type safety** from database to UI
- **Auto-generated API client** from OpenAPI schema
- **Hot module replacement** for rapid development
- **Comprehensive testing** setup
- **Pre-configured linting** and formatting
- **Docker-based** development environment

### Production Ready

- **Database migrations** with version control
- **Background job processing** with SAQ
- **Email delivery** with template support
- **Error handling** and logging
- **Performance monitoring** hooks
- **Deployment configurations** for various platforms

## Design Principles

### 1. Type Safety Everywhere

From SQLAlchemy models to React components, every layer enforces type safety:

```python
# Backend - Fully typed models
class User(UUIDAuditBase):
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
```

```typescript
// Frontend - Auto-generated types
import { UserRead } from "@/lib/api/types.gen";
```

### 2. Layered Architecture

Clear separation of concerns across layers:

- **Controllers** - HTTP request/response handling
- **Services** - Business logic and orchestration
- **Repositories** - Data access patterns
- **Models** - Database schema definitions

### 3. Performance First

- **Async throughout** - Non-blocking I/O operations
- **Optimized queries** - Eager loading strategies
- **Efficient serialization** - msgspec for speed
- **Smart caching** - Redis integration
- **Bundle optimization** - Code splitting with Vite

### 4. Security by Design

- **Input validation** at every layer
- **Authentication** with multiple factors
- **Authorization** with granular controls
- **Rate limiting** for sensitive operations
- **Audit logging** for compliance

## System Requirements

### Development Environment

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Production Environment

- Same as development plus:
- HTTPS termination (nginx/caddy)
- Process manager (systemd/supervisor)
- Monitoring (Prometheus/Grafana)
- Log aggregation (ELK/Loki)

## Next Steps

Now that you understand the high-level architecture:

1. Explore the [Project Structure](02-project-structure.md) to understand code organization
2. Dive into [Backend Architecture](03-backend-architecture.md) for service patterns
3. Learn about [Authentication & Security](04-authentication-security.md) implementation
4. Review [Frontend Architecture](05-frontend-architecture.md) for React patterns

---

*This overview provides the foundation for understanding the Litestar Fullstack SPA architecture. Each subsequent section will dive deeper into specific aspects of the system.*