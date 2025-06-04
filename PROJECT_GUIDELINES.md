# Project Guidelines

This document consolidates all project guidelines for easy reference. Internal links navigate to relevant sections within this document.

## Table of Contents

- **Backend**
  - [Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)](#advanced-alchemy-and-litestar-servicerepositorymodel-patterns-with-msgspec)
  - [Alembic Migration Conventions](#alembic-migration-conventions)
  - [Asynchronous Programming Conventions](#asynchronous-programming-conventions)
  - [Litestar Framework Conventions (with msgspec)](#litestar-framework-conventions-with-msgspec)
  - [Service Layer Conventions (Project Specific)](#service-layer-conventions-project-specific)
  - [SQLAlchemy Model Conventions](#sqlalchemy-model-conventions)
- **Core**
  - [Comments and Documentation](#comments-and-documentation)
  - [Naming Conventions](#naming-conventions)
  - [Project Structure and Organization](#project-structure-and-organization)
  - [Python Style and Formatting](#python-style-and-formatting)
- **Deployment**
  - [CI/CD Pipeline Conventions (GitHub Actions)](#cicd-pipeline-conventions-github-actions)
  - [Dockerfile and Docker Compose Conventions](#dockerfile-and-docker-compose-conventions)
- **Domain**
  - [Authentication, Authorization, and User Management (with msgspec)](#authentication-authorization-and-user-management-with-msgspec)
  - [Data Validation with msgspec.Struct](#data-validation-with-msgspecstruct)
- **Frontend**
  - [ShadCN/UI Component Conventions](#shadcnui-component-conventions)
  - [Tailwind CSS v4 Conventions](#tailwind-css-v4-conventions)
  - [TypeScript Style and Conventions](#typescript-style-and-conventions)
  - [Vite Configuration Conventions](#vite-configuration-conventions)
- **Quality**
  - [Performance Guidelines](#performance-guidelines)
  - [Security Best Practices](#security-best-practices)
  - [Static Analysis Tooling](#static-analysis-tooling)
  - [Testing with Pytest](#testing-with-pytest)
- **Makefile Style and Always-On Rules**
  - [General Setup](#general-setup)
  - [Variable Definitions](#variable-definitions)
  - [Targets](#targets)
  - [Makefile Organization](#makefile-organization)
  - [Comments](#comments)
  - [Readability](#readability)
  - [Exceptions](#exceptions)
  - [Always-On Rules](#always-on-rules)
- **Authentication and Authorization Flow**
  - [Objective](#objective)
  - [Context](#context)
  - [Key Files & Components](#key-files-components)
  - [Rules and Detailed Flow](#rules-and-detailed-flow)
  - [Conceptual Flow Summary](#conceptual-flow-summary)

## Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)

## Objective

To ensure robust, maintainable, and efficient database interactions by consistently applying the project's established Advanced Alchemy patterns for SQLAlchemy models, Litestar services (with inner repositories), and mandatory `msgspec.Struct` DTOs. **The patterns found in `UserService`, `TeamService`, and the `User`, `Team`, `Tag` models are the de-facto standard.**

## Context

- **Technologies**: Advanced Alchemy, SQLAlchemy 2.0, Litestar, `msgspec`.
- **Advanced Alchemy Docs**: [https://docs.advanced-alchemy.litestar.dev/latest/](mdc:https:/docs.advanced-alchemy.litestar.dev/latest)
- **Key Project Patterns**:
  - Services inherit `litestar.plugins.sqlalchemy.service.SQLAlchemyAsyncRepositoryService`.
  - Services define an inner `Repo` class inheriting `litestar.plugins.sqlalchemy.repository.SQLAlchemyAsyncRepository` (or `...SlugRepository`).
  - Models use Advanced Alchemy base classes (e.g., `UUIDAuditBase`) and mixins (e.g., `SlugKey`, `UniqueMixin`).
  - `msgspec.Struct` is **mandatory** for API DTOs.
- **Project Files**: Model definitions (`src/py/app/db/models/`), service implementations (`src/py/app/services/`), `msgspec.Struct` definitions (`src/py/app/schemas/`).

## Rules

### SQLAlchemy Models (`src/py/app/db/models/`)

- **Base Models**: All SQLAlchemy declarative models MUST inherit from an appropriate Advanced Alchemy base model (e.g., `UUIDAuditBase` as seen in `User` and `Team`).
  - ✅ `class User(UUIDAuditBase): ...`
  - ✅ `class Team(UUIDAuditBase, SlugKey): ...`
- **Mixins**: Utilize Advanced Alchemy mixins like `SlugKey` (as in `Team`, `Tag`) and `UniqueMixin` (as in `Tag`) when their functionality is required.
  - `UniqueMixin` is crucial for "get-or-create" M2M scenarios (e.g., tags). It requires implementing `unique_hash` and `unique_filter` methods on the model.
  - ✅

      ```python
      # In models/tag.py
      from advanced_alchemy.mixins import UniqueMixin, SlugKey
      from advanced_alchemy.base import UUIDAuditBase
      from advanced_alchemy.utils.text import slugify
      from sqlalchemy import ColumnElement # type: ignore[attr-defined]
      from collections.abc import Hashable

      class Tag(UUIDAuditBase, SlugKey, UniqueMixin):
          # ... other attributes ...
          @classmethod
          def unique_hash(cls, name: str, slug: str | None = None, **kwargs: object) -> Hashable: # Added **kwargs
              return slugify(name) # Example hash based on slugified name

          @classmethod
          def unique_filter(cls, name: str | None = None, slug: str | None = None, **kwargs: object) -> ColumnElement[bool]: # Added **kwargs and made params optional
              if name is not None: # Ensure at least one is provided for filter
                return cls.slug == slugify(name) # Filter by slug
              if slug is not None:
                return cls.slug == slug
              raise ValueError("Either name or slug must be provided for unique_filter")

      ```

- **Typing**: Use `sqlalchemy.orm.Mapped` and `mapped_column` for all model attributes.
- **Relationships**: Define relationships using `sqlalchemy.orm.relationship`. Prefer `lazy="selectin"` for frequently accessed relationships to avoid N+1 queries, as seen in `User.roles` and `User.teams`.

### Service Layer (`src/py/app/services/`)

- **Base Service Class**: All services MUST inherit from `litestar.plugins.sqlalchemy.service.SQLAlchemyAsyncRepositoryService[ModelType]` (e.g., `UserService(service.SQLAlchemyAsyncRepositoryService[m.User])`).
- **Inner Repository Class**: Each service MUST define an inner class named `Repo` that inherits from `litestar.plugins.sqlalchemy.repository.SQLAlchemyAsyncRepository[ModelType]` (e.g., `UserService.Repo`) or `SQLAlchemyAsyncSlugRepository[ModelType]` if slug functionality is needed (e.g., `TeamService.Repo`).
  - The service's `repository_type` attribute MUST be set to this inner `Repo` class.
  - ✅

      ```python
      # In services/_users.py
      from litestar.plugins.sqlalchemy import repository, service
      from app.db import models as m

      class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
          class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
              model_type = m.User
          repository_type = Repo
          # ... rest of the service ...
      ```

  - ✅

      ```python
      # In services/_teams.py
      from litestar.plugins.sqlalchemy import repository, service
      from app.db import models as m

      class TeamService(service.SQLAlchemyAsyncRepositoryService[m.Team]):
          class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Team]): # Note SlugRepository
              model_type = m.Team
          repository_type = Repo
          # ... rest of the service ...
      ```

- **Data Transformation Hooks**: Utilize `to_model_on_create`, `to_model_on_update`, and `to_model_on_upsert` service hooks for data manipulation and preparation *before* data is passed to the repository. This is where `msgspec.Struct` data from controllers is processed or mapped to model-compatible dictionaries if needed.
  - These hooks often call internal `_populate_*` helper methods within the service (e.g., `_populate_slug`, `_populate_with_hashed_password`).
  - **Mapping `msgspec.Struct` to Model**: Within these hooks, or before calling repository methods, convert incoming `msgspec.Struct` data to a dictionary suitable for model instantiation or repository operations if the service base class doesn't handle `msgspec.Struct` directly. `msgspec.to_builtins(struct_instance)` can be used, or direct field access.

      ```python
      # Example within a to_model_on_create hook or service method
      # data: UserCreateStruct (msgspec.Struct)
      # model_data_dict = msgspec.to_builtins(data) # Converts to dict
      # # Now model_data_dict can be used to create a SQLAlchemy model instance
      # # or passed to repository methods that expect dicts.
      # # The SQLAlchemyAsyncRepositoryService might also directly handle attribute access
      # # from msgspec.Struct if field names align.
      ```

- **Business Logic**: Implement specific business logic methods within the service (e.g., `authenticate`, `update_password` in `UserService`; handling M2M tag logic using `Tag.as_unique_async` in `TeamService`).
- **`msgspec.Struct` for I/O**: Services should expect `msgspec.Struct` instances as input for create/update operations (coming from Litestar controllers) and are responsible for mapping SQLAlchemy model instances to `msgspec.Struct` instances for output if the controller doesn't handle this explicitly.

### Litestar Integration (SQLAlchemyPlugin)

- The `SQLAlchemyPlugin` from `advanced_alchemy.extensions.litestar` MUST be correctly configured in the Litestar application setup (e.g., in `src/py/app/plugins/db.py` or `asgi.py`).
  - This plugin provides the `AsyncSession` for dependency injection into services, which then pass it to their repositories (typically via `self.repository.session`).

## Mandatory `msgspec` Usage

- All Data Transfer Objects (DTOs) used at the API boundary (controller request/response types) MUST be `msgspec.Struct` instances. See the section "[Data Validation with msgspec.Struct](#data-validation-with-msgspecstruct)" for `msgspec.Struct` definition guidelines.

## Exceptions

- Alembic migration scripts operate directly with SQLAlchemy Core/ORM and do not involve services or `msgspec` DTOs.
- CLI commands might interact directly with services, but their input parsing is distinct from API DTO validation.

-----

## Alembic Migration Conventions

## Objective

To ensure database migrations are safe, reversible, and maintainable.

## Context

- Alembic, SQLAlchemy, Advanced Alchemy.
- Migrations managed via `app database` CLI commands.

## Rules

### Migration Generation

- Generate migrations using `app database make-migrations -m "Descriptive message"`.
- Always review auto-generated migrations carefully.

### Migration Content

- Ensure `upgrade()` and `downgrade()` functions are symmetrical.
- For data migrations, provide clear downgrade paths or state they are irreversible if necessary.
- Use `op.bulk_insert()` for large data additions.

### Best Practices

- Keep migrations small and focused on a single schema change or data transformation.
- Test migrations in a development/staging environment before applying to production.

## Exceptions

- Initial database schema setup might be a larger migration.

-----

## Asynchronous Programming Conventions

## Objective

To ensure correct and efficient use of `async` and `await` for I/O-bound operations.

## Context

- Litestar is an ASGI framework, inherently asynchronous.
- SQLAlchemy configured for async operations with Advanced Alchemy.

## Rules

### `async`/`await` Usage

- Use `async def` for all Litestar route handlers, service methods, and repository methods that perform I/O (database calls, external API requests).
- `await` all calls to `async` functions.

### Blocking Calls

- Avoid blocking I/O operations in async code. If unavoidable, run them in a separate thread pool (e.g., using `anyio.to_thread.run_sync`).

### Concurrency

- Use `asyncio.gather()` for concurrent execution of multiple awaitables when appropriate.

## Exceptions

- Synchronous utility functions that are purely CPU-bound.
- CLI commands might have synchronous parts.

-----

## Litestar Framework Conventions (with msgspec)

## Objective

To ensure consistent and effective use of Litestar features, promoting maintainability, performance, and adherence to Litestar best practices, with **`msgspec.Struct` as the mandatory data structure for API DTOs**.

## Context

- **Technologies**: Litestar, Python 3.13+, `msgspec`.
- **Key Concepts**: Controllers, Routers, `msgspec.Struct` for DTOs, Dependency Injection, Guards, Middleware, Event Handlers, Lifespan Hooks, Plugins (especially for Advanced Alchemy).
- **Project Files**: `src/py/app/server/`, `src/py/app/lib/` (for dependencies, exceptions, plugins), `src/py/app/schemas/` (for `msgspec.Struct` definitions), `src/py/app/asgi.py` (app factory).

## Rules

### Application Structure

- **App Factory Pattern**: Utilize the app factory pattern (e.g., `create_app()` in `src/py/app/asgi.py`) for application instantiation.
- **Plugin Usage**: Leverage Litestar plugins for integrating extensions like SQLAlchemy (via Advanced Alchemy `SQLAlchemyPlugin`), SAQ, Vite, etc. Configure plugins centrally.

### Controllers and Routes

- **Organization**: Group related endpoints into `Controller` classes within `src/py/app/server/api/`.
- **Path Naming**: Use `kebab-case` for URL paths.
- **DTOs with `msgspec.Struct`**: **Mandatory**: Use `msgspec.Struct` for all request bodies and response data DTOs. Define these in `src/py/app/schemas/`.
  - Litestar provides automatic validation of incoming `msgspec.Struct` data and serialization of outgoing `msgspec.Struct` data.
  - ✅

      ```python
      from litestar import post, get
      from litestar.controller import Controller
      from app.schemas import UserCreate, UserRead # msgspec.Struct definitions
      from app.services import UserService
      from uuid import UUID

      class UserController(Controller):
          path = "/users"
          tags = ["Users"]
          # Ensure UserService is injected, e.g. via __init__ or Provide in dependencies
          # def __init__(self, user_service: UserService) -> None:
          #     self.user_service = user_service

          @post()
          async def create_user(self, data: UserCreate, user_service: UserService) -> UserRead:
              # 'data' is an auto-validated instance of UserCreate (msgspec.Struct)
              created_db_user = await user_service.create(data) # Service handles mapping to DB model
              # Map DB model back to UserRead msgspec.Struct for response
              return UserRead(
                  id=created_db_user.id,
                  email=created_db_user.email,
                  name=created_db_user.name,
                  is_active=created_db_user.is_active,
                  created_at=created_db_user.created_at,
                  updated_at=created_db_user.updated_at,
              )

          @get("/{user_id:uuid}")
          async def get_user_by_id(self, user_id: UUID, user_service: UserService) -> UserRead:
              db_user = await user_service.get(user_id)
              return UserRead(
                  id=db_user.id,
                  email=db_user.email,
                  # ... other fields
              )
      ```

- **Async Endpoints**: Prefer `async def` for route handlers.

### Dependency Injection (`Dependency`)

- **Explicit Dependencies**: Use Litestar's DI for resources like DB sessions, services, configs.
- **Service Layer Injection**: Inject service classes (e.g., `UserService`) into controllers.
  - Services themselves will obtain the `AsyncSession` via DI to initialize repositories (see the section "[Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)](#advanced-alchemy-and-litestar-servicerepositorymodel-patterns-with-msgspec)").

### Error Handling

- **Litestar Exceptions**: Utilize Litestar's built-in exceptions (`HTTPException`, `NotFoundException`, `ValidationException`).
- **Custom Exception Handlers**: Implement for application-specific errors.

### Guards and Middleware

- **Guards**: For route/controller authorization.
- **Middleware**: For cross-cutting concerns (logging, CORS).

### OpenAPI Schema

- **Docstrings**: Provide clear docstrings for controllers/handlers for OpenAPI generation.
- **Tags**: Use `tags` for grouping.
- `msgspec.Struct` definitions will be automatically used by Litestar to generate the OpenAPI schema components.

## Exceptions

- Websocket handlers have different data handling patterns.
- CLI commands are outside the Litestar request-response cycle.

-----

## Service Layer Conventions (Project Specific)

## Objective

To enforce the project's established conventions for the service layer, ensuring clear separation of business logic, use of the specified base service and inner repository pattern, and interaction with `msgspec.Struct` DTOs.

## Context

- **Project Standard**: Services MUST follow the pattern exemplified by `UserService` and `TeamService`.
- **Base Service**: `litestar.plugins.sqlalchemy.service.SQLAlchemyAsyncRepositoryService[ModelType]`.
- **Inner Repository**: Services define an inner `Repo` class (subclass of `litestar.plugins.sqlalchemy.repository.SQLAlchemyAsyncRepository` or `...SlugRepository`).
- **Data I/O**: `msgspec.Struct` instances are used for data input from controllers and for output from services (or models that controllers then map to `msgspec.Structs`).
- Interacts with Advanced Alchemy models and repositories (via its inner `Repo`).

## Rules

### Core Service Structure (Mandatory Pattern)

- **Inheritance**: Services MUST inherit from `litestar.plugins.sqlalchemy.service.SQLAlchemyAsyncRepositoryService[ModelType]`.
- **Inner `Repo` Class**: Each service MUST define an inner class `Repo` that inherits from `litestar.plugins.sqlalchemy.repository.SQLAlchemyAsyncRepository[ModelType]` (or `...SQLAlchemyAsyncSlugRepository` for slug-based models).
  - The `Repo.model_type` attribute MUST be set to the SQLAlchemy model.
  - The service's `repository_type` attribute MUST be set to this inner `Repo`.
  - ✅ See `UserService` or `TeamService` for exact implementation examples.

### Responsibilities

- **Business Logic**: Encapsulate all business logic related to a domain entity or use case.
- **Orchestration**: Coordinate calls to its inner repository and potentially other services.
- **Data Transformation/Preparation**: Utilize service hooks (`to_model_on_create`, `to_model_on_update`, `to_model_on_upsert`) for preparing data before repository actions. This includes:
  - Processing input `msgspec.Struct` data.
  - Populating fields (e.g., hashing passwords, generating slugs via `self.repository.get_available_slug()`).
  - Handling complex relationships or M2M data (e.g., using `Model.as_unique_async()` for tags, as seen in `TeamService`).
- **DTO Handling**: Expect `msgspec.Struct` instances from controllers for CUD operations. Return SQLAlchemy model instances or `msgspec.Struct` instances as appropriate for the operation. Controllers are typically responsible for the final mapping to response `msgspec.Structs` if the service returns a model.

### Interaction with Repository

- All database operations MUST go through the `self.repository` instance (the inner `Repo`).
- Services should not bypass the repository to interact directly with an `AsyncSession` for standard CRUD or even most custom queries.

### Error Handling

- Raise appropriate Litestar HTTP exceptions (e.g., `NotFoundException`, `PermissionDeniedException`) or custom domain-specific exceptions when business rules are violated or data is not found.

### Example Snippet (Conceptual based on `UserService`)

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m
from app.schemas import UserCreate # msgspec.Struct

class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    class Repo(repository.SQLAlchemyAsyncRepository[m.User]):
        model_type = m.User
    repository_type = Repo

    async def to_model_on_create(self, data: UserCreate) -> m.User: # data is msgspec.Struct
        # Example: Convert msgspec.Struct to dict for model creation if needed by base service/repo
        # or handle field by field. The base service might handle Structs directly.
        data_dict = msgspec.to_builtins(data) # if a dict is strictly needed by underlying layers
        if "password" in data_dict:
             data_dict["hashed_password"] = await self._hash_password(data_dict.pop("password"))
        # ... other population logic ...
        return await super().to_model_on_create(data_dict) # or data directly if supported

    async def _hash_password(self, password: str) -> str: ...
    # ... other business logic methods ...
```

## Further Details

- Refer to the section "[Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)](#advanced-alchemy-and-litestar-servicerepositorymodel-patterns-with-msgspec)" for comprehensive rules on how services, repositories, and models integrate with Advanced Alchemy and `msgspec`.

## Exceptions

- Purely utility services not tied to a SQLAlchemy model might follow a different base class or structure, but this is not the primary pattern for data-centric services.

-----

## SQLAlchemy Model Conventions

## Objective

To ensure SQLAlchemy models are defined consistently, integrating with Advanced Alchemy and following best practices.

## Context

- SQLAlchemy 2.0, Advanced Alchemy, Alembic.
- Focus on model structure, relationships, and typing.

## Rules

### Model Definition

- Inherit from project's Advanced Alchemy base model (e.g., `app.lib.db.base.Base`).
- Use `Mapped` and `mapped_column` for all attributes.
- Define `__tablename__` explicitly.

### Relationships

- Clearly define relationships (`relationship()`) with appropriate `back_populates`, `lazy` loading strategies.

### Typing

- Ensure all model attributes and relationships are fully type-hinted.

## Exceptions

- Potentially views or SQL constructs mapped via `SQLQuery` from Advanced Alchemy.

-----

## Comments and Documentation

## Objective

To ensure the codebase and project are well-documented.

## Context

- Python Docstrings (Google Style)
- TypeScript/JavaScript (TSDoc/JSDoc)
- Sphinx for project documentation.

## Rules

### General Principles

- Comment "why", not "what".
- Keep comments updated.

### Python Docstrings

- Document all public APIs adhering to Google Style.

### TypeScript/JavaScript Comments

- Document all exported members using TSDoc/JSDoc.

### Project Documentation (README, CONTRIBUTING, Sphinx)

- Keep these documents comprehensive and up-to-date.

### Commit Messages

- Follow Conventional Commits.

## Exceptions

- Trivial code may not need extensive comments.

-----

## Naming Conventions

## Objective

To establish clear, consistent, and descriptive naming conventions across the codebase for improved readability and maintainability.

## Context

- **Primary Languages**: Python (backend), TypeScript/JavaScript (frontend).
- **Key Frameworks/Libraries**: Litestar, SQLAlchemy, Pydantic, Pytest, React (assumed for ShadCN), Tailwind CSS, Vite.
- **Existing Conventions**: PEP 8 for Python, standard TypeScript/JavaScript community practices.

## Rules

### General Principles

- **Descriptive Names**: Names should clearly indicate the purpose or content of the entity.
  - ✅ `user_profile_service`, `fetch_pending_orders()`
  - ❌ `ups`, `get_data()`
- **Avoid Abbreviations (Mostly)**: Use full words unless the abbreviation is universally understood and significantly shorter (e.g., `id`, `db`, `url`, `http`).
- **Consistency**: Apply the chosen convention consistently within its scope (e.g., all Python files, all TypeScript files).

### Python (Backend - `src/py`)

- **Packages & Modules (Files)**: `lower_case_with_underscores.py` (e.g., `user_service.py`, `database_utils.py`).
- **Classes**: `CapWords` (PascalCase) (e.g., `UserService`, `UserProfile`, `DatabaseSettings`).
  - SQLAlchemy Models: `CapWords` (e.g., `UserAccount`, `TeamMembership`).
  - Pydantic Schemas (DTOs): `CapWords` often suffixed with `DTO`, `Schema`, `Create`, `Update`, `Read` (e.g., `UserCreateDTO`, `UserReadSchema`).
  - Litestar Controllers: `CapWords` suffixed with `Controller` (e.g., `UserController`).
  - Pytest Test Classes: `TestCapWords` (e.g., `TestUserService`).
- **Functions & Methods**: `lower_case_with_underscores` (e.g., `get_user_by_id`, `calculate_total_price`).
  - Pytest Test Functions: `test_lower_case_with_underscores_describing_behavior` (e.g., `test_create_user_with_valid_data_returns_201`).
- **Variables**: `lower_case_with_underscores` (e.g., `user_list`, `db_session`, `total_amount`).
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`).
- **Private Members**: Single leading underscore for internal use (`_internal_method`, `_temp_variable`). Double leading underscore for name mangling (`__private_attribute`) if strictly necessary (rare).
- **Boolean Variables/Functions**: Often prefixed with `is_`, `has_`, `should_` (e.g., `is_active`, `has_permissions`).

### TypeScript/JavaScript (Frontend - `src/js`)

- **Files & Folders**: `kebab-case` (e.g., `user-profile.tsx`, `api-client.ts`, `auth-hooks/`) or `PascalCase.tsx` for components is also common (e.g., `UserProfile.tsx`). Choose one and be consistent, `kebab-case` for non-component files and `PascalCase.tsx` for components is a good pattern.
  - Project seems to use `kebab-case` for configs (`vite.config.ts`, `tailwind.config.js`).
- **Classes**: `PascalCase` (e.g., `ApiClient`, `AuthService`).
- **Interfaces & Types**: `PascalCase` (e.g., `UserProfile`, `ApiOptions`, `FormField`).
  - Can be prefixed with `I` for interfaces (`IUserProfile`) or `T` for types (`TUserRole`) if preferred by the team, but often not necessary if usage is clear.
- **Functions & Methods**: `camelCase` (e.g., `getUserProfile`, `calculateTotalPrice`).
- **Variables & Properties**: `camelCase` (e.g., `userList`, `apiClient`, `totalAmount`).
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`) or `PascalCase` for exported constant objects (e.g., `ApiEndpoints`).
- **React Components (TSX/JSX)**: `PascalCase` (e.g., `<UserProfile />`, `<Button />`). File names often match: `UserProfile.tsx`.
- **React Hooks**: `useCamelCase` (e.g., `useAuth`, `useUserProfileForm`).
- **Boolean Variables/Functions**: Often prefixed with `is`, `has`, `should` (e.g., `isActive`, `hasPermission`).

### CSS (Tailwind utility classes are primary)

- **Custom CSS Classes (if any)**: `kebab-case` (e.g., `custom-card-style`).
- **CSS Variables (in `globals.css`)**: `kebab-case` with `--` prefix (e.g., `--primary-color`, `--background-default`). ShadCN often uses simple names like `--background`, `--primary`.

### Database (SQLAlchemy models define table/column names indirectly)

- **Table Names**: Generally `lower_case_with_underscores` (e.g., `user_account`, `team_memberships`). SQLAlchemy default for `CamelCase` model is `camel_case` table name, but can be overridden with `__tablename__`.
- **Column Names**: Generally `lower_case_with_underscores` (e.g., `user_id`, `first_name`, `created_at`). SQLAlchemy maps model attributes to these.
- **Index & Constraint Names**: Follow SQLAlchemy/Alembic defaults or define a clear, consistent pattern if customizing (e.g., `ix_table_column`, `uq_table_column`, `fk_table_sourcetable_targettable_column`).

## Exceptions

- Third-party library code may follow different conventions.
- Generated code (e.g., by OpenAPI generators if used for client) might have its own naming style; conform where feasible.
- Acronyms: If an acronym is used, its casing depends on the convention (e.g., `userId` in camelCase, `user_id` in snake_case, `UserID` or `UserId` in PascalCase – prefer `UserId` for readability over `UserID` if it starts a name).

-----

## Project Structure and Organization

## Objective

Define and maintain a consistent and logical project structure to improve navigability, scalability, and ease of understanding for all contributors.

## Context

- Current project layout: Python backend (`src/py/app`), JavaScript frontend (`src/js`), tests (`src/py/tests`, `tests`), docs (`docs`), tools (`tools`).
- Key configuration files: `pyproject.toml`, `Makefile`, `vite.config.ts`, `tailwind.config.js`.

## Rules

### General Principles

- **Separation of Concerns**: Keep backend, frontend, tests, scripts, and documentation in distinct top-level or `src`-level directories.
- **Modularity**: Group related files by feature or domain within their respective application layers (e.g., `src/py/app/services/users/`, `src/js/src/features/authentication/`).

### Python Backend (`src/py/app`)

- **`cli/`**: Click CLI command definitions.
- **`config.py`**: Application configuration settings (potentially loading from environment variables, .env files).
- **`db/`**: SQLAlchemy related files.
  - `models/`: SQLAlchemy model definitions.
  - `migrations/`: Alembic migration scripts.
  - `base.py` or `__init__.py`: Base model definition using Advanced Alchemy.
- **`lib/`**: Core library code, shared utilities, constants, base classes, Advanced Alchemy setup.
  - `constants.py`
  - `dependencies.py` (Litestar dependency providers)
  - `exceptions.py` (Custom application exceptions)
  - `db/plugin.py` / `db/config.py` (SQLAlchemy plugin config for Litestar)
  - `repositories/` (Advanced Alchemy repositories)
- **`schemas/`**: Pydantic schemas for data validation, serialization (DTOs).
- **`server/`**: Litestar server components.
  - `api/`: API controllers/routers, versioned (e.g., `v1/`).
  - `web/`: Routes for serving HTML pages (if any beyond SPA).
  - `guards.py`
  - `middleware.py`
- **`services/`**: Business logic layer, interacting with repositories.
- **`utils/`**: General utility functions not fitting elsewhere.
- **`asgi.py`**: ASGI application entry point, Litestar app factory (`create_app`).
- **`__init__.py`**: Package initializers.
- **`__main__.py`**: Entry point for `python -m app` (CLI runner).

### JavaScript Frontend (`src/js`)

- **`public/`**: Static assets directly served.
- **`src/`**: Main frontend source code.
  - `app.tsx` / `main.tsx`: Main application entry point.
  - `components/`: Reusable UI components.
    - `ui/`: ShadCN/UI components.
    - `custom/` or feature-specific: Project-specific components.
  - `config/` or `constants/`: Frontend configuration.
  - `hooks/`: Custom React hooks.
  - `layouts/`: Page layout components.
  - `lib/`: Utility functions, API client instances (e.g., `utils.ts` for ShadCN `cn`).
  - `pages/` or `routes/`: Page components mapped to URL routes.
  - `services/` or `api/`: API interaction layer (e.g., functions calling backend).
  - `store/` or `state/`: Global state management (if used, e.g., Zustand, Redux).
  - `styles/` or `assets/css/`: Global stylesheets (e.g., `globals.css` for Tailwind base).
- **`vite.config.ts`**: Vite build configuration.
- **`tailwind.config.js` / `.ts`**: Tailwind CSS configuration.
- **`postcss.config.js`**: PostCSS configuration.
- **`tsconfig.json`**: TypeScript configuration.
- **`package.json`**: NPM dependencies and scripts.

### Testing (`src/py/tests` and `tests`)

- **`src/py/tests/unit/`**: Unit tests for Python backend.
- **`src/py/tests/integration/`**: Integration tests for Python backend.
- **`src/py/tests/conftest.py`**: Root conftest for Pytest fixtures.
- `tests/` directory: If used, clarify its purpose (e.g., E2E tests, frontend tests if not co-located).

### Other Key Files/Folders

- **`.github/workflows/`**: GitHub Actions CI/CD workflows.
- **`docs/`**: Sphinx documentation source.
- **`tools/`**: Utility scripts, deployment tools (Docker, K8s).
- **`.env`, `.env.local.example`**: Environment variable files.
- **`pyproject.toml`**: Python project metadata, dependencies, tool configurations.
- **`Makefile`**: Common development and operational commands.

## Rules to Enforce

- New modules/features should follow the established structure.
- Avoid placing application logic in top-level directories outside `src/` unless it's a tool or script.
- Configuration files should reside in standard locations (root for project-wide, specific dirs for tool-specific like Vite/Tailwind in `src/js`).

## Exceptions

- Temporary files or experimental code should be clearly marked or placed in a `.tmp/` directory (and gitignored).

-----

## Python Style and Formatting

## Objective

Ensure consistent, readable, and maintainable Python code across the project, adhering to PEP 8 and project-specific conventions enforced by Ruff and Black.

## Context

- **Technologies**: Python 3.13 (as per .python-version, though pyproject.toml mentions 3.11 target for ruff)
- **Tools**: Ruff (for linting and formatting, configured in `pyproject.toml`), Pre-commit (for enforcement).
- **Conventions**: PEP 8, Google Style Python Docstrings (as per `tool.ruff.lint.pydocstyle` in `pyproject.toml`).

## Rules

### Formatting

- **Adhere to Ruff/Black**: All Python code MUST be formatted using Ruff's formatter (which is Black-compatible), enforced via pre-commit.
  - ✅ `uv run ruff format .` or rely on pre-commit.
  - ❌ Manually formatting code that deviates significantly from Black's output.
- **Line Length**: Maximum line length is 120 characters, as configured in `tool.ruff.line-length`.

### Imports

- **Organization**: Imports should be grouped in the following order: standard library, third-party, first-party (application-specific: `app`, `tests`). This is managed by `ruff.lint.isort`.
  - ✅

      ```python
      import asyncio
      from pathlib import Path

      import litestar
      from sqlalchemy.ext.asyncio import AsyncSession

      from app.lib import constants
      from app.services import UserService
      ```

  - ❌

      ```python
      from app.lib import constants
      import litestar
      import asyncio
      from sqlalchemy.ext.asyncio import AsyncSession
      from app.services import UserService
      from pathlib import Path
      ```

- **Relative Imports**: Disallow all relative imports. Use absolute imports from the `src/py` root. (`tool.ruff.lint.flake8-tidy-imports.ban-relative-imports = "all"`)
  - ✅ `from app.services.my_service import MyService`
  - ❌ `from ..services.my_service import MyService` (within the app)
- **Wildcard Imports**: Avoid wildcard imports (`from module import *`).
  - ✅ `from os import path`
  - ❌ `from os import *`

### Typing

- **Type Hinting**: All function signatures (arguments and return types) and variable declarations SHOULD be type-hinted. This is checked by MyPy and Pyright.
  - ✅ `def get_user(user_id: UUID) -> User | None:`
  - ❌ `def get_user(user_id):`
- **`TYPE_CHECKING`**: Use `if TYPE_CHECKING:` for imports needed only for type hinting to avoid circular dependencies at runtime.
  - ✅

      ```python
      from typing import TYPE_CHECKING

      if TYPE_CHECKING:
          from app.models import User # Expensive import or potential circular import
      
      def get_users() -> "list[User]": ...
      ```

### Naming Conventions

- **General**: Follow PEP 8 naming conventions.
  - Modules: `lower_case_with_underscores`
  - Packages: `lower_case_with_underscores`
  - Classes: `CapWords`
  - Functions: `lower_case_with_underscores`
  - Methods: `lower_case_with_underscores`
  - Constants: `UPPER_CASE_WITH_UNDERSCORES`
  - Variables: `lower_case_with_underscores`
- **Private Members**: Use a single leading underscore for internal/protected members (e.g., `_internal_method`). Use double leading underscores (`__`) for name mangling if strictly necessary (rarely needed).

### Error Handling

- **Specific Exceptions**: Catch specific exceptions rather than generic `Exception` or `BaseException`.
  - ✅ `try: ... except ValueError: ...`
  - ❌ `try: ... except Exception: ...`
- **Custom Exceptions**: Define custom exceptions in `app.lib.exceptions` (or similar, e.g. `app.shared.exceptions`) for application-specific error conditions.

## Exceptions

- Generated code (e.g., in `migrations/versions/`) might not fully adhere to all style guides, but should be kept as clean as possible. Ruff ignores are configured for these.
- Test files might have slightly different naming conventions for test functions (e.g., `test_something_happens`).
- `manage.py` and top-level scripts might have slight deviations if necessary for their specific function.

-----

## CI/CD Pipeline Conventions (GitHub Actions)

## Objective

To maintain robust, efficient, and understandable CI/CD pipelines for automated testing, building, and deployment.

## Context

- GitHub Actions used for CI/CD (workflows in `.github/workflows/`).

## Rules

### Workflow Structure

- **Clarity**: Define clear job and step names.
- **Triggers**: Configure appropriate triggers (push, pull_request, schedule, manual).
- **Caching**: Utilize caching for dependencies (pip, npm) to speed up builds.

### Testing & Linting

- Run linters, type checkers, and tests (unit, integration) on every relevant trigger (e.g., PRs to main).
- Ensure test reports and coverage are generated and accessible.

### Building & Deployment

- Build Docker images in CI.
- Implement secure deployment strategies (e.g., to staging/production environments).
- Use GitHub Actions secrets for sensitive data (API keys, tokens).

### Reusability

- Use reusable workflows or composite actions for common tasks if pipelines become complex.

## Exceptions

- Simple, non-critical workflows might have a more basic structure.

-----

## Dockerfile and Docker Compose Conventions

## Objective

To ensure Docker images are built efficiently, securely, and are maintainable.

## Context

- Docker used for containerization (development and production).
- Multi-stage Docker builds are preferred (as hinted in README).

## Rules

### Dockerfile Best Practices

- **Minimal Base Images**: Use official, minimal base images (e.g., `python:3.13-slim`).
- **Multi-stage Builds**: Utilize multi-stage builds to reduce final image size (e.g., separate build stage for compiling assets or Python dependencies).
- **Layer Ordering**: Order Dockerfile instructions to leverage caching effectively (less frequently changing layers first).
- **Non-root User**: Run applications as a non-root user inside the container.
- **Least Privilege**: Only include necessary files and dependencies in the final image.
- **`.dockerignore`**: Use a comprehensive `.dockerignore` file.

### Docker Compose (`docker-compose.yml`)

- **Development Environment**: Define services for easy local development setup (app, database, redis, etc.).
- **Environment Variables**: Manage configuration through environment variables, not hardcoded in compose files.
- **Volumes**: Use volumes for persistent data and code mounting in development.

## Exceptions

- Specific build tools might require different Dockerfile structures.

-----

## Authentication, Authorization, and User Management (with msgspec)

## Objective

To define consistent and secure practices for handling users, authentication (AuthN), and authorization (AuthZ), using `msgspec.Struct` for all related DTOs.

## Context

- Litestar JWT for session/token management, `httpx-oauth` for OAuth providers.
- Advanced Alchemy models for User, Team, Role (as per the section "[Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)](#advanced-alchemy-and-litestar-servicerepositorymodel-patterns-with-msgspec)").
- Services follow the project's established pattern (see the section "[Service Layer Conventions (Project Specific)](#service-layer-conventions-project-specific)").
- Litestar guards for authorization.
- **DTOs**: All DTOs (e.g., for login requests, token responses, user creation/update) MUST be `msgspec.Struct` instances, defined in `src/py/app/schemas/`.

## Rules

### User Model (`app.db.models.user.User`)

- User model should include all necessary fields: `email` (unique), `hashed_password`, `is_active`, `is_superuser`, `is_verified`, relationships to roles and teams.
- Follows patterns in the section "[Advanced Alchemy and Litestar Service/Repository/Model Patterns (with msgspec)](#advanced-alchemy-and-litestar-servicerepositorymodel-patterns-with-msgspec)".

### Authentication

- **Password Hashing**: Secure password hashing (e.g., Argon2 via `app.lib.crypt`) MUST be used.
- **Login DTOs**: Login requests (e.g., email/password) MUST use a `msgspec.Struct` (e.g., `LoginRequestStruct`).
- **Token DTOs**: Token responses MUST use a `msgspec.Struct` (e.g., `TokenResponseStruct` containing access token, refresh token, type).
- **JWT Handling**: Proper JWT handling (expiry, secure practices for refresh tokens if used).
- `UserService.authenticate()` method is the pattern for password verification.

### Authorization

- **Guards**: Use Litestar guards for protecting routes based on user roles or specific permissions.
  - Guards should operate on the authenticated `User` model instance.
- **Roles & Permissions**: Define clear roles (e.g., `Admin`, `Editor`, `Viewer`) and associate permissions with them. `User.roles` relationship is key.
- `UserService.is_superuser()` and `UserService.has_role()` are patterns for checking user status/roles.

### User Management Services (`UserService`, `TeamService`)

- **Service Pattern**: Adhere to the project's standard service pattern (inner `Repo`, `SQLAlchemyAsyncRepositoryService` base).
- **User Creation/Update DTOs**: User creation and update operations MUST use `msgspec.Struct` (e.g., `UserCreateStruct`, `UserUpdateStruct`). Services will handle mapping these to the `User` model.
- **Password Update**: Password updates should require current password verification, as seen in `UserService.update_password()`.

### API Endpoints

- Auth endpoints (`/auth/login`, `/auth/register`, `/auth/refresh-token`, etc.) MUST use `msgspec.Structs` for request and response bodies.
- User management endpoints (`/users/...`) MUST use `msgspec.Structs`.

## Exceptions

- Publicly accessible informational endpoints that do not involve user data or actions.
- OAuth flows might involve redirects and specific payload structures dictated by the OAuth provider, but token exchange and internal user representation should align with `msgspec` where possible.

-----

## Data Validation with msgspec.Struct

## Objective

To ensure all incoming and outgoing API data is validated correctly and efficiently using `msgspec.Struct` as the primary mechanism for Data Transfer Objects (DTOs) / Schemas. **It is mandatory to use `msgspec.Struct` instead of Pydantic for core data structures.**

## Context

- **Technology**: `msgspec` for data validation and serialization.
- Litestar has built-in, high-performance support for `msgspec`.
- Schemas (Structs) should be defined in a dedicated module, e.g., `src/py/app/schemas/` or feature-specific schema modules.

## Rules

### Struct Definition

- **Use `msgspec.Struct`**: Define clear `msgspec.Struct` types for all API request and response bodies.
  - ✅

      ```python
      import msgspec
      from uuid import UUID
      from datetime import datetime

      class UserBase(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
          email: str
          name: str | None = None

      class UserCreate(UserBase):
          password: str

      class UserUpdate(msgspec.Struct, gc=False, array_like=True, omit_defaults=True):
          email: str | None = None
          name: str | None = None
          password: str | None = None # Example, might be handled differently
          is_active: bool | None = None

      class UserRead(UserBase):
          id: UUID
          is_active: bool
          created_at: datetime
          updated_at: datetime
      ```

- **Field Types**: Use standard Python types and `msgspec` specific types where appropriate. `msgspec` handles many common types efficiently.
- **Constraints**: `msgspec` supports constraints (e.g., `min_len`, `max_len`, `pattern` for strings; `ge`, `le` for numbers) directly in field definitions or via `Meta`.
  - ✅ `email: str = msgspec.field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")` (or use a library for email validation if complex rules are needed)
- **Optional Fields & Defaults**: Use `| None = None` for optional fields with no default, or provide a default value. `omit_defaults=True` in `Struct` options is useful for PATCH-like operations.
- **Read-Only/Write-Only Fields**: Manage these by defining separate structs for Read, Create, and Update operations.
- **Struct Options**: Utilize `msgspec.Struct` options like `gc=False` (disables cyclic GC tracking for performance if struct is simple), `array_like=True` (for tuple-like representations, can be faster), `omit_defaults=True` (omits fields with default values during encoding if they match the default).

### Usage in Litestar

- **Automatic Validation & Serialization**: Litestar automatically validates incoming request data against `msgspec.Struct` type hints in route handlers and serializes return values of `msgspec.Struct` type.
  - ✅

      ```python
      from litestar import post, get
      from uuid import UUID
      from app.schemas import UserCreate, UserRead # Your msgspec structs
      from app.services import UserService # Your service

      @post("/users")
      async def create_user(data: UserCreate, user_service: UserService) -> UserRead:
          # 'data' is automatically validated instance of UserCreate
          new_user = await user_service.create_user(data)
          return UserRead(id=new_user.id, email=new_user.email, ...) # Map model to UserRead struct

      @get("/users/{user_id:uuid}")
      async def get_user(user_id: UUID, user_service: UserService) -> UserRead:
          user = await user_service.get_user(user_id)
          return UserRead(id=user.id, email=user.email, ...) # Map model to UserRead struct
      ```

- **Generic Structs**: `msgspec` supports generic structs, which can be useful for common response patterns (e.g., paginated responses).

### Naming Conventions

- Suffix struct names with `Read`, `Create`, `Update`, `Payload`, etc., to clearly indicate their purpose (e.g., `UserCreate`, `ItemRead`). Avoid generic `DTO` or `Schema` if a more specific suffix is clearer.

### Conversion Between Models and Structs

- **Service Layer Responsibility**: The service layer is often responsible for converting between SQLAlchemy models and `msgspec.Struct` instances.
  - For creation/update: `Service` receives a `Struct` from the controller, potentially converts/maps its fields to a model instance or a dictionary for the repository.
  - For reads: `Service` gets a model instance from the repository and converts it to a `Struct` before returning to the controller.
  - ✅

      ```python
      # Example in a service method
      # async def get_user(...) -> UserRead:
      #     db_user = await self.repository.get_one(id=user_id)
      #     return UserRead(id=db_user.id, email=db_user.email, ...)
      ```

- **Helper Functions**: Consider helper functions or methods for complex mappings between models and structs if direct instantiation becomes verbose.

## Exceptions

- Simple query parameters might use basic type hints directly in Litestar handler signatures if a full `msgspec.Struct` is overkill.
- Internal data structures not exposed via API might use other types (e.g., `dataclasses`) if `msgspec` features aren't needed, but for API boundaries, `msgspec` is mandatory.

-----

## ShadCN/UI Component Conventions

## Objective

To ensure consistent, accessible, and maintainable UI components by leveraging ShadCN/UI's methodology, promoting code reusability and adherence to project design standards. This project uses **ShadCN/UI** with **Tailwind CSS v4** and **React/TypeScript**.

## Context

- **Technologies**: ShadCN/UI, Tailwind CSS v4, React, TypeScript, Radix UI (underlying primitive library for many ShadCN components).
- **Project Files**: `src/js/components/ui/` (where ShadCN components are added via CLI), `src/js/lib/utils.ts` (for `cn` utility), `components.json` (ShadCN config).
- **Key Concepts**: Composable components, copy-paste integration (components live in your codebase), CLI for adding components, theming via CSS variables, accessibility focus.

## Rules

### Component Integration & Management

- **CLI Usage**: Use the ShadCN/UI CLI (`npx shadcn-ui@latest add <component_name>`) to add new components to the project.
  - ✅ `npx shadcn-ui@latest add button card dialog`
  - ❌ Manually copying component code from the ShadCN/UI website unless for specific, documented reasons (e.g., for components not yet in the CLI or for applying manual patches).
- **File Structure**: Keep ShadCN/UI components within the `src/js/components/ui/` directory as per standard convention.
- **Component Ownership**: Remember that ShadCN/UI components are copied into your codebase. You own them and are expected to customize them as needed.
- **Updating Components**: To update components to a newer version from ShadCN/UI, use the CLI with the `--overwrite` flag. Always review the diff carefully before committing changes.
  - ✅ `npx shadcn-ui@latest add button --overwrite` (then `git diff` and review)

### Styling and Theming

- **Tailwind CSS v4**: ShadCN/UI components are styled using Tailwind CSS. All styling customizations should primarily be done via Tailwind utility classes within the component files or by modifying the component's internal Tailwind classes.
  - See the section "[Tailwind CSS v4 Conventions](#tailwind-css-v4-conventions)" for Tailwind guidelines.
- **CSS Variables for Theming**: Utilize CSS variables for theming, as is standard with ShadCN/UI and Tailwind CSS v4. Define these in your global CSS file (e.g., `src/js/src/globals.css`).
  - `components.json` (`rsc` flag, `tailwind.configPath`, `tailwind.css`, `tailwind.baseColor`, `tailwind.cssVariables`) and `tailwind.config.js` should be configured to use these CSS variables (often HSL values).
  - ✅ Ensure `tailwind.config.js` correctly maps theme colors to these CSS variables (e.g., `primary: 'hsl(var(--primary))'`).
- **`cn` Utility**: Use the `cn` utility function (typically found in `src/js/lib/utils.ts`) for conditionally applying Tailwind classes and merging `className` props.
  - ✅ `className={cn("font-bold", isActive && "bg-primary", props.className)}`
- **Avoid Global CSS Overrides**: Do not write global CSS that directly targets ShadCN component base classes in a way that could lead to specificity wars or unexpected side effects. Prefer direct component modification or Tailwind utility application.

### Component Usage & Composition

- **Composition**: Leverage the composable nature of ShadCN/UI components. Build complex UI elements by combining simpler ShadCN components.
  - ✅ Example: Using `<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardContent>`, `<CardFooter>` together.
- **Props for Customization**: When using ShadCN components, utilize their defined props for behavior and appearance modifications before directly editing the component's source code for one-off changes. If a prop is missing for a desired common customization, consider modifying the base component in `src/js/components/ui/` to accept it.
- **Accessibility (A11y)**: ShadCN/UI components are built with accessibility in mind (often using Radix UI primitives). Preserve and enhance these accessibility features.
  - Ensure appropriate ARIA attributes are used if components are heavily customized or composed.
  - Ensure all interactive elements have proper focus states and are keyboard navigable.
  - Test with screen readers periodically.

### Creating New Custom UI Components (Alongside ShadCN)

- **Follow ShadCN Philosophy**: When creating new custom components (not available in ShadCN/UI but needed for the project):
  - Style with Tailwind CSS utility classes.
  - Aim for composability and reusability.
  - Prioritize accessibility from the start (consider using Radix UI primitives if appropriate for headless logic).
  - Place them in a relevant directory, e.g., `src/js/components/custom/` or alongside feature-specific components.
  - Use the `cn` utility for class name construction.

## Exceptions

- If a very specific, non-reusable visual tweak is needed for a ShadCN component in a single instance, direct modification of its utility classes at the point of use is acceptable. However, if this pattern repeats, consider creating a new variant within the component file itself or a new composed component.

-----

## Tailwind CSS v4 Conventions

## Objective

To ensure consistent, maintainable, and efficient use of Tailwind CSS v4, leveraging its utility-first approach and new v4 features for styling the frontend application. This project uses **Tailwind CSS v4**.

## Context

- **Technologies**: Tailwind CSS v4, PostCSS, Vite.
- **Frontend Stack**: Likely React with TypeScript (given ShadCN usage), but adaptable.
- **Project Files**: `src/js/tailwind.config.js` (or `.ts`), `src/js/postcss.config.js`, `src/js/src/globals.css` (or equivalent), frontend component files (e.g., `.tsx`).
- **Key Concepts**: Utility-first, responsive design, dark mode, custom themes via CSS variables, JIT compilation (inherent in v4).

## Rules

### Configuration (`tailwind.config.js` or `tailwind.config.ts`)

- **Theme Customization**: Define project-specific design tokens (colors, spacing, typography, etc.) within the `theme.extend` object. Prefer using CSS variables for dynamic values.
  - ✅

      ```javascript
      // tailwind.config.js (example for v4, syntax might slightly evolve)
      /** @type {import('tailwindcss').Config} */
      module.exports = {
        content: ['./src/js/**/*.{html,js,jsx,ts,tsx,vue,svelte}'],
        theme: {
          extend: {
            colors: {
              primary: 'hsl(var(--primary))',
              secondary: 'hsl(var(--secondary))',
              // ... other colors based on CSS variables
            },
            // ... other extensions for spacing, typography etc.
          },
        },
        plugins: [
            require('@tailwindcss/typography'),
            require('@tailwindcss/forms'),
            // Potentially other plugins like animate, aspect-ratio etc.
        ],
      };
      ```

- **CSS Variables**: Heavily leverage Tailwind CSS v4's improved support for CSS variables for theming. Define base HSL variables in your global CSS (`src/js/src/globals.css`) and reference them in `tailwind.config.js`.
  - ✅ In `globals.css`:

      ```css
      @layer base {
        :root {
          --background: 0 0% 100%; /* Light mode background */
          --foreground: 224 71.4% 4.1%;
          --primary: 220.9 39.3% 11%;
          /* ... other variables ... */
        }
        .dark {
          --background: 224 71.4% 4.1%; /* Dark mode background */
          --foreground: 210 20% 98%;
          --primary: 210 20% 98%;
          /* ... other variables ... */
        }
      }
      ```

- **Content Path**: Ensure the `content` array in `tailwind.config.js` correctly and comprehensively lists all files that will contain Tailwind CSS classes to ensure proper style generation.

### Utility Usage

- **Utility-First**: Embrace the utility-first approach. Apply styles directly in HTML/JSX/Vue/Svelte templates using Tailwind classes.
  - ✅ `<div class="flex items-center justify-between p-4 bg-background text-foreground rounded-lg">...</div>`
  - ❌ Writing extensive custom CSS classes for simple layout or styling that can be achieved with existing utilities.
- **Readability**: For complex components with many utilities, consider:
  - Grouping related utilities logically.
  - Breaking the component into smaller, more focused sub-components.
  - Using a tool/plugin for sorting Tailwind classes if desired (e.g., Prettier plugin).
- **Responsive Prefixes**: Use responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`, `2xl:`) to apply styles at different breakpoints.
  - ✅ `<div class="text-sm md:text-base lg:text-lg">...</div>`
- **State Prefixes**: Use state prefixes (`hover:`, `focus:`, `active:`, `disabled:`, `dark:`, `group-hover:`, `peer-focus:`) for interactive and theme-based styling.
  - ✅ `<button class="bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-2">...</button>`
- **Dark Mode**: Implement dark mode using the `dark:` variant, configured in `tailwind.config.js` (usually `darkMode: 'class'`). Apply the `.dark` class to a parent element (e.g., `<html>` or `<body>`).

### Component Styling

- **ShadCN/UI Integration**: For projects using ShadCN/UI, styling is primarily managed by customizing the ShadCN components, which themselves use Tailwind. See the section "[ShadCN/UI Component Conventions](#shadcnui-component-conventions)".
- **Abstracting Repetitive Utilities**: For highly reusable UI patterns not covered by ShadCN/UI, create dedicated components (e.g., React/Vue/Svelte components) that encapsulate these utilities.
- **Limit `@apply`**: Avoid using `@apply` to create custom CSS classes from Tailwind utilities. Tailwind CSS v4 encourages direct utility application or component-based abstraction.
  - ⚠️ `@apply` should be used very sparingly, if at all. It can lead to CSS bloat and negate some benefits of the utility-first approach if overused.

### Performance

- **JIT Engine**: Tailwind CSS v4 uses a highly optimized Just-In-Time (JIT) engine by default, generating only the CSS that is actually used in your project.
- **Minimize Custom CSS**: Rely on Tailwind utilities as much as possible to keep custom CSS to a minimum. This ensures better maintainability and leverages Tailwind's optimizations.

## Exceptions

- Email templates might require inline styles or different CSS approaches due to email client limitations.
- Interfacing with third-party libraries that have their own extensive styling systems might require some custom CSS or adaptation layers.

-----

## TypeScript Style and Conventions

## Objective

To ensure consistent, type-safe, and maintainable TypeScript code.

## Context

- TypeScript used for frontend development (React/ShadCN/Vite).
- Configuration in `src/js/tsconfig.json`.
- Linting via Biome (from `biome.json`).

## Rules

### Typing

- Strive for strong typing. Avoid `any` where possible. Use `unknown` for safer alternatives to `any`.
- Use specific types (interfaces, type aliases) for objects, props, and state.

### Style

- Follow Biome formatter and linter rules.
- Use `PascalCase` for types, interfaces, and enums.
- Use `camelCase` for functions and variables.

### Modules

- Use ES Modules (`import`/`export`).

## Exceptions

- Interfacing with JavaScript libraries that lack types might require some `any` or type assertions.

-----

## Vite Configuration Conventions

## Objective

To maintain an optimal and understandable Vite configuration for the frontend build process.

## Context

- Vite is used for frontend development and bundling.
- Configuration in `src/js/vite.config.ts`.

## Rules

### Plugins

- Clearly list and configure Vite plugins (e.g., React plugin, other necessary build tools).

### Paths and Aliases

- Define path aliases in `resolve.alias` for cleaner imports (e.g., `@/*` for `src/js/src/*`).

### Build Options

- Configure build options (`build.outDir`, `build.sourcemap`, etc.) appropriately for development and production.

### Server Options

- Configure development server options (`server.port`, `server.proxy`) as needed.

## Exceptions

- Environment-specific overrides if managed carefully.

-----

## Performance Guidelines

## Objective

To ensure the application is performant, providing a good user experience and efficient resource utilization.

## Context

- Async Python backend (Litestar, SQLAlchemy), JavaScript/TypeScript frontend (React/Vite).

## Rules

### Backend Performance

- **Database Queries**: Optimize SQLAlchemy queries. Use `selectinload` or `joinedload` for eager loading of related data to avoid N+1 problems. Index frequently queried columns.
- **Async Operations**: Properly use `async/await` for all I/O-bound operations.
- **Caching**: Implement caching strategies (e.g., Litestar stores, Redis) for frequently accessed, expensive-to-compute data.
- **Task Queues**: Offload long-running or resource-intensive tasks to background workers (SAQ).

### Frontend Performance

- **Bundle Size**: Keep JavaScript bundle sizes small (Vite helps with tree-shaking and code splitting).
- **Code Splitting**: Use dynamic imports (`React.lazy`) for route-based or component-based code splitting.
- **Memoization**: Use `React.memo`, `useMemo`, `useCallback` to prevent unnecessary re-renders of components.
- **Efficient Rendering**: Avoid large list rendering issues (use virtualization if needed).
- **Image Optimization**: Optimize images (compression, appropriate formats, lazy loading).

### General

- **Profiling**: Use profiling tools (e.g., `cProfile` for Python, browser dev tools for frontend) to identify bottlenecks.

## Exceptions

- Premature optimization should be avoided; focus on clear bottlenecks identified through profiling.

-----

## Security Best Practices

## Objective

To ensure the application is developed with security in mind, protecting against common vulnerabilities.

## Context

- Web application with Python backend (Litestar) and JavaScript/TypeScript frontend.
- Data storage via SQLAlchemy, user authentication, external API integrations.
- **Data Validation**: `msgspec.Struct` is used for all API input validation (see the section "[Data Validation with msgspec.Struct](#data-validation-with-msgspecstruct)").

## Rules

### Input Validation

- Validate all incoming data (API requests, user inputs) using `msgspec.Struct` on the backend and appropriate form validation on the frontend.
- Sanitize outputs to prevent XSS (though modern frontend frameworks often handle this by default, e.g., React).

### Authentication & Authorization

- Implement strong password policies, secure session/token management (JWT).
- Enforce proper authorization using guards (backend) and conditional UI rendering (frontend).
- See also: the section "[Authentication, Authorization, and User Management (with msgspec)](#authentication-authorization-and-user-management-with-msgspec)"

### Dependency Management

- Regularly update dependencies to patch known vulnerabilities (`uv lock --upgrade`, `npm upgrade`).
- Use tools to scan for vulnerable dependencies (e.g., `pip-audit`, `npm audit`, GitHub Dependabot).

### Data Handling

- Protect sensitive data (encryption at rest/transit where appropriate for PII, financial data, etc.).
- Avoid logging sensitive information unless absolutely necessary and properly secured/masked.

### API Security

- Use HTTPS for all communication.
- Implement rate limiting and protection against common API attacks (e.g., via API gateway or middleware in Litestar).
- Ensure proper CORS configuration.

### Docker & Deployment

- Use minimal base images for Docker.
- Do not hardcode secrets in Dockerfiles or source code; use environment variables or dedicated secret management tools.
- Scan Docker images for vulnerabilities.

### Secure Headers

- Implement security-related HTTP headers (e.g., `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`).

## Exceptions

- Local development environments might have relaxed security for ease of debugging (e.g., more permissive CORS, simpler HTTPS setup), but production configurations must be strict.

-----

## Static Analysis Tooling

## Objective

To maintain high code quality and catch errors early by adhering to configurations of static analysis tools.

## Context

- Python: Ruff (linting, formatting, import sorting), MyPy & Pyright (type checking), Slotscheck.
- Frontend: Biome (linting, formatting for JS/TS).
- Tools configured in `pyproject.toml` and `biome.json`.
- Enforced via pre-commit hooks.

## Rules

### Adherence

- Code MUST pass all configured static analysis checks.
- Resolve or appropriately ignore (with justification) reported errors/warnings.

### Configuration

- Tool configurations (`pyproject.toml`, `biome.json`) should be version-controlled and consistently applied.
- Regularly review and update tool configurations and versions.

### Pre-commit Hooks

- Ensure pre-commit hooks for these tools are active and maintained.

## Exceptions

- Specific lines may be ignored with `# type: ignore`, `eslint-disable-next-line`, etc., but must include a comment explaining why.

-----

## Testing with Pytest

## Objective

To ensure comprehensive test coverage, maintainable test suites, and effective use of Pytest features for both unit and integration testing.

## Context

- **Technologies**: Pytest, Python 3.13+, `msgspec` (for API DTOs).
- **Tools**: `pytest-asyncio` (for async tests), `pytest-mock` (for mocking), `pytest-cov` (for coverage), `pytest-xdist` (for parallel execution), `pytest-databases`.
- **Project Files**: `src/py/tests/`, `tests/`. `pyproject.toml` contains Pytest configuration (`tool.pytest.ini_options`).

## Rules

### Test Structure and Naming

- **File Naming**: Test files should be named `test_*.py` or `*_test.py` (prefer `test_*.py`).
- **Function Naming**: Test functions should be named `test_*` and clearly describe the scenario and expected outcome.
  - ✅ `def test_create_user_with_valid_data_returns_201_and_user_struct():`
  - ❌ `def test_user():`
- **Class Naming**: Test classes (if used for grouping related tests) should be named `Test*`.
  - ✅ `class TestUserService:`
- **Organization**:
  - `src/py/tests/unit/`: For unit tests, testing individual modules/functions/classes in isolation. Mocks are heavily used here.
  - `src/py/tests/integration/`: For integration tests, testing interactions between components (e.g., API endpoints with database and services).
- **Markers**: Use Pytest markers (`@pytest.mark.<marker_name>`) to categorize tests (e.g., `unit`, `integration`, `slow`). Markers are defined in `pyproject.toml`.
  - ✅ `@pytest.mark.integration`

### Test Content

- **AAA Pattern (Arrange, Act, Assert)**: Structure tests clearly using the Arrange, Act, Assert pattern.
  - ✅

      ```python
      # Assuming ItemRead is a msgspec.Struct
      async def test_get_item_success(item_id: UUID, client: AsyncTestClient, item_in_db: Item, item_read_struct: ItemRead):
          # Arrange (often handled by fixtures)
          # item_id, item_in_db, item_read_struct (expected output) are provided by fixtures.
          # client is the AsyncTestClient for making requests.

          # Act
          response = await client.get(f"/items/{item_id}")

          # Assert
          assert response.status_code == 200
          # Assuming response.json() can be decoded into the msgspec.Struct or a dict matching it
          response_data = msgspec.json.decode(response.content, type=ItemRead)
          assert response_data.id == item_id
          assert response_data.name == item_in_db.name # Or item_read_struct.name
      ```

- **Single Responsibility**: Each test should ideally verify one specific behavior or outcome.
- **Independence**: Tests must be independent and not rely on the state or outcome of other tests. Use fixtures for setup and teardown.
- **Mocking (`pytest-mock`)**: Use the `mocker` fixture from `pytest-mock` for mocking external dependencies or specific internal calls in unit tests. Avoid over-mocking.
  - ✅ `mocker.patch('app.services.some_service.some_object.external_call', return_value=...)`
- **Fixtures**: Utilize Pytest fixtures (`@pytest.fixture`) for setting up preconditions (e.g., test data, client instances, database sessions, `msgspec.Struct` instances for request/response data).
  - Define reusable fixtures in `conftest.py` files at appropriate directory levels.
  - Scope fixtures correctly (`function`, `class`, `module`, `session`).

### Assertions

- **Specific Assertions**: Use specific assertion functions.
- **`msgspec.Struct` Assertions**: When asserting API responses, decode the response into the expected `msgspec.Struct` and assert field values.
  - ✅ `actual_struct = msgspec.json.decode(response.content, type=ExpectedStruct)`
  - ✅ `assert actual_struct == expected_struct_fixture` (if structs support equality comparison and order is deterministic or using `msgspec.match_type`).

### Asynchronous Tests (`pytest-asyncio`)

- **`async def`**: Mark async test functions with `async def`.
- **Async Fixtures**: Use `@pytest_asyncio.fixture` for fixtures that need to perform async operations.

### Integration Tests

- **`AsyncTestClient`**: Use Litestar's `AsyncTestClient` for testing HTTP endpoints.
- **Database State**: Manage database state carefully. `pytest-databases` plugin helps.
- **Real Dependencies**: Integration tests should use real database connections and other in-process services where feasible. Mock external third-party services.
- **Request Data**: When sending data to endpoints (POST, PUT, PATCH), construct instances of the relevant `msgspec.Struct` and pass them to the client's `json=` parameter (httpx client will serialize it).

### Coverage (`pytest-cov`)

- **Aim for High Coverage**: Strive for high test coverage.
- **Meaningful Tests**: Focus on meaningful tests.

## Exceptions

- E2E tests might have different structures.
- Performance-specific tests have different patterns.

-----

## Makefile Style and Always-On Rules

To establish clear, consistent, and maintainable conventions for `Makefile`s within the project, ensuring they are easy to understand, use, and extend.

### General Setup

- The Makefile SHOULD start by specifying the shell:

  ```makefile
  SHELL := /bin/bash
  ```

- A default goal, typically `help`, SHOULD be defined:

  ```makefile
  .DEFAULT_GOAL:=help
  ```

- `.ONESHELL:` SHOULD be used to ensure all lines in a recipe are passed to a single invocation of the shell.
- `.EXPORT_ALL_VARIABLES:` MAY be used if global variable export is desired for sub-makes or shell commands.
- `MAKEFLAGS += --no-print-directory` SHOULD be used to prevent `make` from printing directory enter/leave messages.
- Individual commands within recipes SHOULD be prefixed with `@` to suppress echoing of the command itself, unless the command's output is the primary purpose.

### Variable Definitions

- Variables SHOULD be grouped logically (e.g., color definitions, paths, tool commands).
- Use `:=` for immediate evaluation of simple variable assignments.
- Variables SHOULD be named using `UPPER_CASE_WITH_UNDERSCORES`.
- Predefined variables for console output colors and symbols (e.g., `BLUE`, `GREEN`, `INFO`, `OK`) SHOULD be used for consistent messaging.

### Targets

- All targets that do not represent actual files MUST be declared using `.PHONY`.
- A `help` target MUST be present and SHOULD use a script (e.g., `awk`) to parse specially formatted comments from the Makefile to generate a dynamic help message.
- Comments for help text MUST follow the format: `target_name:.*## Help message for the target`.
- Section headers in the help output SHOULD be generated from comments formatted as: `##@ Section Title`.
- Target names SHOULD be `lower-case-with-hyphens` or `lower_case_with_underscores`. Consistency is key.
- Commands SHOULD be prefixed with `@` to suppress default echoing.
- User feedback SHOULD be provided using `echo` with the predefined color/formatting variables.
- Output from non-critical or verbose commands SHOULD be suppressed using `>/dev/null 2>&1` if it's not useful to the user.

### Makefile Organization

- The Makefile SHOULD be organized into logical sections using commented headers for better readability.
- Typical sections include: Variable definitions, Default/Help targets, Installation/Setup targets, Cleaning targets, Linting and Formatting, Testing and Coverage, Documentation, Build/Release, Local Infrastructure.

### Comments

- Standard `#` character SHOULD be used for comments that are not part of the help system.

### Readability

- Maintain consistent indentation (tabs are standard in Makefiles).
- Group related commands and targets.
- Use blank lines to separate logical blocks within a recipe or between targets.

### Exceptions

- Complex conditional logic or advanced Makefile features might require deviations but should be well-commented.

### Always-On Rules

- **Always run `make lint` after code changes**: After making any code changes, always execute `make lint` from the project root. This will run ruff, mypy, pyright, and pre-commit checks to ensure code quality and consistency.

- **Always update TypeScript types and client on OpenAPI schema changes**: Whenever the OpenAPI schema changes, you must:
  1. Export the updated OpenAPI schema.
  2. Generate the new TypeScript types and client.
  3. Use the `make types` target to automate this process.
  4. **Triggers for this process include:**
     - Any change to files in `src/py/app/schemas/` (schemas)
     - Any change to files in `src/py/app/server/routes/` (routes/controllers)
     - Any change to OpenAPI-related configuration or plugins (e.g., `OpenAPIConfig`, plugin registration)
     - Any other change that could affect the OpenAPI schema

---

## Authentication and Authorization Flow

### Objective

To define and standardize the project's authentication (AuthN) and authorization (AuthZ) flow. This document details the interaction between User models, services, Data Transfer Objects (DTOs), Litestar's security mechanisms (JWT), and password management. This pattern is the de-facto standard for authentication using Litestar with SQLAlchemy and Advanced Alchemy in this project.

### Context

- **Primary Technologies**: Litestar, Advanced Alchemy, SQLAlchemy.
- **Authentication Mechanism**: JSON Web Tokens (JWT) via Litestar's `OAuth2PasswordBearerAuth`.
- **Password Hashing**: `pwdlib` (specifically Argon2) managed through `app.lib.crypt`.
- **Data Transfer Objects (DTOs)**: `msgspec.Struct` for all API request/response bodies related to authentication.

### Key Files & Components

- **User Model**: `src/py/app/db/models/user.py` (Defines the `User` database schema).
- **OAuth Account Model**: `src/py/app/db/models/oauth_account.py` (For third-party OAuth integrations, linked to `User`).
- **Account Schemas**: `src/py/app/schemas/accounts.py` (Contains `msgspec.Struct` definitions like `AccountLogin`, `UserCreate`, `UserRead`).
- **User Service**: `src/py/app/services/_users.py` (Contains `UserService` with core logic like `authenticate`, password hashing hooks).
- **Cryptography Library**: `src/py/app/lib/crypt.py` (Handles password hashing and verification using `pwdlib`).
- **Security Configuration**: `src/py/app/server/security.py` (Defines the `OAuth2PasswordBearerAuth` instance (`auth`), the `current_user_from_token` handler, and various security guards like `requires_active_user`).
- **Access Routes**: `src/py/app/server/routes/access.py` (Contains `AccessController` for `/api/access/login` and `/api/access/signup`).
- **Profile Routes**: `src/py/app/server/routes/profile.py` (Contains `ProfileController` for user profile management like `/api/me`).
- **Dependency Providers**: `src/py/app/server/deps.py` (e.g., `provide_users_service`), `app.server.security.provide_user`.

### Rules and Detailed Flow

#### 1. User Model (`app.db.models.user.User`)

- The `User` model is central to authentication. Critical fields include:
  - `email`: Unique identifier used as the username.
  - `hashed_password`: Stores the securely hashed password.
  - `is_active`: Boolean indicating if the user account can log in.
  - `is_verified`: Boolean for email verification status (if applicable).
  - `is_superuser`: Boolean for superuser privileges.
  - Relationships like `roles` and `teams` are used for authorization.
- It inherits from Advanced Alchemy's `UUIDAuditBase`.

#### 2. Password Management (`app.lib.crypt` & `UserService`)

- **Hashing**: When a user signs up or updates their password, `UserService` (e.g., in `_populate_with_hashed_password` hook or `update_password` method) calls `app.lib.crypt.get_password_hash()` to hash the plain-text password using Argon2.
- **Verification**: During login, `UserService.authenticate()` calls `app.lib.crypt.verify_password()` to compare the provided password against the stored hash.

#### 3. Login Flow (`POST /api/access/login`)

- **Controller**: `AccessController.login` handles the request.
- **Request DTO**: Expects `app.schemas.accounts.AccountLogin` (`msgspec.Struct`) containing `username` (email) and `password`.
- **Authentication Logic**: Calls `UserService.authenticate(username, password)`.
  - This service method retrieves the user by email.
  - Verifies the password using `crypt.verify_password()`.
  - Checks if the user is active.
  - Raises `PermissionDeniedException` if authentication fails (user not found, password mismatch, inactive account).
- **JWT Generation**: If authentication is successful, `security.auth.login(user.email)` is called. `security.auth` is the `OAuth2PasswordBearerAuth` instance.
  - This generates a JWT. The `user.email` is used as the token's subject (`sub`).
- **Response**: The endpoint returns an `OAuth2Login` response (a Litestar type often aliased or used directly), which includes the `access_token` (the JWT) and `token_type` (typically "Bearer").

#### 4. User Registration Flow (`POST /api/access/signup`)

- **Controller**: `AccessController.signup` handles the request.
- **Request DTO**: Expects `app.schemas.accounts.AccountRegister` (`msgspec.Struct`).
- **User Creation**: Calls `UserService.create(data)`, where `data` includes email, password, etc.
  - `UserService` internally hashes the password via its `to_model_on_create` hook (calling `_populate_with_hashed_password`).
  - A default role (e.g., `constants.DEFAULT_ACCESS_ROLE`) is typically assigned.
- **Event Emission**: `request.app.emit("user_created", user_id=user.id)` is called to signal user creation for potential post-registration tasks.
- **Response**: Returns the created user's details, typically mapped to `s.User` schema.

#### 5. JWT Configuration (`security.auth` in `app.server.security.py`)

- An instance of `OAuth2PasswordBearerAuth[m.User]` is created and named `auth`.
- **`retrieve_user_handler`**: Set to `current_user_from_token`. This function is responsible for fetching the `User` model from the database based on the validated token.
- **`token_secret`**: Loaded from `settings.app.SECRET_KEY`. This key is crucial for signing and verifying JWTs.
- **`token_url`**: Set to `/api/access/login`, informing clients where to obtain a token.
- **`exclude`**: A list of paths (e.g., `/api/health`, `/api/access/login`, `/api/access/signup`, schema docs) that do not require authentication.

#### 6. Authenticated Requests & Token Validation

- The client sends the JWT in the `Authorization` header for protected routes: `Authorization: Bearer <your_jwt_token>`.
- The `OAuth2PasswordBearerAuth` middleware, configured on the Litestar application, automatically intercepts requests to protected routes.
- It validates the token's signature, expiry, and other claims.
- If the token is valid, it calls the `retrieve_user_handler` (`current_user_from_token`).

#### 7. User Retrieval from Token (`current_user_from_token`)

- This function receives the validated `Token` object (from Litestar).
- It extracts the subject (`token.sub`), which is the user's email.
- It uses `UserService` (obtained via `deps.provide_users_service` and a database session) to fetch the `m.User` from the database using the email.
- Returns the `m.User` instance if found and active, otherwise returns `None` (which Litestar handles as an authentication failure).

#### 8. Accessing the Current User in Route Handlers

- Once `current_user_from_token` successfully returns a user, Litestar attaches this `m.User` object to the request scope, typically accessible as `request.user` or `connection.user`.
- The `provide_user` dependency (defined in `app.server.security.py`) can be used for type-safe injection of the current `m.User` into route handler parameters.

#### 9. Authorization and Guards

- Security guards, defined in `app.server.security.py` (e.g., `requires_active_user`, `requires_superuser`, `requires_team_membership`, `requires_team_admin`), are applied to controllers or specific routes.
- These guards operate on the `connection.user` object (the authenticated `m.User` instance).
- They check user properties (e.g., `is_active`, `is_superuser`, roles, team memberships) to determine if the user has the necessary permissions for the requested resource or action.
- If a guard check fails, it raises a `PermissionDeniedException`.

#### 10. Data Transfer Objects (DTOs)

- All request and response bodies related to authentication and user management (e.g., login credentials, user registration data, user profile information) MUST be defined as `msgspec.Struct` instances in `app.schemas.accounts` or other relevant schema modules.
- Litestar handles automatic validation of incoming `msgspec.Struct` data and serialization of outgoing `msgspec.Struct` instances.

#### 11. Error Handling

- `litestar.exceptions.PermissionDeniedException` is the standard exception to be raised for authentication failures (e.g., invalid credentials, inactive account) and authorization failures (e.g., insufficient privileges as determined by guards).
- `litestar.exceptions.NotAuthorizedException` might be used if a valid token is simply not present for a protected route.

#### 12. OAuth Accounts (`UserOauthAccount`)

- The `UserOauthAccount` model and its corresponding service (`UserOAuthAccountService`) are designed for linking user accounts to external OAuth providers (e.g., Google, GitHub).
- This flow is complementary to the primary email/password JWT authentication. The specifics of the OAuth dance (redirects, token exchange with providers) are typically handled by a library like `httpx-oauth` and integrated into dedicated OAuth callback routes, eventually linking the external account to an internal `User` record.

### Conceptual Flow Summary

1. **Login**: Client `POST /api/access/login` with credentials -> `AccessController` -> `UserService.authenticate` -> If OK, `security.auth.login` generates JWT -> Client receives JWT.
2. **Authenticated Request**: Client sends request to protected endpoint with `Authorization: Bearer <JWT>` header.
3. **Token Validation**: Litestar's `OAuth2PasswordBearerAuth` middleware validates JWT.
4. **User Retrieval**: `current_user_from_token` is called -> `UserService` fetches user by email from JWT subject.
5. **Guard Execution**: Route-specific guards check `request.user` properties.
6. **Controller Logic**: If all checks pass, the controller handler is executed with `request.user` available.

This comprehensive flow ensures secure and consistent authentication and authorization throughout the application.

-----
